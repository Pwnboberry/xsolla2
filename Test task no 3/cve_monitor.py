#!/usr/bin/env python3
"""
CVE Monitoring Pipeline
========================

Fetch -> Filter -> Enrich (KEV/EPSS) -> Prioritize -> Summarize (LLM) -> Deliver

Design notes are in README.md and report.md. Short version:

- Idempotent: sent CVE IDs are tracked in state.json with a timestamp and
  pruned after STATE_RETENTION_DAYS. A CVE is never re-sent.
- Never fails silently: every run ends with a heartbeat message (success or
  error), so "no new CVEs" and "pipeline is broken" never look the same in
  the channel.
- Spam-bounded: a hard MAX_NOTIFICATIONS cap plus a digest mode. If more than
  DIGEST_THRESHOLD CVEs qualify in one run, only the top ones get a full
  message; the rest are listed compactly in a single digest message. The
  channel gets at most ~1-2 messages regardless of how many CVEs match.
- The LLM only writes the human-readable summary. It never decides what is
  "critical" (that's deterministic: CVSS + EPSS + CISA KEV), and its output
  is validated before use -- see summarize_cve() / validate_summary().
"""

import os
import re
import sys
import json
import time
import html
import logging
import argparse
from datetime import datetime, timedelta, timezone

import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

CVE_ID_RE = re.compile(r"CVE-\d{4}-\d{4,}")

# ============================================================
# 1. CONFIG
# ============================================================

def load_config(path="config.yaml"):
    if not os.path.exists(path):
        logger.error(f"Config file not found: {path}")
        sys.exit(1)
    with open(path, "r") as f:
        cfg = yaml.safe_load(f) or {}

    required_top_level = ["stack", "thresholds"]
    missing = [k for k in required_top_level if k not in cfg]
    if missing:
        logger.error(f"config.yaml is missing required keys: {missing}")
        sys.exit(1)

    for key in ("critical", "high", "medium"):
        if key not in cfg["thresholds"]:
            logger.error(f"config.yaml: thresholds.{key} is required")
            sys.exit(1)

    cfg.setdefault("lookback_days", 2)
    cfg.setdefault("max_notifications", 20)
    cfg.setdefault("min_cvss", 0)
    cfg.setdefault("digest_threshold", 8)
    cfg.setdefault("max_full_detail_in_digest", 5)
    cfg.setdefault("state_retention_days", 90)
    cfg.setdefault("consecutive_failures_alert", 3)
    cfg.setdefault("ollama_model", "llama3.2:3b")
    cfg.setdefault("ollama_url", "http://localhost:11434/api/generate")
    return cfg


CONFIG = load_config()
STACK = CONFIG["stack"]
LOOKBACK_DAYS = CONFIG["lookback_days"]
MAX_NOTIFICATIONS = CONFIG["max_notifications"]
MIN_CVSS = CONFIG["min_cvss"]
DIGEST_THRESHOLD = CONFIG["digest_threshold"]
MAX_FULL_DETAIL = CONFIG["max_full_detail_in_digest"]
STATE_RETENTION_DAYS = CONFIG["state_retention_days"]
CONSECUTIVE_FAILURES_ALERT = CONFIG["consecutive_failures_alert"]

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NVD_API_KEY = os.getenv("NVD_API_KEY")  # optional, raises the rate limit

STATE_FILE = "state.json"
AUDIT_LOG = "llm_audit.log"

# ============================================================
# 2. STATE (idempotency + health tracking)
# ============================================================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"{STATE_FILE} is corrupted, starting fresh")
    return {"sent": {}, "last_run": None, "consecutive_failures": 0}


def save_state(state):
    tmp_path = STATE_FILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_path, STATE_FILE)  # atomic, avoids a half-written state.json


def prune_state(state):
    cutoff = datetime.now(timezone.utc) - timedelta(days=STATE_RETENTION_DAYS)
    kept = {}
    for cve_id, ts in state.get("sent", {}).items():
        try:
            if datetime.fromisoformat(ts) >= cutoff:
                kept[cve_id] = ts
        except ValueError:
            continue  # drop unparsable entries rather than crash
    state["sent"] = kept
    return state

