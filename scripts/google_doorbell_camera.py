import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


SDM_SCOPE = "https://www.googleapis.com/auth/sdm.service"
DEFAULT_REDIRECT_URI = "https://www.google.com"
TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"
PCM_AUTH_BASE = "https://nestservices.google.com/partnerconnections"
SDM_API_BASE = "https://smartdevicemanagement.googleapis.com/v1"
CAMERA_LIVE_STREAM_TRAIT = "sdm.devices.traits.CameraLiveStream"

# Optional non-secret defaults. Secrets and tokens belong in .env or real
# environment variables, not source control.
DEFAULT_PROJECT_ID = ""
DEFAULT_CLIENT_ID = ""
DEFAULT_CLIENT_SECRET = ""
DEFAULT_CLIENT_SECRET_FILE = ""
DEFAULT_REFRESH_TOKEN = ""
DEFAULT_ACCESS_TOKEN = ""
DEFAULT_DEVICE_NAME = ""


@dataclass
class Config:
    project_id: str | None
    client_id: str | None
    client_secret: str | None
    client_secret_file: str | None
    refresh_token: str | None
    access_token: str | None
    timeout: float


class DoorbellError(RuntimeError):
    pass


def load_env_file(path=".env"):
    if not os.path.isfile(path):
        return

    with open(path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Connect to an authorized Google Nest doorbell/camera through the "
            "Google Smart Device Management API."
        )
    )
    parser.add_argument(
        "--project-id",
        default=os.environ.get("GOOGLE_DEVICE_ACCESS_PROJECT_ID", DEFAULT_PROJECT_ID),
        help="Device Access Project ID. Can also use GOOGLE_DEVICE_ACCESS_PROJECT_ID.",
    )
    parser.add_argument(
        "--client-id",
        default=os.environ.get("GOOGLE_OAUTH_CLIENT_ID", DEFAULT_CLIENT_ID),
        help="OAuth client ID. Can also use GOOGLE_OAUTH_CLIENT_ID.",
    )
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", DEFAULT_CLIENT_SECRET),
        help="OAuth client secret. Can also use GOOGLE_OAUTH_CLIENT_SECRET.",
    )
    parser.add_argument(
        "--client-secret-file",
        default=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET_FILE", DEFAULT_CLIENT_SECRET_FILE),
        help=(
            "Path to a downloaded Google OAuth client JSON file. Can also use "
            "GOOGLE_OAUTH_CLIENT_SECRET_FILE."
        ),
    )
    parser.add_argument(
        "--refresh-token",
        default=os.environ.get("GOOGLE_REFRESH_TOKEN", DEFAULT_REFRESH_TOKEN),
        help="OAuth refresh token. Can also use GOOGLE_REFRESH_TOKEN.",
    )
    parser.add_argument(
        "--access-token",
        default=os.environ.get("GOOGLE_ACCESS_TOKEN", DEFAULT_ACCESS_TOKEN),
        help="Short-lived OAuth access token. Can also use GOOGLE_ACCESS_TOKEN.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("GOOGLE_SDM_TIMEOUT", "30")),
        help="HTTP request timeout in seconds.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    auth_url = subparsers.add_parser(
        "auth-url",
        help="Print the Google Nest Partner Connections Manager consent URL.",
    )
    auth_url.add_argument(
        "--redirect-uri",
        default=DEFAULT_REDIRECT_URI,
        help="OAuth redirect URI registered for this client.",
    )

    exchange = subparsers.add_parser(
        "exchange-code",
        help="Exchange a PCM authorization code for access and refresh tokens.",
    )
    exchange.add_argument("--code", required=True, help="Authorization code from the redirect URL.")
    exchange.add_argument(
        "--redirect-uri",
        default=DEFAULT_REDIRECT_URI,
        help="OAuth redirect URI used for the auth URL.",
    )

    subparsers.add_parser("list-devices", help="List authorized SDM devices.")

    rtsp = subparsers.add_parser(
        "rtsp-url",
        help="Generate an RTSP stream URL for a doorbell/camera that supports RTSP.",
    )
    rtsp.add_argument(
        "--device",
        default=os.environ.get("GOOGLE_SDM_DEVICE", DEFAULT_DEVICE_NAME),
        help=(
            "Device resource name or final device ID. If omitted, the first "
            "authorized doorbell/camera with RTSP support is used."
        ),
    )
    rtsp.add_argument(
        "--open",
        action="store_true",
        help="Open the generated RTSP stream in an OpenCV preview window.",
    )
    rtsp.add_argument(
        "--raw-json",
        action="store_true",
        help="Print the full SDM command response instead of just the stream URL.",
    )

    webrtc = subparsers.add_parser(
        "webrtc-answer",
        help="Send an SDP offer and print Google's WebRTC SDP answer.",
    )
    webrtc.add_argument("--offer-file", required=True, help="Path to an SDP offer file.")
    webrtc.add_argument(
        "--device",
        default=os.environ.get("GOOGLE_SDM_DEVICE", DEFAULT_DEVICE_NAME),
        help="Device resource name or final device ID. If omitted, the first WEB_RTC device is used.",
    )

    return parser.parse_args()


