# Remote LPR Troubleshooting

## Device Offline

Check the latest heartbeat in `/operations`, then verify:

```bash
ping device-ip
ssh admin@device-ip
systemctl status lpr-agent --no-pager
journalctl -u lpr-agent -n 100 --no-pager
```

Common causes:

- Site internet outage
- VPN route failure
- Device power loss
- Agent token mismatch
- Central API URL misconfigured

## Camera Stream Offline

Run:

```bash
bash scripts/check-camera-stream.sh "rtsp://user:password@camera-ip/stream"
```

If the stream fails:

- Confirm camera power and switch port link.
- Confirm camera IP, credentials, and RTSP path.
- Test from the LPR device, not only from a laptop.
- Check whether the camera allows multiple RTSP clients.

## LPR Service Inactive

Run:

```bash
systemctl status lpr-engine --no-pager
journalctl -u lpr-engine -n 100 --no-pager
sudo systemctl restart lpr-engine
```

Validate that plate snapshots or recognition logs are updating after restart.

## Disk Above 85%

Check large directories:

```bash
sudo du -h -d 1 /var/lib /var/log | sort -h
```

Likely cleanup targets:

- Old plate snapshots
- Rotated service logs
- Crash dumps
- Unused Docker images

## Remote Access Not Ready

For TeamViewer:

```bash
systemctl status teamviewerd --no-pager
teamviewer info
sudo systemctl restart teamviewerd
```