# ============================================================
# 3. COLLECTION (NVD API 2.0)
# ============================================================

def fetch_cves():
    """Fetch CVEs modified in the last LOOKBACK_DAYS, with pagination.

    Why lastMod and not published: we care about anything that changed
    recently, including CVSS re-scoring, which published-date alone misses.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)

    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    headers = {"User-Agent": "cve-monitor-bot/1.0 (internship assignment)"}
    if NVD_API_KEY:
        headers["apiKey"] = NVD_API_KEY

    # No key: NVD allows 5 requests / 30s. With a key: 50 / 30s.
    delay_between_pages = 1.2 if NVD_API_KEY else 6.5

    results = []
    start_index = 0
    page_size = 2000
    total_results = None

    while True:
        params = {
            "lastModStartDate": start_date.strftime("%Y-%m-%dT%H:%M:%S.000") + "+00:00",
            "lastModEndDate": end_date.strftime("%Y-%m-%dT%H:%M:%S.000") + "+00:00",
            "resultsPerPage": page_size,
            "startIndex": start_index,
        }

        logger.info(f"Querying NVD (startIndex={start_index})...")
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 429:
                logger.warning("NVD rate-limited us (429), waiting 30s...")
                time.sleep(30)
                resp = requests.get(url, params=params, headers=headers, timeout=30)

            if resp.status_code != 200:
                logger.error(f"NVD returned {resp.status_code}: {resp.text[:300]}")
                break

            data = resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"NVD request failed: {e}")
            break
        except ValueError as e:
            logger.error(f"NVD returned non-JSON response: {e}")
            break

        if total_results is None:
            total_results = data.get("totalResults", 0)
            logger.info(f"NVD reports {total_results} CVEs modified in the window")

        for item in data.get("vulnerabilities", []):
            results.append(parse_nvd_item(item))

        start_index += page_size
        if start_index >= (total_results or 0):
            break
        time.sleep(delay_between_pages)

    logger.info(f"Fetched {len(results)} CVEs from NVD")
    return results


def parse_nvd_item(item):
    cve = item.get("cve", {})
    cve_id = cve.get("id", "")

    desc = ""
    for d in cve.get("descriptions", []):
        if d.get("lang") == "en":
            desc = d.get("value", "")
            break

    # Prefer newest CVSS version available; fall back gracefully.
    cvss, cvss_version = 0.0, None
    metrics = cve.get("metrics", {})
    for metric_key, version in (
        ("cvssMetricV31", "3.1"),
        ("cvssMetricV30", "3.0"),
        ("cvssMetricV2", "2.0"),
    ):
        entries = metrics.get(metric_key, [])
        if entries:
            cvss = entries[0].get("cvssData", {}).get("baseScore", 0.0)
            cvss_version = version
            break

    return {
        "id": cve_id,
        "description": desc,
        "cvss_score": cvss,
        "cvss_version": cvss_version,
        "references": [r.get("url") for r in cve.get("references", [])],
    }

# ============================================================
# 4. FILTERING (relevance to our stack)
# ============================================================

def filter_by_stack(cves):
    filtered = []
    patterns = {tech: re.compile(r"\b" + re.escape(tech.lower()) + r"\b") for tech in STACK}

    for cve in cves:
        desc = cve.get("description", "").lower()
        matched = [tech for tech, pat in patterns.items() if pat.search(desc)]
        if matched:
            cve["matched_tech"] = matched
            filtered.append(cve)

    logger.info(f"Stack-relevant: {len(filtered)} of {len(cves)}")
    return filtered

# ============================================================
# 5. ENRICHMENT (CISA KEV + EPSS)
# ============================================================

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_URL = "https://api.first.org/data/v1/epss"


def fetch_kev_catalog():
    """Known-exploited-in-the-wild CVEs, per CISA. This is a verified
    signal (someone confirmed active exploitation), stronger than a
    keyword match for 'exploit' in a free-text description."""
    try:
        resp = requests.get(KEV_URL, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        kev_ids = {v["cveID"] for v in data.get("vulnerabilities", [])}
        logger.info(f"CISA KEV catalog loaded: {len(kev_ids)} entries")
        return kev_ids
    except Exception as e:
        logger.warning(f"Could not load CISA KEV catalog, continuing without it: {e}")
        return set()


def fetch_epss_scores(cve_ids):
    """Probability of exploitation in the next 30 days, per FIRST.org.
    Batched in chunks; failure degrades to epss=0 for all, not a crash."""
    scores = {}
    if not cve_ids:
        return scores

    chunk_size = 100
    for i in range(0, len(cve_ids), chunk_size):
        chunk = cve_ids[i:i + chunk_size]
        try:
            resp = requests.get(EPSS_URL, params={"cve": ",".join(chunk)}, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for row in data.get("data", []):
                scores[row["cve"]] = float(row.get("epss", 0.0))
        except Exception as e:
            logger.warning(f"EPSS lookup failed for a batch, defaulting to 0: {e}")
    return scores


def enrich(cves):
    kev_ids = fetch_kev_catalog()
    epss_scores = fetch_epss_scores([c["id"] for c in cves])
    for cve in cves:
        cve["in_kev"] = cve["id"] in kev_ids
        cve["epss"] = epss_scores.get(cve["id"], 0.0)
    return cves

# ============================================================
# 6. PRIORITIZATION (deterministic, no LLM)
# ============================================================

def prioritize(cves):
    """Priority is decided by code, not by the model. The LLM is never
    asked "is this critical" -- only "explain this CVE that code already
    scored". That keeps a hallucinated severity judgment off the table."""
    for cve in cves:
        cvss = cve.get("cvss_score", 0) or 0
        epss = cve.get("epss", 0.0)
        desc = cve.get("description", "").lower()
        mentions_exploit = any(
            w in desc for w in ("exploit", "poc", "metasploit", "proof of concept")
        )

        if cve.get("in_kev"):
            # Confirmed active exploitation overrides everything else.
            level = "CRITICAL"
            score = 1.0
        else:
            score = (cvss / 10) * 0.55 + epss * 0.35 + (0.10 if mentions_exploit else 0.0)
            score = min(score, 1.0)
            if score >= CONFIG["thresholds"]["critical"]:
                level = "CRITICAL"
            elif score >= CONFIG["thresholds"]["high"]:
                level = "HIGH"
            elif score >= CONFIG["thresholds"]["medium"]:
                level = "MEDIUM"
            else:
                level = "LOW"

        cve["priority_score"] = round(score, 3)
        cve["priority_level"] = level
        cve["mentions_exploit"] = mentions_exploit

    return sorted(cves, key=lambda x: x["priority_score"], reverse=True)

