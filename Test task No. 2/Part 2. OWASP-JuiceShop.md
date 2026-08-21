# Part 2. OWASP Juice Shop Vulnerability Assessment

## Environment

- Application: OWASP Juice Shop v17.1.1
- URL: http://localhost:3000
- Browser: Google Chrome
- Operating System: Kali Linux
- Analysis method: Manual testing using browser Developer Tools (DevTools)

No automated vulnerability scanners (Burp Suite, OWASP ZAP, Nikto) were used during this assessment.

## Executive Summary

| Priority | Vulnerability | Risk |
|----------|---------------|------|
| CRITICAL | SQL Injection | Authentication bypass, full database access |
| HIGH | Broken Access Control | Unauthorized admin access |
| HIGH | XSS | Session theft, phishing |
| MEDIUM | Sensitive Data Exposure | Information leakage |
| MEDIUM | Security Misconfiguration | Missing security headers |

**Most critical:** SQL Injection — allows attacker to bypass login and gain administrative access.

---

# 1. Broken Access Control

## OWASP Top 10

**A01:2021 – Broken Access Control**

## Location

```
http://localhost:3000/#/administration
```

## How it was discovered

After logging into the application as an administrator, I manually navigated through the available pages and discovered the Administration panel.

The page allows management of users and application content. Access to this functionality demonstrates the presence of privileged administrative features.

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/part2/Broken%20Access%20Control1.png)

## Business Impact

If an attacker gains administrative privileges, they can:

- modify user accounts;
- delete customer data;
- disable parts of the application;
- completely compromise the integrity of the service.

This could result in service disruption and loss of customer trust.

## Recommendation

- Apply strict Role-Based Access Control (RBAC).
- Verify permissions on every server-side request.
- Restrict administrative endpoints to authorized roles only.
- Perform authorization checks on the backend, not only in the frontend.

---

# 2. Sensitive Data Exposure

## OWASP Top 10

**A02:2021 – Cryptographic Failures (Sensitive Data Exposure)**

## Location

```
http://localhost:3000/ftp
```

## How it was discovered

While exploring the application manually, I discovered an exposed FTP directory.

The directory contains internal files such as:

- encrypt.py
- quarantine
- legal
- coupons_2013.md
- incident-support.kdbx

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/part2/Sensitive%20Data%20Exposure%20(ftp)3.JPG)

## Business Impact

Public access to internal files may expose:

- confidential company information;
- backup files;
- internal documentation;
- credentials or password databases.

Such information could be used for further attacks against the organization.

## Recommendation

- Disable public access to internal directories.
- Store sensitive files outside the web root.
- Apply proper authentication and authorization.
- Regularly review publicly accessible resources.

---

# 3. Security Misconfiguration

## OWASP Top 10

**A05:2021 – Security Misconfiguration**

## Location

HTTP Response Headers

## How it was discovered

Using the browser Developer Tools (Network tab), I inspected HTTP response headers.

Several recommended security headers were missing:

- Content-Security-Policy
- Strict-Transport-Security
- Referrer-Policy

Additionally, the deprecated **Feature-Policy** header was present instead of the modern **Permissions-Policy**.

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/part2/Security%20Misconfiguration2.JPG)

## Business Impact

Missing security headers increase the risk of:

- Cross-Site Scripting (XSS);
- Man-in-the-Middle attacks;
- information leakage through HTTP Referer headers;
- browser abuse of sensitive features.

## Recommendation

Configure appropriate security headers:

- Content-Security-Policy
- Strict-Transport-Security
- Referrer-Policy
- Permissions-Policy

Review the server configuration according to OWASP Secure Header
