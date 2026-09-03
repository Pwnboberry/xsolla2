# CVE Monitoring Bot

A bot that checks for new security vulnerabilities (CVEs) every day and sends a short summary to Telegram — no human needed.

**What it does, step by step:**
1. Gets new CVEs from NVD (the official vulnerability database)
2. Keeps only the ones related to our tech stack (nginx, PostgreSQL, etc.)
3. Checks if each CVE is:
   - Already being actively exploited (CISA KEV list)
   - Likely to be exploited soon (EPSS score)
4. Gives each CVE a priority: CRITICAL / HIGH / MEDIUM / LOW
5. Uses a local AI model to write a short, plain-English summary
6. Sends everything to Telegram

## Why NVD?

- It's the official, most complete CVE database
- Free, no API key required (though one helps with rate limits)
- Lets us filter by "last modified date" — important because CVE scores get updated after they're first published

Other option considered: **OSV.dev**. It's better for package-level bugs (npm, PyPI), but NVD is better for infrastructure-level stuff like nginx or Kubernetes, which is what our stack needs.

## Why a local AI model (Ollama)?

- No paid API key needed
- Runs fully on our own machine, nothing sent to a third party
- The AI only writes summaries — it never decides how dangerous a CVE is. That decision is made by code (see below), not the AI.

⚠️ Note: on a machine without a GPU, the bigger model (`llama3.2:3b`) was too slow and kept timing out. We switched to the smaller `llama3.2:1b` — faster, but sometimes writes worse summaries. Real examples of this are in `report.md`.

## Setup

```
git clone <this-repo>
cd cve-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install Ollama and pull the model:
```
ollama pull llama3.2:1b
ollama serve &
```

Set up your secrets:
```
cp .env.example .env
nano .env
```
Fill in:
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` — get this from @BotFather in Telegram
- `NVD_API_KEY` — optional, only needed for frequent runs

## How to run it

```
python3 cve_monitor.py --dry-run   # test run, no Telegram message sent
python3 cve_monitor.py             # real run, sends to Telegram
```

To run it automatically every day (this is how it was actually configured for testing — see report.md for a week of real automated runs):
```
0 7 * * * cd /path/to/cve-monitor && /path/to/venv/bin/python3 cve_monitor.py >> cron.log 2>&1
```

## Config options (`config.yaml`)

| Setting | What it does |
|---|---|
| `stack` | List of technologies to watch for |
| `lookback_days` | How many days back to search NVD |
| `max_notifications` | Max messages per run |
| `min_cvss` | Ignore CVEs below this score |
| `digest_threshold` | If more CVEs than this match, switch to short digest mode |
| `state_retention_days` | How long we remember a CVE was already sent |
| `thresholds` | Score cutoffs for CRITICAL / HIGH / MEDIUM |
| `ollama_model` | Which local AI model to use |

All secrets stay in `.env` — never in `config.yaml`, never in the code.

## Key design choices

**The AI does not decide priority.**
Priority is calculated by plain code: CVSS score + EPSS score + whether it's on the CISA "actively exploited" list. If a CVE is on that list, it's always marked CRITICAL — no matter what the AI or CVSS says. This keeps priority decisions predictable and repeatable.

**No duplicate messages.**
Every sent CVE ID is saved in `state.json`. Next run, it checks that list first and skips anything already sent. Tested this myself: ran the bot twice in a row — first run sent 4 messages, second run (same CVE data) sent 0. Works as expected.

**Always sends a status message, even if nothing happened.**
This way, "no new CVEs today" and "the bot is broken" never look the same in the chat — silence never means "everything is fine."

**Handles CVE floods.**
If too many CVEs match in one run, only the top few get a full AI summary. The rest go into one short list message. This stops the bot from spamming the channel on a bad day.

**AI answers are checked before sending.**
If the AI's answer is missing the required structure, mentions a different CVE than expected, or times out — the bot doesn't send a broken message. It falls back to a simple template built directly from the NVD description, and clearly labels it as a fallback (not AI-written).

## Known limitations

- Only one main data source (NVD), plus two extra signals (KEV, EPSS) — no cross-checking with other CVE databases
- Stack filtering is just keyword matching (whole words) in the description — not 100% precise. Example: a CVE about "Django" won't match "python" unless the word "Python" is also in the text
- If something fails partway through a run, it just retries from scratch next time — no per-item retry queue
- On slow (CPU-only) hardware, a real portion of AI summaries fail and fall back to the template — exact numbers are in `report.md`

## Example Telegram message

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/tg-bot.JPG)
