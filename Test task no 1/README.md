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
- `jq` — for parsing EDR JSON logs

## Installing dependencies

```bash
# Install jq (Debian/Ubuntu/Kali)
sudo apt-get update
sudo apt-get install jq -y
```

Check the installation:

```bash
jq --version
```

## Installing the script

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/log-timeline-analyzer.git
cd log-timeline-analyzer
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

## Example output

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/build_timeline/logs.JPG)
