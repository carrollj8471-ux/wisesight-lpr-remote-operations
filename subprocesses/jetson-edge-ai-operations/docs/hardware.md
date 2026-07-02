# Hardware and OS Baseline

Use this document to capture a sanitized baseline for the Jetson edge host.

## Commands

```bash
uname -m
uname -r
cat /etc/nv_tegra_release
lsblk
df -h
free -h
hostnamectl
```

## Expected Notes

- `uname -m` should report `aarch64` on Jetson ARM64 hardware.
- NVIDIA L4T / JetPack version should be captured from `/etc/nv_tegra_release` when present.
- Root filesystem layout should be documented without exposing serial numbers or customer identifiers.

## Portfolio Framing

This baseline demonstrates embedded Linux awareness, ARM64 operations, and readiness to support edge systems in the field.
