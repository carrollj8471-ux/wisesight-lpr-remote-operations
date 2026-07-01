#!/usr/bin/env bash
set -euo pipefail

CAMERA_URL="${1:-${CAMERA_RTSP_URL:-}}"

if [ -z "$CAMERA_URL" ]; then
  echo "Usage: $0 rtsp://user:pass@camera-ip/stream"
  exit 1
fi

if ffprobe -v error -rtsp_transport tcp -i "$CAMERA_URL" -show_entries stream=codec_type -of csv=p=0 >/dev/null 2>&1; then
  echo "camera_status=online"
  exit 0
else
  echo "camera_status=offline"
  exit 2
fi
