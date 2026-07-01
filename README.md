# WiseSight LPR Remote Operations

## Purpose

Demonstrate a remote operations platform for WiseSight license plate recognition parking enforcement deployments across multiple physical locations.

The project focuses on monitoring LPR edge devices, passive sensor health, plate-read activity, remote access readiness, and incident response workflows for parking enforcement operations.

---

## Features

- LPR parking enforcement operations dashboard
- Searchable plate/vehicle lookup demo
- Enforcement area visualization
- Plate-read confidence scores
- Last-seen timestamps
- Plate-read snapshot review
- Remote LPR site health dashboard
- Device heartbeat API for Jetson, mini PC, or edge-host agents
- Passive LPR sensor status reporting
- TeamViewer/SSH service readiness checks
- Jetson recovery and provisioning documentation
- Docker Compose demo runtime

---

## Remote Operations Platform

Open the remote operations dashboard:

http://127.0.0.1:5000/operations

The operations module tracks:

- Device online/offline/warning status
- CPU, memory, disk, temperature, uptime, and heartbeat age
- LPR service, passive sensor status, and TeamViewer daemon status
- Last plate seen at each edge device
- Open incidents across enforcement sites

Heartbeat agents post JSON to:

```text
POST /api/ops/heartbeat
X-Agent-Token: your-shared-token
```

Example agent run:

```powershell
python agent/lpr_agent.py --once --server-url http://127.0.0.1:5000/api/ops/heartbeat
```

---

## Security Documentation

- [Vulnerability Assessment Report](docs/vulnerability-assessment-report.md)
- [Architecture](docs/architecture.md)
- [Provisioning](docs/provisioning.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Jetson Recovery](docs/jetson-recovery.md)
- [Remote Access](docs/remote-access.md)

---

## Folder Structure

wisesight-lpr-remote-operations/

- app.py
- docker-compose.yml
- requirements.txt
- README.md

agent/
- lpr_agent.py
- lpr-agent.service

configs/
- example-sites.yaml
- nginx.conf

docs/
- architecture.md
- provisioning.md
- troubleshooting.md
- jetson-recovery.md
- remote-access.md

scripts/
- health-check.sh
- hold-jetson-packages.sh
- install-agent.sh
- install-teamviewer-arm64.sh

templates/
- index.html
- operations.html

static/
- css/style.css
- js/app.js
- snapshots/

---

## Install

```powershell
pip install -r requirements.txt
```

---

## Run

```powershell
python app.py
```

---

## Run with Docker Compose

```powershell
docker compose up
```

---

## Open Dashboards

Parking enforcement dashboard:

http://127.0.0.1:5000

Remote LPR operations dashboard:

http://127.0.0.1:5000/operations

## Camera Access Policy

This project intentionally does not connect to cameras, open live feeds, request
stream URLs, or store camera credentials. Edge devices report passive operational
status such as `LPR_SENSOR_STATUS`, `lpr_service`, and `last_plate_seen`.
