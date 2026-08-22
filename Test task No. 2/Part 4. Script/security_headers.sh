#!/bin/bash
# check_headers.sh — проверка security-заголовков у списка доменов.

if [ -z "$1" ]; then
    echo "Usage: $0 <domains.txt | domain1 domain2 ...>"
    exit 1
fi

OUTPUT_FILE="security_headers_report.csv"
HSTS_MIN=15552000   # 180 дней — см. обоснование в README.md

# === Цвета ===
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# === Список доменов: либо файл (если $1 — существующий файл), либо аргументы ===
DOMAINS=()
if [ -f "$1" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        line=$(echo "$line" | sed 's/#.*//' | tr -d '[:space:]')
        [ -z "$line" ] && continue
        DOMAINS+=("$line")
    done < "$1"
else
    DOMAINS=("$@")
fi

TOTAL=${#DOMAINS[@]}
if [ "$TOTAL" -eq 0 ]; then
    echo "Список доменов пуст."
    exit 1
fi

echo "domain,strict-transport-security,content-security-policy,x-frame-options,x-content-type-options,referrer-policy,overall" > "$OUTPUT_FILE"

i=0
for domain in "${DOMAINS[@]}"; do
    i=$((i + 1))
    echo -e "${GREEN}[$i/$TOTAL] $domain ...${NC}"

    # ЗАМЕНА: используем HEAD-запрос (-I) + -k + --noproxy '*'
    headers=$(curl -sIL -k --noproxy '*' --connect-timeout 15 "https://$domain" 2>/dev/null)

    if [ -z "$headers" ]; then
        echo "$domain,ERROR,ERROR,ERROR,ERROR,ERROR,ERROR" >> "$OUTPUT_FILE"
        echo -e "  ${RED}ERROR: домен недоступен / таймаут${NC}\n"
        continue
    fi

    hsts=$(echo "$headers" | grep -i '^strict-transport-security:' | tail -n1 | cut -d' ' -f2- | tr -d '\r')
    csp=$(echo "$headers"  | grep -i '^content-security-policy:'   | tail -n1 | cut -d' ' -f2- | tr -d '\r')
    xfo=$(echo "$headers"  | grep -i '^x-frame-options:'           | tail -n1 | cut -d' ' -f2- | tr -d '\r')
    xcto=$(echo "$headers" | grep -i '^x-content-type-options:'    | tail -n1 | cut -d' ' -f2- | tr -d '\r')
    rp=$(echo "$headers"   | grep -i '^referrer-policy:'           | tail -n1 | cut -d' ' -f2- | tr -d '\r')

    # === HSTS: есть заголовок — ещё не значит, что он полезен ===
    if [ -z "$hsts" ]; then
        s_hsts="MISSING"; c_hsts=$RED
    else
        max_age=$(echo "$hsts" | grep -oE 'max-age=[0-9]+' | cut -d'=' -f2)
        if [ -z "$max_age" ] || [ "$max_age" -lt "$HSTS_MIN" ]; then
            s_hsts="WARN"; c_hsts=$YELLOW      # max-age=1 и т.п. — формально есть, толку нет
        else
            s_hsts="GOOD"; c_hsts=$GREEN
        fi
    fi

    # === CSP: WARN, если политика себя же обнуляет ===
    if [ -z "$csp" ]; then
        s_csp="MISSING"; c_csp=$RED
    elif echo "$csp" | grep -qiE "unsafe-inline|unsafe-eval|(script-src|default-src)[^;]*\*"; then
        s_csp="WARN"; c_csp=$YELLOW
    else
        s_csp="GOOD"; c_csp=$GREEN
    fi

    # === X-Frame-Options: значение имеет значение ===
    if [ -z "$xfo" ]; then
        s_xfo="MISSING"; c_xfo=$RED
    elif echo "$xfo" | grep -qiE '^(deny|sameorigin)$'; then
        s_xfo="GOOD"; c_xfo=$GREEN
    else
        s_xfo="WARN"; c_xfo=$YELLOW            # напр. устаревший ALLOW-FROM
    fi

    # === X-Content-Type-Options: единственное осмысленное значение — nosniff ===
    if [ -z "$xcto" ]; then
        s_xcto="MISSING"; c_xcto=$RED
    elif echo "$xcto" | grep -qi '^nosniff$'; then
        s_xcto="GOOD"; c_xcto=$GREEN
    else
        s_xcto="WARN"; c_xcto=$YELLOW
    fi

    # === Referrer-Policy: unsafe-url сливает полный referrer — это не GOOD ===
    if [ -z "$rp" ]; then
        s_rp="MISSING"; c_rp=$RED
    elif echo "$rp" | grep -qi 'unsafe-url'; then
        s_rp="WARN"; c_rp=$YELLOW
    else
        s_rp="GOOD"; c_rp=$GREEN
    fi

    # === Итог по домену ===
    if [ "$s_hsts" = "MISSING" ] || [ "$s_csp" = "MISSING" ] || [ "$s_xfo" = "MISSING" ] || [ "$s_xcto" = "MISSING" ] || [ "$s_rp" = "MISSING" ]; then
        overall="MISSING"; c_overall=$RED
    elif [ "$s_hsts" = "WARN" ] || [ "$s_csp" = "WARN" ] || [ "$s_xfo" = "WARN" ] || [ "$s_xcto" = "WARN" ] || [ "$s_rp" = "WARN" ]; then
        overall="WARN"; c_overall=$YELLOW
    else
        overall="GOOD"; c_overall=$GREEN
    fi

    echo "$domain,$s_hsts,$s_csp,$s_xfo,$s_xcto,$s_rp,$overall" >> "$OUTPUT_FILE"

    echo -e "  HSTS: ${c_hsts}$s_hsts${NC} | CSP: ${c_csp}$s_csp${NC} | XFO: ${c_xfo}$s_xfo${NC} | XCTO: ${c_xcto}$s_xcto${NC} | RP: ${c_rp}$s_rp${NC}"
    echo -e "  Overall: ${c_overall}$overall${NC}\n"
done

echo "Done! Результаты сохранены в: $OUTPUT_FILE"
