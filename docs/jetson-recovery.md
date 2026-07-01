# Jetson LPR Recovery Playbook

## Broken apt or dpkg State

Run:

```bash
sudo dpkg --configure -a
sudo apt-get -f install
sudo apt-get update
```

If an NVIDIA L4T kernel post-install script fails, capture the exact package name before retrying.

## Missing `/dev/mtdblock0`

Some Jetson kernel post-install scripts expect boot media paths that are not present on every deployment. Do not blindly force package upgrades on production LPR devices. Validate the Jetson model, boot method, and L4T release first.

## Hold Jetson Kernel Packages

After restoring a stable state:

```bash
sudo bash scripts/hold-jetson-packages.sh
apt-mark showhold
```

## Verify Core Services

```bash
systemctl --failed
systemctl status lpr-agent --no-pager
systemctl status lpr-engine --no-pager
systemctl status teamviewerd --no-pager
```

## Validate Device Health Payload

```bash
python3 agent/lpr_agent.py --once
```

Confirm the device updates in `/operations`.
