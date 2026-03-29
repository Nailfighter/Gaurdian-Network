import json
import socket
from datetime import datetime, timezone
from pathlib import Path

from dnslib import DNSRecord

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 53
UPSTREAM_DNS = "1.1.1.1"
LOG_FILE = Path(__file__).resolve().parent / "logs" / "dns_log.json"
DEVICES_FILE = Path(__file__).resolve().parent / "data" / "devices.json"
MAX_LOG_ENTRIES = 1000


def _load_devices() -> list[dict]:
    if not DEVICES_FILE.exists():
        return []
    try:
        raw = json.loads(DEVICES_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(raw, dict):
        devices = raw.get("devices", [])
    elif isinstance(raw, list):
        devices = raw
    else:
        devices = []

    return [item for item in devices if isinstance(item, dict)]


def _resolve_device(client_ip: str) -> tuple[str, str]:
    for device in _load_devices():
        known_ip = (
            device.get("ip")
            or device.get("client_ip")
            or device.get("tailscale_ip")
            or device.get("address")
        )
        if known_ip == client_ip:
            return (
                str(device.get("device_id", "unknown-device")),
                str(device.get("name", "Unknown Device")),
            )
    return ("unknown-device", "Unknown Device")


def _append_entry(domain: str, client_ip: str, device_id: str, device_name: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        entries = json.loads(LOG_FILE.read_text(encoding="utf-8")) if LOG_FILE.exists() else []
    except (json.JSONDecodeError, OSError):
        entries = []

    entries.append({
        "domain": domain,
        "client_ip": client_ip,
        "device_id": device_id,
        "device_name": device_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    entries = entries[-MAX_LOG_ENTRIES:]
    LOG_FILE.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def _forward(data: bytes) -> bytes | None:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.sendto(data, (UPSTREAM_DNS, 53))
        response, _ = sock.recvfrom(4096)
        sock.close()
        return response
    except Exception:
        return None


def start_guardian():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    print(f"[DNS Logger] Listening on {LISTEN_IP}:{LISTEN_PORT} — logging all queries")

    while True:
        data, addr = sock.recvfrom(512)
        client_ip = addr[0]
        try:
            request = DNSRecord.parse(data)
            domain = str(request.q.qname).rstrip(".")
        except Exception:
            domain = "<parse error>"

        device_id, device_name = _resolve_device(client_ip)
        _append_entry(domain, client_ip, device_id, device_name)
        print(f"[DNS] {device_name} ({device_id} | {client_ip}) -> {domain}")

        upstream_response = _forward(data)
        if upstream_response:
            sock.sendto(upstream_response, addr)
        else:
            reply = DNSRecord.parse(data).reply()
            sock.sendto(reply.pack(), addr)


if __name__ == "__main__":
    start_guardian()
