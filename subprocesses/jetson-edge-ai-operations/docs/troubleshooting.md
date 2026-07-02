# Troubleshooting

## Before and After Pattern

For each incident, document:

- Symptom
- Command output summary
- Root cause hypothesis
- Recovery command sequence
- Final validation
- Follow-up prevention

## APT / dpkg Problems

```bash
sudo dpkg --audit
sudo dpkg --configure -a
sudo apt --fix-broken install
apt-mark showhold
```

## Failed Services

```bash
systemctl --failed
systemctl status teamviewerd --no-pager
journalctl -u teamviewerd -n 100 --no-pager
```

## System Snapshot

```bash
bash scripts/system-info.sh
bash scripts/health-check.sh
```

## Redaction

Before committing examples, remove hostnames, IPs, usernames, serial numbers, TeamViewer IDs, tokens, and customer/site identifiers.
