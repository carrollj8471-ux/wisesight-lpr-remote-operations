# WiseSight LPR Remote Operations Architecture

## Overview

WiseSight LPR Remote Operations combines a parking enforcement review dashboard with a lightweight remote operations layer for LPR edge deployments. The central Flask app receives heartbeats from field devices, stores the latest health state in SQLite, and renders a multi-site operations dashboard.

## Components

- `agent/lpr_agent.py`: Linux edge-device heartbeat agent.
- `app.py`: Flask web app, heartbeat API, device health model, and dashboard routes.
- `templates/operations.html`: Remote operations dashboard.
- `scripts/health-check.sh`: On-device Linux health snapshot.
- `configs/example-sites.yaml`: Example site inventory model.
- `agent/lpr-agent.service`: systemd unit for running the agent continuously.

## Data Flow

1. A Jetson, mini PC, or edge host runs the heartbeat agent every 60 seconds.
2. The agent collects OS, service, passive sensor, and last-plate signals.
3. The agent posts JSON to `/api/ops/heartbeat`.
4. The Flask app upserts the device record in `lpr_device_heartbeats`.
5. The dashboard classifies devices as online, warning, or offline.
6. Operators inspect site health, device metrics, and open incidents from `/operations`.

## Health Model

Devices are marked:

- `online` when the heartbeat is fresh and core services are active.
- `warning` when disk, memory, temperature, LPR sensor, LPR service, or remote-access checks need attention.
- `offline` when the device reports offline or the heartbeat is stale for more than 10 minutes.

## Portfolio Value

This project demonstrates Linux administration, edge-device monitoring, service recovery awareness, passive LPR sensor status reporting, Flask API development, and production-style operational documentation.

## Subprocess: Jetson Edge AI Operations

The Jetson Edge AI Operations subprocess documents the lower-level device lifecycle required before an edge host can reliably participate in WiseSight LPR Remote Operations. It covers hardware baseline capture, NVIDIA L4T recovery, package holds, remote access readiness, user policy hardening, and system diagnostics.

See `subprocesses/jetson-edge-ai-operations/README.md`.
