
# Security Headers Checker

A simple Bash script that checks common HTTP security headers for one or more domains.

The script verifies not only whether a header is present, but also whether it is configured correctly.

It checks the following headers:

| Header | Purpose |
|---|---|
| `Strict-Transport-Security` (HSTS) | Forces HTTPS, prevents SSL-stripping |
| `Content-Security-Policy` (CSP) | Restricts sources of scripts/styles, mitigates XSS |
| `X-Frame-Options` | Prevents clickjacking via iframes |
| `X-Content-Type-Options` | Blocks MIME-type sniffing |
| `Referrer-Policy` | Controls how much referrer data leaks to other sites |

For each domain, the script generates a CSV report with one of the following statuses:

| Status | Meaning |
|---|---|
| 🟢 **GOOD** | Header is present **and** correctly configured |
| 🟡 **WARN** | Header is present, but configured insecurely or suboptimally |
| 🔴 **MISSING** | Header is absent entirely |
| ⚫ **ERROR** | The domain could not be checked (network/DNS/TLS failure) |

---

## Requirements

The script only requires:

- `bash`
- `curl`

Install curl if it's missing:

```bash
sudo apt update
sudo apt install curl
```

That's it — no Python, no external libraries, no pip.

---

## Repository structure

```text
task2-security-headers-checker/
├── check_headers.sh
├── domains.txt
└── README.md
```

## 🚀 Getting started

**1. Clone the repository**

```bash
git clone https://github.com/Pwnboberry/xsolla2.git
cd xsolla2/task2-security-headers-checker
```

**2. Verify the files are there**

```bash
ls
```

Expected output:
check_headers.sh
domains.txt
README.md

**3. Make the script executable**

```bash
chmod +x check_headers.sh
```

**4. Run it**

Using a file with domains (one per line, `#` for comments):

```bash
./check_headers.sh domains.txt
```

Or pass domains directly as arguments:

```bash
./check_headers.sh xsolla.com paypal.com github.com
```

---

## Output

The script prints a colorized report in the terminal and saves the results to:

```text
security_headers_report.csv
```

CSV columns:

```text
domain,
strict-transport-security,
content-security-policy,
x-frame-options,
x-content-type-options,
referrer-policy,
overall
```

---

## Evaluation criteria

A header being *present* doesn't mean it's *doing anything useful* — a header like
`Strict-Transport-Security: max-age=1` technically exists, but provides essentially
zero protection. So the script doesn't just check presence — it checks the **value**
against a threshold, based on common industry guidance (OWASP, Mozilla Observatory).

### Strict-Transport-Security

| Status | Rule |
|---|---|
| 🟢 GOOD | `max-age ≥ 15552000` (180 days) |
| 🟡 WARN | `max-age` is set but too small, or malformed |
| 🔴 MISSING | Header is absent |

> **Why 180 days?** OWASP and Mozilla both recommend a *minimum* of six months for
> HSTS `max-age`, with a year or more preferred for production. Browsers remember the HSTS policy only for the specified time. A very small value (for example, `max-age=1`) technically enables HSTS, but provides almost no practical protection.

### Content-Security-Policy

| Status | Rule |
|---|---|
| 🟢 GOOD | Policy exists, no obviously unsafe directives |
| 🟡 WARN | Contains `unsafe-inline`, `unsafe-eval`, or a wildcard (`*`) in `script-src`/`default-src` |
| 🔴 MISSING | Header is absent |

### X-Frame-Options

| Status | Rule |
|---|---|
| 🟢 GOOD | `DENY` or `SAMEORIGIN` |
| 🟡 WARN | Deprecated/unsupported value (e.g. `ALLOW-FROM`) |
| 🔴 MISSING | Header is absent |

### X-Content-Type-Options

| Status | Rule |
|---|---|
| 🟢 GOOD | `nosniff` |
| 🟡 WARN | Any other value |
| 🔴 MISSING | Header is absent |

### Referrer-Policy

| Status | Rule |
|---|---|
| 🟢 GOOD | Any policy except `unsafe-url` |
| 🟡 WARN | `unsafe-url` (leaks the full referrer, even cross-origin and over plain HTTP) |
| 🔴 MISSING | Header is absent |

### Overall status

- **GOOD** – all headers are present and correctly configured.
- **WARN** – no headers are missing, but at least one is weakly configured.
- **MISSING** – at least one required header is absent.

## Error handling

The script handles:

- DNS errors
- connection timeouts
- redirects
- invalid TLS certificates
- unreachable websites

If an error occurs, the domain is marked as `ERROR` and the script continues checking the next one.

---

## Limitations

This is a basic header checker.

It does not replace a full security audit.

Some websites may use modern alternatives (for example `frame-ancestors` instead of `X-Frame-Options`), so manual verification may still be required.
