#!/bin/bash
# build_timeline.sh - Полный парсинг логов + HTML отчет
# Usage: ./build_timeline.sh

echo "🔍 Building timeline..."

# ============================================
# 1. ПАРСИМ ЛОГИ В CSV
# ============================================

echo "timestamp,source,event_type,user,src_ip,detail" > timeline.csv

AUTH_LOG_YEAR="${AUTH_LOG_YEAR:-2016}"
# ---------- AUTH LOG ----------
if [ -f "auth.log" ]; then
    echo "  📁 Parsing auth.log..."
    grep -E "Accepted password|Failed password|Invalid user|POSSIBLE BREAK-IN|useradd|sudo" auth.log | \
    awk -v year="$AUTH_LOG_YEAR" '{

        month=$1; day=$2; time=$3
        m["Jan"]="01"; m["Feb"]="02"; m["Mar"]="03"; m["Apr"]="04"
        m["May"]="05"; m["Jun"]="06"; m["Jul"]="07"; m["Aug"]="08"
        m["Sep"]="09"; m["Oct"]="10"; m["Nov"]="11"; m["Dec"]="12"
	ts=year "-" m[month] "-" day "T" time "Z"
        
        if ($0 ~ /Accepted password/) {
            event="ssh_login_success"
            for(i=1;i<=NF;i++){if($i=="from"){src_ip=$(i+1); break}}
            user=$9
            detail="SSH login successful"
        }
        else if ($0 ~ /Failed password/) {
            event="ssh_login_failed"
            for(i=1;i<=NF;i++){if($i=="from"){src_ip=$(i+1); break}}
            user=$9
            detail="SSH login failed"
        }
        else if ($0 ~ /Invalid user/) {
            event="ssh_invalid_user"
            for(i=1;i<=NF;i++){if($i=="Invalid" && $(i+1)=="user"){user=$(i+2); break}}
            for(i=1;i<=NF;i++){if($i=="from"){src_ip=$(i+1); break}}
            detail="Invalid SSH user"
        }
        else if ($0 ~ /POSSIBLE BREAK-IN/) {
            event="breakin_attempt"
            user="-"
            src_ip=$(NF-1)
            detail="Possible break-in attempt"
        }
	    else if ($0 ~ /useradd\[.*new user/) {
            event="user_created"
            for(i=1;i<=NF;i++){if($i=="name="){user=substr($(i+1),1,length($(i+1))-1); break}}
            if(user=="") user=$NF
            src_ip="-"
            detail="New user created"
        }
        else if ($0 ~ /sudo.*COMMAND=/) {
            event="sudo_command"
            user=$8; gsub(/:/, "", user)
            src_ip="-"
            detail=substr($0, index($0, "COMMAND="))
        }
        else { next }
        
        if (src_ip == "" || src_ip == "from") src_ip = "-"
        if (user == "" || user == "from") user = "-"
        
	gsub(",", ";", detail)
        printf "%s,Auth,%s,%s,%s,%s\n", ts, event, user, src_ip, detail
    }' >> timeline.csv
fi

