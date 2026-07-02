#!/usr/bin/env bash
set -euo pipefail

OLD_USER="${1:-}"
NEW_USER="${2:-}"

if [ -z "$OLD_USER" ] || [ -z "$NEW_USER" ]; then
  echo "Usage: $0 old-user new-user"
  exit 1
fi

if id "$NEW_USER" >/dev/null 2>&1; then
  echo "Target user already exists: $NEW_USER"
  exit 2
fi

echo "About to rename user and primary group: $OLD_USER -> $NEW_USER"
read -r -p "Type RENAME to continue: " confirmation

if [ "$confirmation" != "RENAME" ]; then
  echo "Aborted."
  exit 3
fi

sudo usermod -l "$NEW_USER" "$OLD_USER"
sudo groupmod -n "$NEW_USER" "$OLD_USER"
sudo usermod -d "/home/$NEW_USER" -m "$NEW_USER"
sudo chage -l "$NEW_USER"
