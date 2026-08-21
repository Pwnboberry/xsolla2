# Part 2. OWASP Juice Shop Vulnerability Assessment

## Environment

- Application: OWASP Juice Shop v17.1.1
- URL: http://localhost:3000
- Browser: Google Chrome
- Operating System: Kali Linux
- Analysis method: Manual testing using browser Developer Tools (DevTools)

No automated vulnerability scanners (Burp Suite, OWASP ZAP, Nikto) were used during this assessment.

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

Review the server configuration according to OWASP Secure Headers recommendations.

---

# 4. Cross-Site Scripting (XSS)

## OWASP Top 10

**A03:2021 – Injection (Cross-Site Scripting)**

## Location

Search field

Payload used:

```html
<img src=x onerror=alert(1)>
```

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/part2/the%20search%20bar-xss.JPG)


## How it was discovered

The payload was entered into the application search field.

The application accepted the input without proper sanitization.

The payload was reflected back into the page, demonstrating that user input is processed without sufficient validation.

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/part2/XSS4.JPG)

## Business Impact

An attacker could:

- execute arbitrary JavaScript;
- steal user session cookies;
- impersonate users;
- redirect visitors to malicious websites.

This may lead to account compromise and phishing attacks.

## Recommendation

- Escape all user-controlled output.
- Validate and sanitize input.
- Use a strict Content Security Policy.
- Prefer framework-provided output encoding.

---

# 5. SQL Injection

## OWASP Top 10

**A03:2021 – Injection (SQL Injection)**

## Location

Login page

## How it was discovered

Manual testing of the authentication form revealed SQL Injection behavior.

The application accepted SQL Injection payloads during authentication.

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/part2/sql%20inj5.png)

After that, the account was automatically logged in with administrator privileges.

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/part2/payloadSQL.png)

## Business Impact

SQL Injection may allow an attacker to:

- bypass authentication;
- read confidential database information;
- modify stored records;
- delete application data;
- gain complete control over the database.

The potential impact is critical because it affects confidentiality, integrity, and availability.

## Recommendation

- Use parameterized SQL queries (Prepared Statements).
- Never concatenate user input into SQL queries.
- Validate user input.
- Apply the principle of least privilege for database accounts.

---

# Result

During the assessment, five different vulnerability classes were identified:

| Vulnerability | OWASP Category |
|---------------|----------------|
| Broken Access Control | A01:2021 |
| Sensitive Data Exposure | A02:2021 |
| SQL Injection | A03:2021 |
| Cross-Site Scripting | A03:2021 |
| Security Misconfiguration | A05:2021 |

The vulnerabilities were identified manually using browser functionality and developer tools without performing attacks against any external systems.
