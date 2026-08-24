# AI Usage Report

## Where AI Was Used

During this assignment, AI was used at several stages.

### 1. Log Parsing Script Development

- AI suggested using **`jq`** for parsing `edr_events.json`.
- AI generated the initial code for an interactive HTML report with filtering and color highlighting.

### 2. Analysis of Results

- AI helped identify events that were easy to miss during manual review.
- AI suggested a structure for reconstructing the attack timeline and organizing the incident report.

---

# What AI Did Well

## 1. Fast Code Generation

AI produced a working Bash script prototype within minutes.

Without AI, writing and debugging the script manually would have taken significantly longer.

For example, AI suggested this approach for extracting IP addresses from `auth.log`:

```
for(i=1;i<=NF;i++){if($i=="from"){src_ip=$(i+1); break}}
```

AI also correctly suggested using **jq** and generated filters for extracting the required fields from `edr_events.json`.

```
jq -r '[.timestamp, "EDR", .event, .user, .src_ip // "-", .detail // "-"] | @csv'
```

---

## 2. Explaining the Results

AI helped interpret the collected logs and distinguish between:

- events that indicated a real attack;
- normal background Internet noise.

This made it easier to reconstruct the incident timeline.

---

# Where AI Made Mistakes

In many cases, AI tended to **overcomplicate** the solution and focused on unnecessary details.

As with any AI-generated code, it was important to verify every result manually instead of trusting it blindly.

---

## Problem 1 — Overly Complex Solutions

AI frequently suggested complicated constructions that were either unnecessary or unreliable.

For example, instead of simply searching for the keyword `from`, AI proposed a regular expression:

```
awk 'match($0, /from ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/, arr) {print arr[1]}'
```

The following solution turned out to be much simpler and more reliable:

```
for(i=1;i<=NF;i++){if($i=="from"){src_ip=$(i+1); break}}
```

---

## Problem 2 — Incorrect Timeline Sorting

Initially, AI suggested sorting events directly by their original timestamps.

However, log timestamps such as:

```
Dec 10 03:00:01
```

cannot be sorted correctly as plain text.

### How I Fixed It

I converted all timestamps into the ISO format:

```
YYYY-MM-DDTHH:MM:SSZ
```

and only then sorted them using:

```
sort -t, -k1
```

After that, all events appeared in the correct chronological order.

---

## Problem 3 — Printing Thousands of Events

The first AI-generated version displayed **every event** in the terminal.

The dataset contained more than **5,000 timeline events**, and sometimes AI even suggested displaying all **15,000 log entries**, making the output unreadable.

### How I Fixed It

I asked AI to display only the most important events.

The final version prints only critical events:

```
# Terminal output — only critical events
tail -n +2 timeline.csv | grep -E "ssh_login_success|user_created|ALERT"
```

while all collected data is still saved to CSV and HTML reports for detailed analysis.

---

# Conclusions

## 1. AI Quickly Generates Working Prototypes

AI significantly speeds up the initial development process.

However, the generated code almost always requires manual refinement, especially regarding:

- log parsing;
- error handling;
- optimization;
- output formatting.

---

## 2. Clear Prompts Produce Better Results

AI performs much better when given precise instructions.

Poor prompt:

```
Parse the logs.
```

Better prompt:

```
Find all "Accepted password" entries in auth.log and extract the username and IP address.
```

---

## 3. Final Verification Was My Responsibility

Even when the generated code worked technically, it could still produce incorrect results.

For example, AI sometimes extracted an IP address incorrectly or proposed a solution that looked correct but did not work with the actual log format.

Every important step had to be verified manually before being included in the final solution.

---

# Final Note

AI should be treated as a development assistant rather than a source of truth.

It is very effective at generating ideas, code, and explanations, but all results must be reviewed, verified, and, if necessary, corrected by a human before being used.
