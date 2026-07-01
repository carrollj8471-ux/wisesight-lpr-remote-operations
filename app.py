from datetime import datetime, timedelta
import os
import random
import sqlite3
import threading
import time

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from scripts.google_doorbell_camera import (
    DEFAULT_ACCESS_TOKEN,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_SECRET,
    DEFAULT_CLIENT_SECRET_FILE,
    DEFAULT_DEVICE_NAME,
    DEFAULT_PROJECT_ID,
    DEFAULT_REFRESH_TOKEN,
    Config,
    DoorbellError,
    generate_webrtc_answer,
    load_env_file,
    load_oauth_client_file,
    refresh_access_token,
)


load_env_file()
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.environ.get(
    "WISESIGHT_DB_PATH",
    os.path.join(BASE_DIR, "lpr_operations.db"),
)
SNAPSHOT_FOLDER = os.path.join(BASE_DIR, "snapshots")
OPS_AGENT_TOKEN = os.environ.get("OPS_AGENT_TOKEN", "")

SIMULATED_TRUCKS = [
    "KW18472",
    "KW19301",
    "KW20015",
    "KW21109",
    "KW21988",
    "KW22517",
    "KW23044",
    "KW24102",
]

CAMERAS = [
    "North Entry LPR Camera",
    "South Exit LPR Camera",
    "Central Permit Camera",
    "West Lane LPR Camera",
    "Violation Review Camera",
    "Short-Term Parking Camera",
    "East Perimeter LPR Camera",
]

OPS_SITE_COORDINATES = {
    "garage-downtown": {"top": 28, "left": 31},
    "surface-lot-main": {"top": 53, "left": 54},
    "campus-permit-zone": {"top": 34, "left": 74},
    "event-overflow": {"top": 70, "left": 23},
}

SAMPLE_OPS_DEVICES = [
    {
        "site_id": "surface-lot-main",
        "site_name": "Main Surface Lot",
        "device_id": "jetson-j3011-01",
        "hostname": "wisesight-edge-01",
        "status": "online",
        "uptime": "8 days, 4 hours",
        "cpu_percent": 21.4,
        "memory_percent": 48.2,
        "disk_percent": 62.0,
        "temperature_c": 57.5,
        "lpr_service": "active",
        "camera_rtsp": "reachable",
        "teamviewer_status": "active",
        "public_ip": "198.51.100.22",
        "private_ip": "10.20.4.12",
        "latency_ms": 38,
        "last_plate_seen": "2026-07-01 16:40:22",
        "last_heartbeat": "2026-07-01 17:54:10",
    },
    {
        "site_id": "garage-downtown",
        "site_name": "Downtown Parking Garage",
        "device_id": "mini-pc-north-02",
        "hostname": "wisesight-north-02",
        "status": "warning",
        "uptime": "3 days, 12 hours",
        "cpu_percent": 64.7,
        "memory_percent": 71.3,
        "disk_percent": 86.0,
        "temperature_c": 63.4,
        "lpr_service": "active",
        "camera_rtsp": "reachable",
        "teamviewer_status": "active",
        "public_ip": "203.0.113.40",
        "private_ip": "10.20.8.21",
        "latency_ms": 82,
        "last_plate_seen": "2026-07-01 16:12:03",
        "last_heartbeat": "2026-07-01 17:53:44",
    },
    {
        "site_id": "campus-permit-zone",
        "site_name": "Campus Permit Zone",
        "device_id": "jetson-r4020-01",
        "hostname": "wisesight-remote-01",
        "status": "offline",
        "uptime": "unknown",
        "cpu_percent": 0,
        "memory_percent": 0,
        "disk_percent": 74.0,
        "temperature_c": None,
        "lpr_service": "inactive",
        "camera_rtsp": "unreachable",
        "teamviewer_status": "inactive",
        "public_ip": "203.0.113.88",
        "private_ip": "10.40.2.19",
        "latency_ms": None,
        "last_plate_seen": "2026-07-01 10:08:19",
        "last_heartbeat": "2026-07-01 17:23:15",
    },
]

