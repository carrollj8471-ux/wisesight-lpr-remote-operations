#!/usr/bin/env bash
set -euo pipefail

SITE_ID="${SITE_ID:-unknown-site}"
DEVICE_ID="${DEVICE_ID:-$(hostname)}"
TIMESTAMP="$(date -Iseconds)"

echo "site_id=${SITE_ID}"
echo "device_id=${DEVICE_ID}"
echo "timestamp=${TIMESTAMP}"
echo "kernel=$(uname -r)"
echo "arch=$(uname -m)"
echo "uptime=$(uptime -p)"
echo "disk_usage=$(df -h / | awk 'NR==2 {print $5}')"
echo "memory_usage=$(free -m | awk '/Mem:/ {printf \"%.1f%%\", $3/$2*100}')"
echo "load_average=$(uptime | awk -F'load average:' '{print $2}')"
echo "failed_services=$(systemctl --failed --no-legend | wc -l)"
echo "lpr_service=$(systemctl is-active "${LPR_SERVICE:-lpr-engine}" 2>/dev/null || echo inactive)"
echo "teamviewer_status=$(systemctl is-active teamviewerd 2>/dev/null || echo inactive)"

if command -v nvpmodel >/dev/null 2>&1; then
  echo "jetson_power_mode=$(sudo nvpmodel -q 2>/dev/null | head -1 || true)"
fi

if command -v tegrastats >/dev/null 2>&1; then
  timeout 3 tegrastats 2>/dev/null | head -1 || true
fi
