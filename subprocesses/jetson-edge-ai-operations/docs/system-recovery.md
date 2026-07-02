# NVIDIA L4T Package Recovery

## Scenario

A Jetson L4T kernel package can fail during post-install when the system expects `/dev/mtdblock0`, but `/proc/mtd` shows no exposed MTD partitions. This can leave packages half-configured and block normal APT operations.

## Diagnosis

```bash
sudo dpkg --audit
sudo dpkg --configure -a
sudo apt --fix-broken install
cat /proc/mtd
ls /dev/mtd*
uname -r
```

## Recovery Pattern

```bash
sudo dpkg --configure -a
sudo apt --fix-broken install
sudo dpkg --audit
```

If the running system is stable and vendor kernel updates are not part of the supported deployment path, hold Jetson kernel/BSP packages:

```bash
sudo apt-mark hold \
  nvidia-l4t-kernel \
  nvidia-l4t-kernel-headers \
  nvidia-l4t-kernel-dtbs \
  nvidia-l4t-display-kernel
```

## Lesson Learned

Avoid broad `apt full-upgrade` on Jetson BSP/kernel packages unless the vendor BSP supports the exact upgrade path. Treat Jetson kernel and boot packages as hardware-coupled components, not generic Ubuntu packages.
