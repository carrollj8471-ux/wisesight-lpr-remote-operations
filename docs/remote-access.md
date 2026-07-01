# Remote Access Readiness

## Supported Methods

- TeamViewer Host for ARM64 Jetson deployments.
- SSH through VPN for managed networks.
- Local console access for recovery when the network path is unavailable.

## TeamViewer Checks

```bash
systemctl is-active teamviewerd
teamviewer info
```

Install on ARM64:

```bash
sudo bash scripts/install-teamviewer-arm64.sh
```

## SSH Checks

```bash
systemctl is-active ssh
ss -tulpn | grep ':22'
```

Recommended SSH posture:

- Disable password login when key-based access is available.
- Restrict SSH to VPN or management networks.
- Keep a documented break-glass account for field recovery.

## Dashboard Signal

The heartbeat agent reports `teamviewer_status` or another configured remote-access service through `REMOTE_ACCESS_SERVICE`. A stopped remote-access daemon moves the device into warning state, even when the LPR service is still running.
