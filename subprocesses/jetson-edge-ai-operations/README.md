# Jetson Edge AI Operations Subprocess

This subprocess documents the provisioning, recovery, hardening, and remote administration workflow for NVIDIA Jetson ARM64 edge devices used in WiseSight LPR Remote Operations.

It is intentionally scoped to edge-device lifecycle management. It does not provide camera access, live feeds, stream URLs, or camera credential handling.

## Purpose

Take a Jetson reComputer-class device from raw hardware to a stable, remotely managed Linux edge host ready to report operational health into the WiseSight LPR Remote Operations platform.

## Key Skills Demonstrated

- NVIDIA Jetson / ARM64 Linux administration
- L4T / JetPack package recovery
- APT and dpkg troubleshooting
- Remote access deployment with TeamViewer Host ARM64
- User and password policy management
- systemd service troubleshooting
- Edge-device operational readiness
- Bash scripting and system diagnostics

## Hardware Profile

- NVIDIA Jetson Orin Nano / reComputer-class device
- ARM64 / aarch64 architecture
- Ubuntu-based NVIDIA L4T / JetPack system
- NVMe or vendor-supported root filesystem

## Operational Problem Solved

During setup, NVIDIA L4T kernel packages can enter a half-configured state when package post-install scripts expect an MTD/QSPI boot device that is not exposed by the running system. This blocks normal package installation and can leave the device in an unstable maintenance state.

The subprocess covers dpkg diagnosis, package manager recovery, Jetson kernel package holds, running-kernel validation, and long-term prevention of unsupported BSP/kernel upgrades.

## Subprocess Flow

1. Capture hardware and OS baseline.
2. Validate NVIDIA L4T / JetPack version.
3. Recover broken APT/dpkg state if needed.
4. Hold Jetson kernel/BSP packages that should not be upgraded broadly.
5. Configure remote access services for field support.
6. Apply user and password policy hardening.
7. Run repeatable health diagnostics.
8. Store only sanitized logs and screenshots.

## Scripts

- `scripts/system-info.sh` - captures host, kernel, L4T, disk, memory, services, held packages, and remote-access status.
- `scripts/health-check.sh` - compact operational health report for field support.
- `scripts/install-teamviewer-arm64.sh` - installs TeamViewer Host for ARM64 Linux.
- `scripts/hold-jetson-kernel-packages.sh` - holds Jetson L4T kernel/BSP packages.
- `scripts/password-policy.sh` - applies password complexity policy with `pam_pwquality`.
- `scripts/user-rename.sh` - guided user/group rename helper.

## Documentation

- `docs/hardware.md`
- `docs/jetson-flashing.md`
- `docs/system-recovery.md`
- `docs/remote-access.md`
- `docs/security-hardening.md`
- `docs/troubleshooting.md`

## Redaction Rules

Do not commit:

- Passwords
- TeamViewer IDs
- Private IPs
- Public IPs tied to a site
- Serial numbers
- Tokens
- Full logs with personal or customer data
- Hostnames that identify a live deployment

Use `logs/sanitized-samples/` and `screenshots/` only for redacted examples.
