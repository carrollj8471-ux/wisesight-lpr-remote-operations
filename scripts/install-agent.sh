#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/wisesight-lpr-remote-ops}"
CONFIG_DIR="${CONFIG_DIR:-/etc/wisesight}"
SERVICE_NAME="lpr-agent.service"

sudo mkdir -p "$APP_DIR" "$CONFIG_DIR"
sudo cp -R agent scripts "$APP_DIR/"
sudo cp agent/lpr-agent.service "/etc/systemd/system/${SERVICE_NAME}"

if [ ! -f "${CONFIG_DIR}/lpr-agent.env" ]; then
  sudo tee "${CONFIG_DIR}/lpr-agent.env" >/dev/null <<'ENV'
SITE_ID=surface-lot-main
SITE_NAME=Main Surface Lot
DEVICE_ID=
OPS_SERVER_URL=http://127.0.0.1:5000/api/ops/heartbeat
OPS_AGENT_TOKEN=
LPR_SERVICE=lpr-engine
REMOTE_ACCESS_SERVICE=teamviewerd
LPR_SENSOR_STATUS=online
LPR_SNAPSHOT_DIR=/var/lib/wisesight/snapshots
HEARTBEAT_INTERVAL=60
ENV
fi

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager
