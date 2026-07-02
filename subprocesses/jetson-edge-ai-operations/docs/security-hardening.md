# Security Hardening

## User and Password Policy

The subprocess includes `scripts/password-policy.sh`, which installs `libpam-pwquality` and applies a baseline password complexity policy.

Example policy:

```text
minlen = 12
ucredit = -1
lcredit = -1
dcredit = -1
ocredit = -1
retry = 3
enforce_for_root
```

## User Rename Workflow

Use `scripts/user-rename.sh` for a guided user/group rename. Review all prompts before applying changes.

## Baseline Controls

- Unique local admin credentials per device.
- No shared field passwords.
- SSH restricted to management networks.
- Remote access accounts protected by MFA.
- Disk encryption where operationally practical.
- Package holds documented and reviewed.
- Sanitized logs only in source control.