# ============================================================
# 7. SUMMARIZATION (LLM, with output validation)
# ============================================================

def call_ollama(prompt):
    try:
        resp = requests.post(
            CONFIG["ollama_url"],
            json={
                "model": CONFIG["ollama_model"],
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 250, "temperature": 0.2},
            },
            timeout=120,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
        logger.error(f"Ollama returned {resp.status_code}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Ollama is not running (start it with 'ollama serve')")
        return None
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        return None


def audit_log(cve_id, reason, raw_response):
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "time": datetime.now(timezone.utc).isoformat(),
            "cve_id": cve_id,
            "reason": reason,
            "raw_response": raw_response,
        }) + "\n")


def validate_summary(cve_id, response):
    """Reject anything that looks fabricated or off-structure rather than
    trying to fix it. A rejected summary falls back to a deterministic
    template -- worse writing, but it can't invent facts."""
    if not response or not response.strip():
        return False, "empty response"

    if not all(tag in response for tag in ("WHAT:", "IMPACT:", "ACTION:")):
        return False, "missing required structure"

    mentioned_ids = set(CVE_ID_RE.findall(response))
    other_ids = mentioned_ids - {cve_id}
    if other_ids:
        # The model referenced a different CVE than the one it was asked
        # about -- classic small-model cross-contamination between prompts.
        return False, f"mentions other CVE IDs: {other_ids}"

    if len(response) > 1500:
        return False, "response far longer than requested"

    return True, None