# ---------- EDR LOGS ----------
if [ -f "edr_events.json" ] && command -v jq &> /dev/null; then
    echo "  📁 Parsing EDR logs..."
    jq -r '
        [.timestamp, "EDR", .event, .user, .src_ip // "-", .detail // "-"] | 
        @csv
    ' edr_events.json >> timeline.csv || echo "⚠️  jq failed to parse edr_events.json — check its format" >&2
fi

# ---------- WEB LOGS ----------
if [ -f "access.log" ]; then
    echo "  📁 Parsing access.log..."
    grep -E "wp-login|admin|\.php" access.log | \
    awk '{
        if (match($0, /\[([0-9]{2})\/([A-Za-z]{3})\/([0-9]{4}):([0-9]{2}:[0-9]{2}:[0-9]{2})/, arr)) {
            day=arr[1]; month=arr[2]; year=arr[3]; time=arr[4]
            m["Jan"]="01"; m["Feb"]="02"; m["Mar"]="03"; m["Apr"]="04"
            m["May"]="05"; m["Jun"]="06"; m["Jul"]="07"; m["Aug"]="08"
            m["Sep"]="09"; m["Oct"]="10"; m["Nov"]="11"; m["Dec"]="12"
            ts=year "-" m[month] "-" day "T" time "Z"
            src_ip=$1
            
            if (match($0, /"([A-Z]+) ([^ ]*)/, url)) {
                method=url[1]; path=url[2]
            } else { method="-"; path="-" }
            
            if (path ~ /wp-login/) { event="wp_login_attempt" }
            else if (path ~ /\.php$/) { event="web_php_request" }
            else if (path ~ /admin/) { event="admin_scan" }
            else { event="web_request" }
            
            detail="HTTP: " path
            printf "%s,Web,%s,-,%s,%s\n", ts, event, src_ip, detail
        }
    }' >> timeline.csv
fi

# Сортируем
echo "  📊 Sorting..."
(head -1 timeline.csv && tail -n +2 timeline.csv | sort -t, -k1) > timeline_sorted.csv
mv timeline_sorted.csv timeline.csv

# ============================================
# 2. СОЗДАЕМ HTML ОТЧЕТ
# ============================================

total=$(tail -n +2 timeline.csv | wc -l)
edr=$(grep -c ",EDR," timeline.csv 2>/dev/null || echo "0")
auth=$(grep -c ",Auth," timeline.csv 2>/dev/null || echo "0")
web=$(grep -c ",Web," timeline.csv 2>/dev/null || echo "0")
critical=$(grep -cE "ssh_login_success|user_created|ALERT|mysqldump" timeline.csv 2>/dev/null || echo "0")

echo "  📄 Creating HTML report..."

cat > timeline_report.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Timeline Report</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }
        h1 { color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; margin-bottom: 20px; }
        .stats { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
        .stats span { display: inline-block; margin-right: 30px; }
        .stats .num { color: #f0883e; font-weight: bold; }
        .controls { margin: 15px 0; padding: 10px; background: #161b22; border-radius: 8px; }
        .controls input { background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; padding: 6px 12px; border-radius: 6px; width: 300px; }
        .controls input:focus { outline: none; border-color: #58a6ff; }
        .scroll { max-height: 80vh; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { background: #161b22; color: #58a6ff; padding: 10px 8px; text-align: left; border-bottom: 2px solid #30363d; position: sticky; top: 0; z-index: 10; }
        td { padding: 6px 8px; border-bottom: 1px solid #21262d; vertical-align: top; }
        tr:hover { background: #1c2128; }
        .critical { background: #2d1b1b; }
        .critical td:first-child { border-left: 3px solid #f85149; }
        .warning { background: #1d231b; }
        .warning td:first-child { border-left: 3px solid #d29922; }
        .timestamp { color: #8b949e; font-family: monospace; white-space: nowrap; }
        .source { font-weight: bold; padding: 2px 8px; border-radius: 12px; font-size: 11px; }
        .source-edr { background: #1f2937; color: #60a5fa; }
        .source-auth { background: #1f2937; color: #34d399; }
        .source-web { background: #1f2937; color: #f472b6; }
        .event { font-family: monospace; }
        .user { color: #f0883e; font-family: monospace; }
        .ip { color: #60a5fa; font-family: monospace; }
        .detail { color: #8b949e; }
        .badge { display: inline-block; padding: 1px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; }
        .badge-critical { background: #f85149; color: #fff; }
        .badge-high { background: #d29922; color: #fff; }
        .badge-medium { background: #1f6feb; color: #fff; }
        .badge-low { background: #30363d; color: #8b949e; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #0d1117; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #484f58; }
    </style>
</head>
<body>
    <h1>🔍 Timeline Report</h1>
EOF

cat >> timeline_report.html << EOF
    <div class="stats">
        <span>📊 Total: <span class="num">$total</span></span>
        <span>🔴 EDR: <span class="num">$edr</span></span>
        <span>🟢 Auth: <span class="num">$auth</span></span>
        <span>🩷 Web: <span class="num">$web</span></span>
        <span>🚨 Critical: <span class="num">$critical</span></span>
    </div>
    
    <div class="controls">
        🔍 Filter: <input type="text" id="search" placeholder="Type to filter..." onkeyup="filterTable()">
        <span style="margin-left:15px;color:#8b949e;">Showing: <span id="count">$total</span> events</span>
    </div>
    
    <div class="scroll">
    <table id="timeline">
        <thead>
            <tr>
                <th style="width:180px;">Timestamp</th>
                <th style="width:60px;">Source</th>
                <th style="width:170px;">Event</th>
                <th style="width:100px;">User</th>
                <th style="width:130px;">IP</th>
                <th>Detail</th>
            </tr>
        </thead>
        <tbody>
EOF

tail -n +2 timeline.csv | \
awk -F, '{
    timestamp=$1; source=$2; event=$3; user=$4; src_ip=$5; detail=$6
    
    severity="low"
    if (event ~ /ssh_login_success|user_created|ALERT|mysqldump|authorized_keys|log_cleared/) severity="critical"
    else if (event ~ /ssh_login_failed|breakin_attempt|wp_login/) severity="high"
    else if (event ~ /Invalid|404|scan/) severity="medium"
    
    if (length(detail) > 80) detail = substr(detail, 1, 77) "..."
    if (length(user) > 12) user = substr(user, 1, 9) "..."
    if (length(src_ip) > 15) src_ip = substr(src_ip, 1, 12) "..."
    
    row_class = (severity == "critical") ? "critical" : (severity == "high" ? "warning" : "")
    badge = (severity == "critical") ? "badge-critical" : (severity == "high" ? "badge-high" : (severity == "medium" ? "badge-medium" : "badge-low"))
    badge_text = toupper(severity)
    source_class = (source == "EDR") ? "source-edr" : (source == "Auth" ? "source-auth" : "source-web")
    
    printf "<tr class=\"%s\">", row_class
    printf "<td class=\"timestamp\">%s</td>", substr(timestamp,1,19)
    printf "<td><span class=\"source %s\">%s</span></td>", source_class, source
    printf "<td class=\"event\">%s</td>", event
    printf "<td class=\"user\">%s</td>", (user=="-"?"":user)
    printf "<td class=\"ip\">%s</td>", (src_ip=="-"?"":src_ip)
    printf "<td class=\"detail\">%s <span class=\"badge %s\">%s</span></td>", detail, badge, badge_text
    printf "</tr>\n"
}' >> timeline_report.html

cat >> timeline_report.html << 'EOF'
        </tbody>
    </table>
    </div>
    
    <script>
        function filterTable() {
            const input = document.getElementById('search');
            const filter = input.value.toLowerCase();
            const rows = document.getElementById('timeline').getElementsByTagName('tr');
            let visible = 0;
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.getElementsByTagName('td');
                let match = false;
                for (let j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.toLowerCase().indexOf(filter) > -1) {
                        match = true;
                        break;
                    }
                }
                row.style.display = (filter === '' || match) ? '' : 'none';
                if (filter === '' || match) visible++;
            }
            document.getElementById('count').textContent = visible;
        }
    </script>
    
    <p style="color:#8b949e;margin-top:15px;font-size:12px;">
        💡 Use search to filter | Scroll to see all events
    </p>
</body>
</html>
EOF

# ============================================
# 3. ВЫВОД В ТЕРМИНАЛ
# ============================================

echo ""
echo "========================================"
echo "✅ Done! Total events: $total"
echo "========================================"
echo ""

# Показываем самые важные события
echo "🚨 CRITICAL EVENTS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -n +2 timeline.csv | \
grep -E "ssh_login_success|user_created|ALERT|mysqldump|authorized_keys" | \
head -20 | \
awk -F, '{printf "  %s | %s | %-12s | %-15s | %s\n", substr($1,1,19), $3, $4, $5, substr($6,1,50)}'

echo ""
echo "📁 Files created:"
echo "  - timeline.csv (raw data)"
echo "  - timeline_report.html (open in browser)"
echo ""
echo "🌐 Open in browser:"
echo "  firefox timeline_report.html"
echo "  google-chrome timeline_report.html"
