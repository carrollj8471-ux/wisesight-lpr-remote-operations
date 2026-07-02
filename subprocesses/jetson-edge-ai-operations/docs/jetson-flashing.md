# Jetson Flashing Notes

This repo does not include vendor images or proprietary flashing bundles. Use this file to document the safe process followed for a specific Jetson model.

## Checklist

- Confirm exact Jetson module and carrier board.
- Confirm supported JetPack / L4T release.
- Back up needed data before flashing.
- Use vendor-supported flashing instructions.
- Validate boot mode and root filesystem target.
- Confirm the running kernel after first boot.

## Validation

```bash
uname -a
cat /etc/nv_tegra_release
lsblk
df -h
```

## Caution

Avoid broad OS upgrades that replace vendor BSP/kernel packages unless the target JetPack/L4T release explicitly supports the upgrade path.