def config_from_args(args):
    config = Config(
        project_id=args.project_id,
        client_id=args.client_id,
        client_secret=args.client_secret,
        client_secret_file=args.client_secret_file,
        refresh_token=args.refresh_token,
        access_token=args.access_token,
        timeout=args.timeout,
    )

    if config.client_secret_file:
        load_oauth_client_file(config)

    return config


def load_oauth_client_file(config):
    try:
        with open(config.client_secret_file, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except OSError as error:
        raise DoorbellError(f"Could not read OAuth client file: {error}") from error
    except ValueError as error:
        raise DoorbellError("OAuth client file is not valid JSON.") from error

    client = payload.get("web") or payload.get("installed")
    if not isinstance(client, dict):
        raise DoorbellError(
            "OAuth client file must contain a 'web' or 'installed' client section."
        )

    config.client_id = config.client_id or client.get("client_id")
    config.client_secret = config.client_secret or client.get("client_secret")


def require(value, label):
    if value:
        return value
    raise DoorbellError(f"Missing {label}. Pass the flag or set the matching environment variable.")


def post_form(url, data, timeout):
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    return request_json(request, timeout)


def api_get(url, access_token, timeout):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    return request_json(request, timeout)


def api_post(url, access_token, payload, timeout):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    return request_json(request, timeout)


def request_json(request, timeout):
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return parse_response_body(response.read().decode("utf-8"), response.geturl())
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        details = parse_error_body(body)
        raise DoorbellError(f"HTTP {error.code} from {error.url}\n{details}") from error
    except urllib.error.URLError as error:
        raise DoorbellError(f"Network error calling {request.full_url}: {error.reason}") from error


def parse_response_body(body, url):
    if not body:
        return {}

    try:
        return json.loads(body)
    except ValueError as error:
        raise DoorbellError(f"Expected JSON response from {url}, got:\n{body}") from error


def parse_error_body(body):
    try:
        parsed = json.loads(body)
    except ValueError:
        return body
    return json.dumps(parsed, indent=2)


def build_auth_url(config, redirect_uri):
    project_id = require(config.project_id, "Device Access Project ID")
    client_id = require(config.client_id, "OAuth client ID")
    query = urllib.parse.urlencode(
        {
            "redirect_uri": redirect_uri,
            "access_type": "offline",
            "prompt": "consent",
            "client_id": client_id,
            "response_type": "code",
            "scope": SDM_SCOPE,
        }
    )
    return f"{PCM_AUTH_BASE}/{project_id}/auth?{query}"


def exchange_code(config, code, redirect_uri):
    return post_form(
        TOKEN_URL,
        {
            "client_id": require(config.client_id, "OAuth client ID"),
            "client_secret": require(config.client_secret, "OAuth client secret"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        config.timeout,
    )


def refresh_access_token(config):
    if config.refresh_token and config.client_id and config.client_secret:
        try:
            token = post_form(
                TOKEN_URL,
                {
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "refresh_token": config.refresh_token,
                    "grant_type": "refresh_token",
                },
                config.timeout,
            )
            return token["access_token"]
        except DoorbellError:
            if not config.access_token:
                raise
            print(
                "Warning: refresh token failed; using configured access token instead.",
                file=sys.stderr,
            )
            return config.access_token

    if config.access_token:
        return config.access_token

    raise DoorbellError(
        "Missing credentials. Set GOOGLE_REFRESH_TOKEN with GOOGLE_OAUTH_CLIENT_ID "
        "and GOOGLE_OAUTH_CLIENT_SECRET, or provide GOOGLE_ACCESS_TOKEN."
    )


def list_devices(config, access_token):
    project_id = require(config.project_id, "Device Access Project ID")
    url = f"{SDM_API_BASE}/enterprises/{project_id}/devices"
    return api_get(url, access_token, config.timeout).get("devices", [])


def summarize_device(device):
    traits = device.get("traits", {})
    live_stream = traits.get(CAMERA_LIVE_STREAM_TRAIT, {})
    info = traits.get("sdm.devices.traits.Info", {})
    parent = (device.get("parentRelations") or [{}])[0]
    return {
        "name": device.get("name"),
        "type": device.get("type"),
        "customName": info.get("customName"),
        "room": parent.get("displayName"),
        "supportedProtocols": live_stream.get("supportedProtocols", []),
    }


def is_camera_device(device):
    return device.get("type") in {
        "sdm.devices.types.DOORBELL",
        "sdm.devices.types.CAMERA",
    } and CAMERA_LIVE_STREAM_TRAIT in device.get("traits", {})


def supports_protocol(device, protocol):
    live_stream = device.get("traits", {}).get(CAMERA_LIVE_STREAM_TRAIT, {})
    return protocol in live_stream.get("supportedProtocols", [])


def find_device(devices, requested, protocol):
    if requested:
        for device in devices:
            name = device.get("name", "")
            device_id = name.rsplit("/", 1)[-1]
            if requested in {name, device_id}:
                if protocol and not supports_protocol(device, protocol):
                    raise DoorbellError(
                        f"{name} does not advertise {protocol}. "
                        f"Protocols: {supported_protocols_text(device)}"
                    )
                return device
        raise DoorbellError(f"No authorized SDM device matched {requested!r}.")

    for device in devices:
        if is_camera_device(device) and (not protocol or supports_protocol(device, protocol)):
            return device

    camera_summaries = [summarize_device(device) for device in devices if is_camera_device(device)]
    raise DoorbellError(
        f"No authorized doorbell/camera advertises {protocol} support.\n"
        f"Authorized cameras: {json.dumps(camera_summaries, indent=2)}"
    )


def supported_protocols_text(device):
    protocols = summarize_device(device)["supportedProtocols"]
    return ", ".join(protocols) if protocols else "none"


def execute_command(config, access_token, device_name, command, params):
    url = f"{SDM_API_BASE}/{device_name}:executeCommand"
    return api_post(
        url,
        access_token,
        {
            "command": command,
            "params": params,
        },
        config.timeout,
    )


def generate_rtsp_stream(config, access_token, device):
    return execute_command(
        config,
        access_token,
        device["name"],
        "sdm.devices.commands.CameraLiveStream.GenerateRtspStream",
        {},
    )


def stop_rtsp_stream(config, access_token, device_name, stream_extension_token):
    return execute_command(
        config,
        access_token,
        device_name,
        "sdm.devices.commands.CameraLiveStream.StopRtspStream",
        {"streamExtensionToken": stream_extension_token},
    )


def generate_webrtc_answer(config, access_token, device, offer_sdp):
    if not offer_sdp.endswith(("\n", "\r\n")):
        offer_sdp += "\n"
    return execute_command(
        config,
        access_token,
        device["name"],
        "sdm.devices.commands.CameraLiveStream.GenerateWebRtcStream",
        {"offerSdp": offer_sdp},
    )


def open_rtsp_preview(rtsp_url):
    try:
        import cv2
    except ModuleNotFoundError as error:
        raise DoorbellError("OpenCV is required for --open. Install opencv-python.") from error

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise DoorbellError("OpenCV could not open the RTSP stream URL.")

    print("Preview open. Press q in the preview window to close it.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                time.sleep(0.2)
                continue
            cv2.imshow("Google Doorbell RTSP Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def command_auth_url(args, config):
    print(build_auth_url(config, args.redirect_uri))


def command_exchange_code(args, config):
    token = exchange_code(config, args.code, args.redirect_uri)
    print(json.dumps(token, indent=2))
    print("\nStore the refresh_token securely; do not commit it to source control.", file=sys.stderr)


def command_list_devices(config):
    access_token = refresh_access_token(config)
    devices = list_devices(config, access_token)
    print(json.dumps([summarize_device(device) for device in devices], indent=2))


def command_rtsp_url(args, config):
    access_token = refresh_access_token(config)
    devices = list_devices(config, access_token)
    device = find_device(devices, args.device, "RTSP")
    response = generate_rtsp_stream(config, access_token, device)

    if args.raw_json:
        print(json.dumps(response, indent=2))
    else:
        rtsp_url = response["results"]["streamUrls"]["rtspUrl"]
        print(rtsp_url)
        print(
            "\nThis URL is short-lived and should only be used by one client.",
            file=sys.stderr,
        )

    if args.open:
        extension_token = response["results"].get("streamExtensionToken")
        try:
            open_rtsp_preview(response["results"]["streamUrls"]["rtspUrl"])
        finally:
            if extension_token:
                stop_rtsp_stream(config, access_token, device["name"], extension_token)


def command_webrtc_answer(args, config):
    access_token = refresh_access_token(config)
    devices = list_devices(config, access_token)
    device = find_device(devices, args.device, "WEB_RTC")

    with open(args.offer_file, "r", encoding="utf-8") as file:
        offer_sdp = file.read()

    response = generate_webrtc_answer(config, access_token, device, offer_sdp)
    print(json.dumps(response, indent=2))


def main():
    load_env_file()
    args = parse_args()
    config = config_from_args(args)

    try:
        if args.command == "auth-url":
            command_auth_url(args, config)
        elif args.command == "exchange-code":
            command_exchange_code(args, config)
        elif args.command == "list-devices":
            command_list_devices(config)
        elif args.command == "rtsp-url":
            command_rtsp_url(args, config)
        elif args.command == "webrtc-answer":
            command_webrtc_answer(args, config)
        else:
            raise DoorbellError(f"Unknown command: {args.command}")
    except DoorbellError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
