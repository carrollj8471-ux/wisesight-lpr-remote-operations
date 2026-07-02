#!/usr/bin/env bash
set -euo pipefail

echo "===== Host ====="
hostnamectl || true

echo
echo "===== Kernel ====="
uname -a

echo
echo "===== NVIDIA L4T ====="
cat /etc/nv_tegra_release 2>/dev/null || echo "Not a Jetson/L4T system"

echo
echo "===== Block Devices ====="
lsblk

echo
echo "===== Disk ====="
df -h

echo
echo "===== Memory ====="
free -h

echo
echo "===== Failed Services ====="
systemctl --failed || true

echo
echo "===== Held Packages ====="
apt-mark showhold || true

echo
echo "===== TeamViewer ====="
systemctl is-active teamviewerd || true
teamviewer info 2>/dev/null || true