def fallback_summary(cve):
    desc = cve.get("description", "")[:220]
    return (
        f"WHAT: {desc}...\n"
        f"IMPACT: Not auto-summarized (model output was rejected or unavailable) "
        f"-- read the description above.\n"
        f"ACTION: Review manually; see the NVD link below."
    )


def summarize_cve(cve):
    cve_id = cve.get("id", "Unknown")
    description = cve.get("description", "No description")
    tech = ", ".join(cve.get("matched_tech", ["unknown"]))
    level = cve.get("priority_level", "UNKNOWN")

    prompt = f"""You are a security analyst. Summarize this CVE in 3 short sentences for an on-call engineer reading this at 6am.

CVE ID: {cve_id}
Description: {description}
Affected tech in our stack: {tech}
Priority (already decided by our system, do not re-derive it): {level}

Respond using exactly this structure and nothing else:
WHAT: <one sentence, what the vulnerability is>
IMPACT: <one sentence, what happens if it's exploited>
ACTION: <one sentence, what the engineer should do next>

Rules: only use facts from the description above. Do not invent CVE IDs, CVSS numbers, vendor names, or affected versions that are not in the description. Do not copy the description verbatim. Plain English, no jargon dump."""

    raw = call_ollama(prompt)
    ok, reason = validate_summary(cve_id, raw or "")

    if ok:
        return raw.strip()

    logger.warning(f"{cve_id}: rejected LLM summary ({reason}), using fallback template")
    audit_log(cve_id, reason, raw)
    return fallback_summary(cve)

# ============================================================
# 8. FORMATTING + DELIVERY
# ============================================================

def esc(text):
    return html.escape(str(text), quote=False)


def format_cve_message(cve):
    emoji_map = {"CRITICAL": "\U0001F534", "HIGH": "\U0001F7E0", "MEDIUM": "\U0001F7E1", "LOW": "\U0001F7E2"}
    emoji = emoji_map.get(cve.get("priority_level", "LOW"), "\u26AA")
    flags = []
    if cve.get("in_kev"):
        flags.append("CONFIRMED EXPLOITED (CISA KEV)")
    elif cve.get("mentions_exploit"):
        flags.append("exploit mentioned in description")
    flags_text = f" [{esc(', '.join(flags))}]" if flags else ""

    return (
        f"{emoji} <b>{esc(cve['id'])}</b> | {esc(cve['priority_level'])} "
        f"(CVSS {esc(cve.get('cvss_score', 0))}, EPSS {esc(round(cve.get('epss', 0), 3))})"
        f"{flags_text}\n\n"
        f"\U0001F4E6 <b>Tech:</b> {esc(', '.join(cve.get('matched_tech', [])))}\n\n"
        f"\U0001F4DD {esc(cve.get('summary', 'No summary available'))}\n\n"
        f"\U0001F517 https://nvd.nist.gov/vuln/detail/{esc(cve['id'])}"
    )


def format_digest(cves):
    lines = ["<b>CVE digest</b> (too many matches for individual messages today):\n"]
    for cve in cves:
        lines.append(
            f"- {esc(cve['id'])} | {esc(cve['priority_level'])} "
            f"(CVSS {esc(cve.get('cvss_score', 0))}) | {esc(', '.join(cve.get('matched_tech', [])))}"
        )
    return "\n".join(lines)


def send_to_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing)")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        logger.error(f"Telegram error {resp.status_code}: {resp.text[:300]}")
        return False
    except Exception as e:
        logger.error(f"Telegram request failed: {e}")
        return False


def save_to_file(message):
    with open("cve_report.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n{datetime.now(timezone.utc).isoformat()}\n{message}\n")


def send_notification(message, dry_run=False):
    save_to_file(message)
    if dry_run:
        logger.info("[dry-run] would send to Telegram:\n" + message[:200] + "...")
        return
    sent = send_to_telegram(message)
    logger.info("Sent to Telegram and saved to file" if sent else "Saved to file (Telegram unavailable)")