SAMPLE_OPS_ALERTS = [
    {
        "site_id": "garage-downtown",
        "device_id": "mini-pc-north-02",
        "severity": "warning",
        "message": "Root disk is above 85%. Review retention on plate-read snapshots.",
    },
    {
        "site_id": "campus-permit-zone",
        "device_id": "jetson-r4020-01",
        "severity": "critical",
        "message": "Device heartbeat is stale and LPR service is inactive.",
    },
]

CAMERA_LOCATIONS = [
    {"name": "North Entry LPR Camera", "top": 5, "left": 58, "short_name": "North"},
    {"name": "South Exit LPR Camera", "top": 93, "left": 30, "short_name": "South"},
    {"name": "Central Permit Camera", "top": 46, "left": 63, "short_name": "Central"},
    {"name": "West Lane LPR Camera", "top": 40, "left": 16, "short_name": "West"},
    {"name": "Violation Review Camera", "top": 48, "left": 36, "short_name": "Review"},
    {"name": "Short-Term Parking Camera", "top": 51, "left": 53, "short_name": "Short"},
    {"name": "East Perimeter LPR Camera", "top": 44, "left": 89, "short_name": "East"},
]

LOT_ZONES = {
    "lime": {
        "name": "Permit Zone A",
        "color": "#bdf47f",
        "label_top": 40,
        "label_left": 18,
    },
    "red": {
        "name": "Violation Review Zone",
        "color": "#ef7770",
        "label_top": 47,
        "label_left": 38,
    },
    "blue": {
        "name": "Short-Term Parking Zone",
        "color": "#7f8ff4",
        "label_top": 47,
        "label_left": 53,
    },
    "amber": {
        "name": "Visitor Parking Zone",
        "color": "#efc16d",
        "label_top": 45,
        "label_left": 70,
    },
    "green": {
        "name": "Residential Permit Zone",
        "color": "#72dd86",
        "label_top": 42,
        "label_left": 88,
    },
    "purple_north": {
        "name": "Garage Entry Zone",
        "color": "#b866ee",
        "label_top": 7,
        "label_left": 68,
    },
    "purple_south": {
        "name": "Garage Exit Zone",
        "color": "#c65bee",
        "label_top": 91,
        "label_left": 43,
    },
}

LOT_POSITIONS = {
    "KW18472": {"top": 76, "left": 53, "zone_key": "blue"},
    "KW19301": {"top": 35, "left": 22, "zone_key": "lime"},
    "KW20015": {"top": 47, "left": 39, "zone_key": "red"},
    "KW21109": {"top": 52, "left": 55, "zone_key": "blue"},
    "KW21988": {"top": 65, "left": 35, "zone_key": "red"},
    "KW22517": {"top": 57, "left": 71, "zone_key": "amber"},
    "KW23044": {"top": 26, "left": 67, "zone_key": "purple_north"},
    "KW24102": {"top": 49, "left": 85, "zone_key": "green"},
}


