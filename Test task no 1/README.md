# Log Timeline Analyzer

A tool for analyzing security logs and building an attack timeline.

## Description

The script analyzes three types of logs:

- `edr_events.json` — EDR events (processes, files, network)
- `auth.log` — authentication logs (SSH, sudo, user creation)
- `access.log` — web server logs (WordPress attacks)

The output includes:

- A CSV file with all events
- An HTML report with filtering and color coding
- A list of critical events in the terminal

## Requirements

- Linux (Kali, Ubuntu, Debian) or macOS
- Bash 4.0+
- `gawk` (GNU awk) - the script uses `match()` with a capture array, a GNU extension not available in plain POSIX awk/mawk
- `jq` - for parsing EDR JSON logs
- 
## Installing dependencies

```bash
# Install jq (Debian/Ubuntu/Kali)
sudo apt-get update
sudo apt-get install gawk jq -y
```

Check the installation:

```bash
gawk --version
jq --version
```

## Installing the script

```bash
# Clone the repository
git clone https://github.com/Pwnboberry/xsolla2.git
cd "xsolla2/Test task no 1"

```

Make the script executable:

```bash
chmod +x build_timeline.sh
```

## Usage

### 1. Prepare the log files

Place the log files in the same directory as the script:

```text
~/logs/
├── build_timeline.sh
├── edr_events.json
├── auth.log
└── access.log
```

### 2. Run the script

```bash
./build_timeline.sh
```

## Why are only suspicious events filtered?

The logs contain more than 15,000 lines, but only a few of them represent real threats.

The final timeline does not include:

- multiple `Failed password` entries if they are not followed by a successful authentication;
- login attempts with non-existent users (`Invalid user`), which are typical Internet scanning activity;
- individual `POSSIBLE BREAK-IN` messages, which are warning messages and, without additional signs of compromise, do not confirm an actual attack.

We focus only on events that indicate a real attack.

## Why are IP addresses extracted separately?

In `auth.log`, the IP address may appear in different positions. We search for the keyword `from` and take the following argument. This guarantees correct IP extraction even if the log format is slightly different.

## Why are all 5,000+ events not displayed in the terminal?

More than 5,000 lines are difficult to read. We display only critical events (4–10 entries) in the terminal, while all other events are exported to CSV and HTML for detailed analysis.

## Expected log formats

Place the log files in the same directory as the script, using these
exact names and formats:

**`auth.log`** - standard Linux syslog format (as produced by rsyslog),
one event per line, no year in the timestamp:
```
Dec 13 21:27:14 hostname sshd[31287]: Accepted password for deploy from 203.0.113.77 port 52288 ssh2
```

⚠️ Syslog auth.log lines don't include a year. The script assumes **2016** by default (the year of this assignment's dataset). 
To analyze logs from a different year, set the `AUTH_LOG_YEAR` environment variable before running:

```
AUTH_LOG_YEAR=2024 ./build_timeline.sh
```

**`access.log`** - Apache/Nginx combined log format, includes its own year in the timestamp, no extra configuration needed:

```
153.107.193.211 - - [13/Dec/2016:20:00:30 -0800] "GET / HTTP/1.1" 200 10230 "-" "Mozilla/5.0 ..."
```

**`edr_events.json`** - JSON Lines (one JSON object per line, not a JSON array), with these fields expected:

```
{"timestamp": "2016-12-13T21:27:14Z", "host": "web-prod-01", "event": "logon", "user": "deploy", "src_ip": "203.0.113.77", "detail": "interactive SSH session"}
```

Required fields: `timestamp`, `event`, `user`. Optional: `src_ip`, `detail` (both default to `-` if missing).

All three files are optional — the script processes whichever ones are present in the directory and skips the rest.


## Example output

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/build_timeline/logs.JPG)
