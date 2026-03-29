import json
import socket
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from dnslib import DNSRecord

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 53
UPSTREAM_DNS = "1.1.1.1"
MONITORED_CLIENT_IP = "100.73.141.11"
MAX_LOG_ENTRIES = 1000
FLUSH_INTERVAL = 1.0  # seconds between file writes

LOG_FILE = Path(__file__).resolve().parent / "logs" / "dns_log.json"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_log: deque = deque(maxlen=MAX_LOG_ENTRIES)
_dirty = threading.Event()


def _flush_loop():
    """Background thread: writes log to disk whenever new entries arrive."""
    while True:
        _dirty.wait(timeout=FLUSH_INTERVAL)
        _dirty.clear()
        snapshot = list(_log)
        try:
            LOG_FILE.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass


def _append_entry(domain: str, client_ip: str) -> None:
    _log.append({
        "domain": domain,
        "client_ip": client_ip,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _dirty.set()


def _forward(data: bytes, upstream_sock: socket.socket) -> bytes | None:
    try:
        upstream_sock.sendto(data, (UPSTREAM_DNS, 53))
        response, _ = upstream_sock.recvfrom(4096)
        return response
    except Exception:
        return None


def start_guardian():
    threading.Thread(target=_flush_loop, daemon=True).start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    upstream_sock.settimeout(1.5)

    print(f"[DNS Logger] Listening on {LISTEN_IP}:{LISTEN_PORT} — monitoring {MONITORED_CLIENT_IP}")

    while True:
        data, addr = sock.recvfrom(512)
        client_ip = addr[0]

        try:
            request = DNSRecord.parse(data)
            domain = str(request.q.qname).rstrip(".")
        except Exception:
            domain = "<parse error>"

        if client_ip == MONITORED_CLIENT_IP:
            _append_entry(domain, client_ip)

        upstream_response = _forward(data, upstream_sock)
        if upstream_response:
            sock.sendto(upstream_response, addr)
        else:
            reply = DNSRecord.parse(data).reply()
            sock.sendto(reply.pack(), addr)


if __name__ == "__main__":
    start_guardian()
