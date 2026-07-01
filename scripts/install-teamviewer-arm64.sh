#!/usr/bin/env bash
set -euo pipefail

ARCH="$(dpkg --print-architecture)"

if [ "$ARCH" != "arm64" ]; then
  echo "This script is intended for Jetson/ARM64 devices. Current architecture: ${ARCH}"
  exit 1
fi

TMP_DEB="/tmp/teamviewer-host_arm64.deb"

wget -O "$TMP_DEB" "https://download.teamviewer.com/download/linux/teamviewer-host_arm64.deb"
sudo apt-get update
sudo apt-get install -y "$TMP_DEB"
sudo systemctl enable --now teamviewerd
teamviewer info || true
