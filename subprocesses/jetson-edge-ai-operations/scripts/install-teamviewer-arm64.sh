#!/usr/bin/env bash
set -euo pipefail

ARCH="$(dpkg --print-architecture)"

if [ "$ARCH" != "arm64" ]; then
  echo "This script is intended for Jetson/ARM64 devices. Current architecture: ${ARCH}"
  exit 1
fi

cd "$HOME/Downloads"

if [ ! -f teamviewer-host_arm64.deb ]; then
  wget https://download.teamviewer.com/download/linux/teamviewer-host_arm64.deb
fi

sudo apt install -y ./teamviewer-host_arm64.deb
sudo systemctl enable teamviewerd
sudo systemctl restart teamviewerd
teamviewer info || true
