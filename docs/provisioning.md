# LPR Device Provisioning

## Target Device

This flow is intended for NVIDIA Jetson, ARM64 Linux boxes, or small x86 edge hosts used at remote LPR locations.

## Baseline Steps

1. Install Ubuntu or the vendor-supported Jetson Linux image.
2. Set a stable hostname such as `wisesight-edge-01`.
3. Create an admin user with sudo access.
4. Install system updates after validating Jetson package compatibility.
5. Install Python 3, `ffmpeg`, `curl`, and system monitoring tools.
6. Install the WiseSight heartbeat agent.
7. Configure site identity and passive LPR sensor status settings.
8. Enable remote access through TeamViewer or SSH over VPN.
9. Register the device with the central operations dashboard.

## Agent Install

From the repository root on the edge device:

```bash
sudo bash scripts/install-agent.sh
```

Edit:

```bash
sudo nano /etc/wisesight/lpr-agent.env
```

Recommended fields:

```text
SITE_ID=surface-lot-main
SITE_NAME=Main Surface Lot
DEVICE_ID=jetson-j3011-01
OPS_SERVER_URL=https://ops.example.com/api/ops/heartbeat
OPS_AGENT_TOKEN=replace-with-shared-secret
LPR_SERVICE=lpr-engine
REMOTE_ACCESS_SERVICE=teamviewerd
LPR_SENSOR_STATUS=online
LPR_SNAPSHOT_DIR=/var/lib/wisesight/snapshots
HEARTBEAT_INTERVAL=60
```

Restart after editing:

```bash
sudo systemctl restart lpr-agent
sudo systemctl status lpr-agent --no-pager
```

## Jetson Package Hold

For Jetson devices where kernel package upgrades have caused boot or post-install failures, hold the L4T kernel packages:

```bash
sudo bash scripts/hold-jetson-packages.sh
```
