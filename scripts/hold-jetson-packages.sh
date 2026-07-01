#!/usr/bin/env bash
set -euo pipefail

PACKAGES=(
  nvidia-l4t-kernel
  nvidia-l4t-kernel-dtbs
  nvidia-l4t-kernel-headers
)

for package in "${PACKAGES[@]}"; do
  if dpkg -s "$package" >/dev/null 2>&1; then
    sudo apt-mark hold "$package"
  fi
done

apt-mark showhold | grep -E 'nvidia-l4t-kernel|nvidia-l4t-kernel-dtbs|nvidia-l4t-kernel-headers' || true
