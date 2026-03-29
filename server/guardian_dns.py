import json
import socket
from datetime import datetime, timezone
from pathlib import Path

from dnslib import DNSRecord

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 53
UPSTREAM_DNS = "1.1.1.1"
MONITORED_CLIENT_IP = "100.73.141.11"
LOG_FILE = Path(__file__).resolve().parent / "logs" / "dns_log.json"
MAX_LOG_ENTRIES = 1000


def _append_entry(domain: str, client_ip: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        entries = json.loads(LOG_FILE.read_text(encoding="utf-8")) if LOG_FILE.exists() else []
    except (json.JSONDecodeError, OSError):
        entries = []

    entries.append({
        "domain": domain,
        "client_ip": client_ip,
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
    print(
        f"[DNS Logger] Listening on {LISTEN_IP}:{LISTEN_PORT} — "
        f"logging only {MONITORED_CLIENT_IP}"
    )

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

        upstream_response = _forward(data)
        if upstream_response:
            sock.sendto(upstream_response, addr)
        else:
            reply = DNSRecord.parse(data).reply()
            sock.sendto(reply.pack(), addr)


if __name__ == "__main__":
    start_guardian()
