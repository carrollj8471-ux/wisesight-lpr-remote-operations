# WiseSight LPR Remote Operations

## Purpose

Demonstrate a remote operations platform for WiseSight license plate recognition parking enforcement deployments across multiple physical locations.

The project focuses on monitoring LPR edge devices, camera health, plate-read activity, remote access readiness, and incident response workflows for parking enforcement operations.

---

## Features

- LPR parking enforcement operations dashboard
- Searchable plate/vehicle lookup demo
- Enforcement area visualization
- Plate-read confidence scores
- Last-seen timestamps
- Plate-read snapshot review
- Remote LPR site health dashboard
- Device heartbeat API for Jetson, mini PC, or camera-server agents
- Camera RTSP watchdog scripts
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
- LPR service, camera stream, and TeamViewer daemon status
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
- check-camera-stream.sh
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

## Open Front Door Live Stream

Start the Flask app, then open:

http://127.0.0.1:5000/doorbell

The front door doorbell uses WebRTC, so the stream must be opened in a browser.
Click **Start Live Stream** on that page. RTSP/VLC/OpenCV will not work for this
doorbell because it advertises `WEB_RTC` only.

---

## Google Nest Doorbell Connection

Google/Nest doorbells require OAuth through Google's Device Access / Smart Device
Management API. The helper script in `scripts/google_doorbell_camera.py` uses
the official API flow and will not bypass Google account security.

Required setup:

- Create a Google Device Access project and OAuth client.
- Copy `.env.example` to `.env`.
- Fill in the `.env` values for your Device Access project, OAuth client, token,
  and front door device.
- Keep `.env` private. It is ignored by git.

Example:

```powershell
Copy-Item .env.example .env
notepad .env
```

The script also accepts command-line flags, but `.env` is safer than putting
secrets in source code or terminal history.

Get the account-linking URL:

```powershell
python scripts/google_doorbell_camera.py auth-url
```

Open the URL, grant access to your doorbell, then copy the `code=` value from
the redirect URL and exchange it:

```powershell
python scripts/google_doorbell_camera.py exchange-code --code YOUR_AUTH_CODE
```

Store the returned refresh token securely:

```text
GOOGLE_REFRESH_TOKEN=YOUR_REFRESH_TOKEN
```

List authorized devices:

```powershell
python scripts/google_doorbell_camera.py list-devices
```

Generate a short-lived RTSP stream URL for a compatible doorbell/camera:

```powershell
python scripts/google_doorbell_camera.py rtsp-url
```

Preview the RTSP stream with OpenCV:

```powershell
python scripts/google_doorbell_camera.py rtsp-url --open
```

Some newer Google Home cameras/doorbells advertise `WEB_RTC` instead of `RTSP`.
For those, generate an SDP offer in a WebRTC app and pass it to:

```powershell
python scripts/google_doorbell_camera.py webrtc-answer --offer-file offer.sdp
```