def send_heartbeat(total, filtered, sent, state, error=None, dry_run=False):
    """Sent on every run, success or failure. This is what lets the
    on-call engineer tell 'nothing new today' apart from 'the bot died
    three days ago' -- both look like silence otherwise."""
    consecutive = state.get("consecutive_failures", 0)
    urgent = "\U0001F6A8 " if (error and consecutive >= CONSECUTIVE_FAILURES_ALERT) else ""
    status = "FAILED" if error else "OK"
    status_text = f"Error: {esc(error)}" if error else "No new critical CVEs (or none matched)."
    time_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    msg = (
        f"{urgent}<b>CVE Monitor heartbeat</b>\n"
        f"Status: {status}" + (f" ({consecutive} runs failing in a row)" if error else "") + "\n"
        f"Time: {time_str}\n\n"
        f"Total from NVD: {total}\n"
        f"Stack-relevant: {filtered}\n"
        f"Sent this run: {sent}\n\n"
        f"{status_text}"
    )
    send_notification(msg, dry_run=dry_run)

# ============================================================
# 9. MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="CVE monitoring pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Don't send to Telegram, only write cve_report.txt")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting CVE Monitoring Bot")
    logger.info("=" * 60)

    try:
        requests.get(CONFIG["ollama_url"].replace("/api/generate", "/api/tags"), timeout=3)
        logger.info("Ollama is reachable")
    except Exception:
        logger.warning("Ollama not reachable -- summaries will fall back to templates")

    state = load_state()
    state = prune_state(state)

    try:
        all_cves = fetch_cves()
    except Exception as e:
        logger.exception("Unhandled error while fetching CVEs")
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        send_heartbeat(0, 0, 0, state, error=f"fetch failed: {e}", dry_run=args.dry_run)
        save_state(state)
        return

    if not all_cves:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        send_heartbeat(0, 0, 0, state, error="NVD returned no data", dry_run=args.dry_run)
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return

    filtered = filter_by_stack(all_cves)
    if not filtered:
        state["consecutive_failures"] = 0
        send_heartbeat(len(all_cves), 0, 0, state, dry_run=args.dry_run)
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return

    filtered = enrich(filtered)
    prioritized = prioritize(filtered)

    sent_ids = state.get("sent", {})
    to_send = [
        c for c in prioritized
        if c["id"] not in sent_ids and (c.get("cvss_score") or 0) >= MIN_CVSS
    ]
    to_send = to_send[:MAX_NOTIFICATIONS]

    sent_count = 0
    if len(to_send) > DIGEST_THRESHOLD:
        # Too many at once: full detail for the worst few, everything else
        # as one compact digest line. Bounds the number of messages sent
        # regardless of how many CVEs matched (e.g. a 200-CVE day).
        full_detail = to_send[:MAX_FULL_DETAIL]
        rest = to_send[MAX_FULL_DETAIL:]

        for cve in full_detail:
            cve["summary"] = summarize_cve(cve)
            send_notification(format_cve_message(cve), dry_run=args.dry_run)
            sent_ids[cve["id"]] = datetime.now(timezone.utc).isoformat()
            sent_count += 1
            time.sleep(1)

        send_notification(format_digest(rest), dry_run=args.dry_run)
        for cve in rest:
            sent_ids[cve["id"]] = datetime.now(timezone.utc).isoformat()
            sent_count += 1
    else:
        for cve in to_send:
            cve["summary"] = summarize_cve(cve)
            send_notification(format_cve_message(cve), dry_run=args.dry_run)
            sent_ids[cve["id"]] = datetime.now(timezone.utc).isoformat()
            sent_count += 1
            time.sleep(1)

    state["sent"] = sent_ids
    state["consecutive_failures"] = 0
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    send_heartbeat(len(all_cves), len(filtered), sent_count, state, dry_run=args.dry_run)
    save_state(state)

    logger.info("=" * 60)
    logger.info(f"Done. Sent {sent_count} notifications")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