os.makedirs(SNAPSHOT_FOLDER, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS truck_locations (
                truck_number TEXT PRIMARY KEY,
                zone TEXT,
                confidence REAL,
                snapshot_file TEXT,
                camera_name TEXT,
                last_seen TEXT
            )
            """
        )

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(truck_locations)").fetchall()
        }

        if "camera_name" not in columns:
            conn.execute(
                "ALTER TABLE truck_locations ADD COLUMN camera_name TEXT DEFAULT ''"
            )

        seed_missing_trucks(conn)
        normalize_existing_trucks(conn)
        init_ops_tables(conn)


def init_ops_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lpr_device_heartbeats (
            site_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            site_name TEXT,
            hostname TEXT,
            status TEXT,
            uptime TEXT,
            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,
            temperature_c REAL,
            lpr_service TEXT,
            camera_rtsp TEXT,
            teamviewer_status TEXT,
            public_ip TEXT,
            private_ip TEXT,
            latency_ms REAL,
            last_plate_seen TEXT,
            last_heartbeat TEXT,
            PRIMARY KEY (site_id, device_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lpr_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )

    heartbeat_count = conn.execute(
        "SELECT COUNT(*) AS count FROM lpr_device_heartbeats"
    ).fetchone()["count"]

    if heartbeat_count == 0:
        for device in SAMPLE_OPS_DEVICES:
            seeded_device = device.copy()

            if seeded_device.get("status") == "offline":
                seeded_device["last_heartbeat"] = timestamp_minutes_ago(31)
                seeded_device["last_plate_seen"] = timestamp_minutes_ago(212)
            else:
                seeded_device["last_heartbeat"] = timestamp_minutes_ago(1)
                seeded_device["last_plate_seen"] = timestamp_minutes_ago(8)

            upsert_ops_device(conn, seeded_device)

    alert_count = conn.execute(
        "SELECT COUNT(*) AS count FROM lpr_alerts"
    ).fetchone()["count"]

    if alert_count == 0:
        for alert in SAMPLE_OPS_ALERTS:
            conn.execute(
                """
                INSERT INTO lpr_alerts (
                    site_id,
                    device_id,
                    severity,
                    message,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'open', ?)
                """,
                (
                    alert["site_id"],
                    alert["device_id"],
                    alert["severity"],
                    alert["message"],
                    current_timestamp(),
                ),
            )


def seed_missing_trucks(conn):
    existing = {
        row["truck_number"]
        for row in conn.execute("SELECT truck_number FROM truck_locations").fetchall()
    }

    for truck_number in SIMULATED_TRUCKS:
        if truck_number in existing:
            continue

        conn.execute(
            """
            INSERT INTO truck_locations (
                truck_number,
                zone,
                confidence,
                snapshot_file,
                camera_name,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                truck_number,
                zone_for_truck(truck_number),
                random_confidence(),
                f"{truck_number}.jpg",
                camera_for_truck(truck_number),
                current_timestamp(),
            ),
        )


def normalize_existing_trucks(conn):
    for truck_number in SIMULATED_TRUCKS:
        conn.execute(
            """
            UPDATE truck_locations
            SET snapshot_file = COALESCE(NULLIF(snapshot_file, ''), ?),
                camera_name = ?,
                last_seen = COALESCE(NULLIF(last_seen, ''), ?),
                confidence = COALESCE(confidence, ?),
                zone = ?
            WHERE truck_number = ?
            """,
            (
                f"{truck_number}.jpg",
                camera_for_truck(truck_number),
                current_timestamp(),
                random_confidence(),
                zone_for_truck(truck_number),
                truck_number,
            ),
        )


def random_zone():
    zone = random.choice(list(LOT_ZONES.values()))
    space = random.randint(1, 12)
    return f"{zone['name']} - Space {space}"


def zone_for_truck(truck_number):
    position = LOT_POSITIONS.get(truck_number)

    if not position:
        return random_zone()

    zone = LOT_ZONES[position["zone_key"]]
    space = SIMULATED_TRUCKS.index(truck_number) + 1
    return f"{zone['name']} - Space {space}"


def camera_for_truck(truck_number):
    position = LOT_POSITIONS.get(truck_number)

    if not position:
        return random.choice(CAMERAS)

    zone_camera_map = {
        "lime": "West Lane LPR Camera",
        "red": "Violation Review Camera",
        "blue": "Short-Term Parking Camera",
        "amber": "Central Permit Camera",
        "green": "East Perimeter LPR Camera",
        "purple_north": "North Entry LPR Camera",
        "purple_south": "South Exit LPR Camera",
    }

    return zone_camera_map[position["zone_key"]]


def random_confidence():
    return round(random.uniform(0.89, 0.98), 2)


def current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def timestamp_minutes_ago(minutes):
    return (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")


def parse_timestamp(value):
    if not value:
        return None

    for date_format in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value[:19], date_format)
        except ValueError:
            continue

    return None


