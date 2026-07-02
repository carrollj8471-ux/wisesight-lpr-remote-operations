# Remote Access Setup

WiseSight field devices need reliable remote administration without exposing broad unmanaged access.

## TeamViewer Host ARM64

Jetson devices require ARM64 packages, not amd64 packages.

```bash
bash scripts/install-teamviewer-arm64.sh
systemctl status teamviewerd --no-pager
teamviewer info
```

## Security Notes

- Require MFA on remote access accounts.
- Remove former staff and vendor access promptly.
- Prefer VPN or zero-trust access for SSH.
- Disable password SSH when key-based access is available.
- Log and review remote support sessions.
- Never commit TeamViewer IDs or screenshots containing them.
