# AI Usage

## AI tools used

I used ChatGPT and Claude during this assignment for:

- developing and reviewing the Bash script;
- improving the README documentation;
- explaining some OWASP vulnerabilities;
- clarifying TLS concepts and security headers.

---

## What AI did well

ChatGPT helped me:

- explain security concepts in simple language;
- improve the readability and logic of the Bash script;
- speed up research on HTTP security headers and TLS configuration.

---

## Where AI was wrong

### 1. Incorrect interpretation of X-Frame-Options

At first, ChatGPT reported that some websites were vulnerable because the `X-Frame-Options` header was missing.

After manually reviewing the HTTP responses, I discovered that some websites protect themselves using the modern `frame-ancestors` directive inside the `Content-Security-Policy` header instead. In reality, those websites were not vulnerable.

---

### 2. Incorrect assumptions during the Juice Shop analysis

While reviewing OWASP Juice Shop, ChatGPT initially suggested checking several findings that were not valid for my version of the application.

I manually verified every reported vulnerability before including it in the final report.

---

The Bash script and the README were developed together with AI (Claude). Below is an honest list of the mistakes AI made during the process and how they were corrected.

### 3. The first version of the script was overcomplicated

AI suggested a much more complex Bash implementation with additional logic (detailed `curl` error handling, temporary files, and complicated redirect parsing). For this assignment, such an implementation was unnecessary. The script was eventually simplified into a cleaner and more practical version.

### 4. Incorrect diagnosis of the network issue

When almost every domain (except one) started failing with timeouts, AI immediately assumed the problem was caused by **DPI blocking based on SNI**. Although this sounded reasonable, it turned out not to be the actual cause. AI presented this hypothesis before fully verifying it.

---

## Summary

All issues were corrected during the assignment. The final version of the Bash script and the README were tested against real websites and work correctly.

This assignment was a good example of why AI-generated code and AI-based troubleshooting should always be verified manually instead of being trusted immediately, especially when writing code or diagnosing networking and timeout-related problems.
