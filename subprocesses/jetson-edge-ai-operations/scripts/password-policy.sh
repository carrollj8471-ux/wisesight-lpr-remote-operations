#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y libpam-pwquality

if [ -f /etc/security/pwquality.conf ]; then
  sudo cp /etc/security/pwquality.conf /etc/security/pwquality.conf.bak.$(date +%Y%m%d%H%M%S)
fi

sudo tee /etc/security/pwquality.conf >/dev/null <<'POLICY'
minlen = 12
ucredit = -1
lcredit = -1
dcredit = -1
ocredit = -1
retry = 3
enforce_for_root
POLICY

echo "Password quality policy applied."