def heartbeat_age_minutes(last_heartbeat):
    heartbeat_at = parse_timestamp(last_heartbeat)

    if not heartbeat_at:
        return None

    age = datetime.now() - heartbeat_at
    return max(0, round(age.total_seconds() / 60))


def classify_device_health(device):
    age_minutes = heartbeat_age_minutes(device.get("last_heartbeat"))

    if device.get("status") == "offline" or (
        age_minutes is not None and age_minutes > 10
    ):
        return "offline"

    warning_checks = [
        device.get("status") == "warning",
        (device.get("disk_percent") or 0) >= 85,
        (device.get("memory_percent") or 0) >= 90,
        (device.get("temperature_c") or 0) >= 78,
        device.get("lpr_service") not in ("active", "running", "ok"),
        device.get("camera_rtsp") not in ("reachable", "online", "ok"),
        device.get("teamviewer_status") not in ("active", "running", "ok"),
    ]

    if any(warning_checks):
        return "warning"

    return "online"


def upsert_ops_device(conn, payload):
    now = current_timestamp()
    conn.execute(
        """
        INSERT INTO lpr_device_heartbeats (
            site_id,
            device_id,
            site_name,
            hostname,
            status,
            uptime,
            cpu_percent,
            memory_percent,
            disk_percent,
            temperature_c,
            lpr_service,
            camera_rtsp,
            teamviewer_status,
            public_ip,
            private_ip,
            latency_ms,
            last_plate_seen,
            last_heartbeat
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(site_id, device_id) DO UPDATE SET
            site_name = excluded.site_name,
            hostname = excluded.hostname,
            status = excluded.status,
            uptime = excluded.uptime,
            cpu_percent = excluded.cpu_percent,
            memory_percent = excluded.memory_percent,
            disk_percent = excluded.disk_percent,
            temperature_c = excluded.temperature_c,
            lpr_service = excluded.lpr_service,
            camera_rtsp = excluded.camera_rtsp,
            teamviewer_status = excluded.teamviewer_status,
            public_ip = excluded.public_ip,
            private_ip = excluded.private_ip,
            latency_ms = excluded.latency_ms,
            last_plate_seen = excluded.last_plate_seen,
            last_heartbeat = excluded.last_heartbeat
        """,
        (
            payload.get("site_id"),
            payload.get("device_id"),
            payload.get("site_name") or payload.get("site_id"),
            payload.get("hostname"),
            payload.get("status", "online"),
            payload.get("uptime"),
            payload.get("cpu_percent"),
            payload.get("memory_percent"),
            payload.get("disk_percent"),
            payload.get("temperature_c"),
            payload.get("lpr_service"),
            payload.get("camera_rtsp"),
            payload.get("teamviewer_status"),
            payload.get("public_ip"),
            payload.get("private_ip"),
            payload.get("latency_ms"),
            payload.get("last_plate_seen"),
            payload.get("last_heartbeat", now),
        ),
    )


def fetch_ops_devices():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM lpr_device_heartbeats
            ORDER BY site_name, device_id
            """
        ).fetchall()

    devices = []
    for row in rows:
        device = dict(row)
        device["health"] = classify_device_health(device)
        device["heartbeat_age_minutes"] = heartbeat_age_minutes(
            device.get("last_heartbeat")
        )
        device["coordinates"] = OPS_SITE_COORDINATES.get(
            device["site_id"],
            {"top": 50, "left": 50},
        )
        devices.append(device)

    return devices


def fetch_open_alerts():
    with get_connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, site_id, device_id, severity, message, status, created_at
                FROM lpr_alerts
                WHERE status = 'open'
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'warning' THEN 2
                        ELSE 3
                    END,
                    created_at DESC
                """
            ).fetchall()
        ]


def build_ops_summary(devices, alerts):
    health_counts = {"online": 0, "warning": 0, "offline": 0}

    for device in devices:
        health_counts[device["health"]] += 1

    cpu_values = [device["cpu_percent"] for device in devices if device["cpu_percent"]]
    average_cpu = round(sum(cpu_values) / len(cpu_values), 1) if cpu_values else 0
    last_heartbeats = [
        device["last_heartbeat"] for device in devices if device["last_heartbeat"]
    ]

    return {
        "device_count": len(devices),
        "online": health_counts["online"],
        "warning": health_counts["warning"],
        "offline": health_counts["offline"],
        "open_alerts": len(alerts),
        "average_cpu": average_cpu,
        "last_heartbeat": max(last_heartbeats) if last_heartbeats else "No heartbeats",
    }


