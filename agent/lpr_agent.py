#!/usr/bin/env python3
"""Lightweight heartbeat agent for WiseSight LPR edge devices."""

import argparse
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


DEFAULT_SERVER_URL = "http://127.0.0.1:5000/api/ops/heartbeat"


def run_command(command, timeout=4):
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""

    return result.stdout.strip()


def service_status(name):
    if not name:
        return "unknown"

    status = run_command(["systemctl", "is-active", name])
    return status or "unknown"


def uptime_pretty():
    uptime_text = run_command(["uptime", "-p"])
    return uptime_text or "unknown"


def disk_percent(path="/"):
    usage = shutil.disk_usage(path)
    return round((usage.used / usage.total) * 100, 1)


def memory_percent():
    meminfo = {}
    with open("/proc/meminfo", "r", encoding="utf-8") as handle:
        for line in handle:
            key, value = line.split(":", 1)
            meminfo[key] = int(value.strip().split()[0])

    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", 0)

    if total == 0:
        return 0

    return round(((total - available) / total) * 100, 1)


def cpu_snapshot():
    with open("/proc/stat", "r", encoding="utf-8") as handle:
        parts = handle.readline().split()[1:]
        values = [int(value) for value in parts]

    idle = values[3] + values[4]
    total = sum(values)
    return idle, total


def cpu_percent():
    idle_1, total_1 = cpu_snapshot()
    time.sleep(0.2)
    idle_2, total_2 = cpu_snapshot()

    idle_delta = idle_2 - idle_1
    total_delta = total_2 - total_1

    if total_delta == 0:
        return 0

    return round((1 - idle_delta / total_delta) * 100, 1)


def temperature_c():
    for thermal_file in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            raw_value = int(thermal_file.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            continue

        if raw_value > 1000:
            return round(raw_value / 1000, 1)

        return float(raw_value)

    tegrastats = run_command(["tegrastats"], timeout=2)
    for part in tegrastats.split():
        if part.startswith("CPU@") and part.endswith("C"):
            try:
                return float(part.replace("CPU@", "").replace("C", ""))
            except ValueError:
                return None

    return None


def private_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "unknown"


def latest_plate_seen(snapshot_dir):
    if not snapshot_dir:
        return None

    directory = Path(snapshot_dir)

    if not directory.exists():
        return None

    files = [path for path in directory.iterdir() if path.is_file()]

    if not files:
        return None

    latest = max(files, key=lambda path: path.stat().st_mtime)
    return datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def build_payload():
    hostname = socket.gethostname()
    site_id = os.environ.get("SITE_ID", "unknown-site")
    device_id = os.environ.get("DEVICE_ID", hostname)
    lpr_service_name = os.environ.get("LPR_SERVICE", "lpr-engine")
    remote_service_name = os.environ.get("REMOTE_ACCESS_SERVICE", "teamviewerd")

    return {
        "site_id": site_id,
        "site_name": os.environ.get("SITE_NAME", site_id),
        "device_id": device_id,
        "hostname": hostname,
        "status": "online",
        "uptime": uptime_pretty(),
        "cpu_percent": cpu_percent(),
        "memory_percent": memory_percent(),
        "disk_percent": disk_percent(os.environ.get("DISK_PATH", "/")),
        "temperature_c": temperature_c(),
        "lpr_service": service_status(lpr_service_name),
        "lpr_sensor_status": os.environ.get("LPR_SENSOR_STATUS", "unknown"),
        "teamviewer_status": service_status(remote_service_name),
        "public_ip": os.environ.get("PUBLIC_IP", "unknown"),
        "private_ip": private_ip(),
        "latency_ms": None,
        "last_plate_seen": latest_plate_seen(os.environ.get("LPR_SNAPSHOT_DIR")),
        "last_heartbeat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def post_heartbeat(server_url, token, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        server_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    if token:
        request.add_header("X-Agent-Token", token)

    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, response.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="Send WiseSight LPR device heartbeats.")
    parser.add_argument("--once", action="store_true", help="Send one heartbeat and exit.")
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.environ.get("HEARTBEAT_INTERVAL", "60")),
        help="Seconds between heartbeats.",
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("OPS_SERVER_URL", DEFAULT_SERVER_URL),
        help="Central heartbeat API URL.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("OPS_AGENT_TOKEN", ""),
        help="Shared agent token for the X-Agent-Token header.",
    )
    args = parser.parse_args()

    while True:
        payload = build_payload()

        try:
            status, body = post_heartbeat(args.server_url, args.token, payload)
            print(f"heartbeat accepted: status={status} body={body}")
        except urllib.error.URLError as error:
            print(f"heartbeat failed: {error}")

        if args.once:
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
