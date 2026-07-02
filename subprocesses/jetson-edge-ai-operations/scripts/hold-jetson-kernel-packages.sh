#!/usr/bin/env bash
set -euo pipefail

PACKAGES=(
  nvidia-l4t-kernel
  nvidia-l4t-kernel-headers
  nvidia-l4t-kernel-dtbs
  nvidia-l4t-display-kernel
)

for package in "${PACKAGES[@]}"; do
  if dpkg -s "$package" >/dev/null 2>&1; then
    sudo apt-mark hold "$package"
  else
    echo "not-installed=$package"
  fi
done

apt-mark showhold | grep -E 'nvidia-l4t-(kernel|display-kernel)' || true
