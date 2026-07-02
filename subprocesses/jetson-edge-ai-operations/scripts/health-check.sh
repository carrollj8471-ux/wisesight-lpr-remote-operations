#!/usr/bin/env bash
set -euo pipefail

echo "host=$(hostname)"
echo "arch=$(uname -m)"
echo "kernel=$(uname -r)"
echo "l4t=$(cat /etc/nv_tegra_release 2>/dev/null || echo not-detected)"
echo "uptime=$(uptime -p)"
echo "disk_root=$(df -h / | awk 'NR==2 {print $5}')"
echo "memory=$(free -m | awk '/Mem:/ {printf "%.1f%%", $3/$2*100}')"
echo "failed_services=$(systemctl --failed --no-legend | wc -l)"
echo "held_packages=$(apt-mark showhold | tr '\n' ',' | sed 's/,$//')"
echo "teamviewer_status=$(systemctl is-active teamviewerd 2>/dev/null || echo inactive)"