def build_ops_sites(devices):
    sites = {}

    for device in devices:
        site = sites.setdefault(
            device["site_id"],
            {
                "site_id": device["site_id"],
                "site_name": device["site_name"] or device["site_id"],
                "devices": [],
                "coordinates": device["coordinates"],
                "health": "online",
            },
        )

        site["devices"].append(device)
        site_health_rank = {"offline": 3, "warning": 2, "online": 1}

        if site_health_rank[device["health"]] > site_health_rank[site["health"]]:
            site["health"] = device["health"]

    return sorted(sites.values(), key=lambda site: site["site_name"])


def update_random_truck():
    truck_number = random.choice(SIMULATED_TRUCKS)

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE truck_locations
            SET zone = ?,
                confidence = ?,
                camera_name = ?,
                last_seen = ?
            WHERE truck_number = ?
            """,
            (
                zone_for_truck(truck_number),
                random_confidence(),
                camera_for_truck(truck_number),
                current_timestamp(),
                truck_number,
            ),
        )


def detection_simulator():
    while True:
        update_random_truck()
        time.sleep(20)


def fetch_truck(truck_number):
    if not truck_number:
        return None

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                truck_number,
                truck_number AS plate_number,
                zone,
                confidence,
                snapshot_file,
                camera_name,
                last_seen
            FROM truck_locations
            WHERE UPPER(truck_number) = UPPER(?)
            """,
            (truck_number.strip(),),
        ).fetchone()


