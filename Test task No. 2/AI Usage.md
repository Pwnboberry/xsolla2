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

### 4. Documentation and code went out of sync

When reviewing the finished script together with Claude, I described removing the `-k` flag from `curl` in `report.md` (explaining why disabling TLS certificate validation was a bad idea for a security tool), 
but the actual fix was never applied to `check_headers.sh` - the `-k` flag was still there

Claude caught this by checking the real script file line by line against what the report claimed, instead of trusting the report's description.

The reason for the mismatch was simple: I fixed the code on my local machine, but forgot to push the changes to the remote GitHub repository. 

As a result, the documentation was up to date, but the code in the repository was not.

This case also showed that AI (Claude) is good at catching small inconsistencies that can arise from human oversight. It doesn't fix mistakes for me, but it helps me notice them when I might have otherwise missed them.

**How I fixed it:** removed `-k` from the `curl` call and added `--max-time 30` as an additional safeguard against slow responses that `--connect-timeout` alone doesn't cover, then re-ran the script to confirm the results still
matched expectations.

This was a good reminder that a written explanation of a fix and the actual ode doing that fix can silently drift apart - I need to verify the file itself, not just re-read my own description of it.

---

## Summary

All issues were corrected during the assignment. The final version of the Bash script and the README were tested against real websites and work correctly.

This assignment was a good example of why AI-generated code and AI-based troubleshooting should always be verified manually instead of being trusted immediately, especially when writing code or diagnosing networking and timeout-related problems.