def fetch_all_trucks():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT truck_number, zone, confidence, snapshot_file, camera_name, last_seen
            FROM truck_locations
            ORDER BY last_seen DESC
            """
        ).fetchall()

    return [
        {
            **dict(row),
            "plate_number": row["truck_number"],
            "position": LOT_POSITIONS.get(row["truck_number"], {"top": 50, "left": 50}),
            "zone_color": zone_color_for_truck(row["truck_number"]),
        }
        for row in rows
    ]


def zone_color_for_truck(truck_number):
    position = LOT_POSITIONS.get(truck_number)

    if not position:
        return "#e26b2c"

    return LOT_ZONES[position["zone_key"]]["color"]


def build_dashboard_summary(trucks):
    confidence_values = [truck["confidence"] for truck in trucks if truck["confidence"]]
    average_confidence = (
        round(sum(confidence_values) / len(confidence_values) * 100)
        if confidence_values
        else 0
    )

    last_seen_values = [truck["last_seen"] for truck in trucks if truck["last_seen"]]
    last_update = max(last_seen_values) if last_seen_values else "No reads"

    camera_status = []
    for camera in CAMERAS:
        camera_trucks = [
            truck for truck in trucks if truck["camera_name"] == camera
        ]
        latest_read = max(
            [truck["last_seen"] for truck in camera_trucks if truck["last_seen"]],
            default="No reads",
        )

        camera_status.append(
            {
                "name": camera,
                "reads": len(camera_trucks),
                "latest_read": latest_read,
                "status": "Online",
            }
        )

    return {
        "active_trucks": len(trucks),
        "active_plates": len(trucks),
        "average_confidence": average_confidence,
        "camera_count": len(CAMERAS),
        "last_update": last_update,
        "camera_status": camera_status,
    }


@app.route("/")
def index():
    truck_query = (
        request.args.get("plate", request.args.get("truck", "")).strip()
    )
    result = fetch_truck(truck_query)
    trucks = fetch_all_trucks()
    display_trucks = [
        truck
        for truck in trucks
        if result and truck["truck_number"] == result["truck_number"]
    ]

    return render_template(
        "index.html",
        result=result,
        truck_query=truck_query,
        plate_query=truck_query,
        trucks=trucks,
        plates=trucks,
        display_trucks=display_trucks,
        display_plates=display_trucks,
        lot_zones=LOT_ZONES.values(),
        camera_locations=CAMERA_LOCATIONS,
        summary=build_dashboard_summary(trucks),
    )


@app.route("/operations")
def operations():
    devices = fetch_ops_devices()
    alerts = fetch_open_alerts()

    return render_template(
        "operations.html",
        devices=devices,
        sites=build_ops_sites(devices),
        alerts=alerts,
        summary=build_ops_summary(devices, alerts),
    )


@app.route("/api/ops/devices")
def ops_devices_api():
    devices = fetch_ops_devices()
    alerts = fetch_open_alerts()

    return jsonify(
        {
            "summary": build_ops_summary(devices, alerts),
            "sites": build_ops_sites(devices),
            "devices": devices,
            "alerts": alerts,
        }
    )


@app.route("/api/ops/heartbeat", methods=["POST"])
def ops_heartbeat_api():
    if OPS_AGENT_TOKEN and request.headers.get("X-Agent-Token") != OPS_AGENT_TOKEN:
        return jsonify({"error": "Invalid agent token."}), 401

    payload = request.get_json(silent=True) or {}
    required_fields = ["site_id", "device_id"]
    missing_fields = [field for field in required_fields if not payload.get(field)]

    if missing_fields:
        return (
            jsonify(
                {
                    "error": "Missing required heartbeat fields.",
                    "missing_fields": missing_fields,
                }
            ),
            400,
        )

    payload["last_heartbeat"] = payload.get("last_heartbeat") or current_timestamp()

    with get_connection() as conn:
        upsert_ops_device(conn, payload)

    device = payload.copy()
    device["health"] = classify_device_health(device)

    return jsonify({"status": "accepted", "device": device}), 202


def doorbell_config():
    config = Config(
        project_id=os.environ.get("GOOGLE_DEVICE_ACCESS_PROJECT_ID", DEFAULT_PROJECT_ID),
        client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID", DEFAULT_CLIENT_ID),
        client_secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", DEFAULT_CLIENT_SECRET),
        client_secret_file=os.environ.get(
            "GOOGLE_OAUTH_CLIENT_SECRET_FILE",
            DEFAULT_CLIENT_SECRET_FILE,
        ),
        refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN", DEFAULT_REFRESH_TOKEN),
        access_token=os.environ.get("GOOGLE_ACCESS_TOKEN", DEFAULT_ACCESS_TOKEN),
        timeout=float(os.environ.get("GOOGLE_SDM_TIMEOUT", "30")),
    )

    if config.client_secret_file:
        load_oauth_client_file(config)

    return config


@app.route("/doorbell")
def doorbell():
    return render_template("doorbell.html")


@app.route("/api/doorbell/webrtc", methods=["POST"])
def doorbell_webrtc():
    payload = request.get_json(silent=True) or {}
    offer_sdp = payload.get("offerSdp")

    if not offer_sdp:
        return jsonify({"error": "Missing offerSdp."}), 400

    config = doorbell_config()
    device_name = os.environ.get("GOOGLE_SDM_DEVICE", DEFAULT_DEVICE_NAME)

    if not device_name:
        return jsonify({"error": "Missing GOOGLE_SDM_DEVICE."}), 500

    device = {"name": device_name}

    try:
        access_token = refresh_access_token(config)
        response = generate_webrtc_answer(config, access_token, device, offer_sdp)
    except DoorbellError as error:
        return jsonify({"error": str(error)}), 502

    return jsonify(response.get("results", {}))


@app.route("/snapshots/<path:filename>")
def snapshots(filename):
    file_path = os.path.join(SNAPSHOT_FOLDER, filename)

    if not os.path.isfile(file_path):
        abort(404)

    return send_from_directory(SNAPSHOT_FOLDER, filename)


init_db()

if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    threading.Thread(target=detection_simulator, daemon=True).start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)
