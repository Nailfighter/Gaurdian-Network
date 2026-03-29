import json
import socket
import threading
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import os
import sys

def _inject_sudo_user_site_packages() -> None:
    sudo_user = os.getenv("SUDO_USER")
    if not sudo_user:
        return

    pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
    candidate = f"/home/{sudo_user}/.local/lib/python{pyver}/site-packages"
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.append(candidate)


try:
    from dnslib import DNSRecord, RCODE
except ModuleNotFoundError:
    _inject_sudo_user_site_packages()
    from dnslib import DNSRecord, RCODE

LISTEN_IP = os.getenv("GUARDIAN_DNS_LISTEN_IP", "0.0.0.0")
LISTEN_PORT = int(os.getenv("GUARDIAN_DNS_LISTEN_PORT", "53"))
UPSTREAM_DNS = os.getenv("GUARDIAN_DNS_UPSTREAM", "1.1.1.1")
MONITORED_CLIENT_IP = os.getenv("GUARDIAN_DNS_MONITORED_CLIENT_IP", "100.73.141.11")
MAX_LOG_ENTRIES = 1000
FLUSH_INTERVAL = 1.0  # seconds between file writes

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
BLOCKLIST_REFRESH_INTERVAL = 30  # seconds

LOG_FILE = Path(__file__).resolve().parent / "logs" / "dns_log.json"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_log: deque = deque(maxlen=MAX_LOG_ENTRIES)
_dirty = threading.Event()

# Blocklist — set of domains to block (e.g. {"youtube.com", "tiktok.com"})
_blocklist: set[str] = set()
_blocklist_lock = threading.Lock()


def _normalize_domain(value: str) -> str:
    """Normalize user/supabase value to a plain lowercase hostname."""
    candidate = (value or "").strip().lower()
    if not candidate:
        return ""

    parsed = urlparse(candidate)
    if parsed.scheme:
        candidate = parsed.hostname or ""
    else:
        candidate = candidate.split("/")[0]
        candidate = candidate.split(":", 1)[0]

    candidate = candidate.rstrip(".")
    if candidate.startswith("www."):
        candidate = candidate[4:]

    return candidate


# ── Logging ──────────────────────────────────────────────────────────────────

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


def _append_entry(domain: str, client_ip: str, blocked: bool = False) -> None:
    entry = {
        "domain": domain,
        "client_ip": client_ip,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if blocked:
        entry["blocked"] = True
    _log.append(entry)
    _dirty.set()


# ── Blocklist ─────────────────────────────────────────────────────────────────

def _load_blocklist() -> set[str]:
    """Fetch active blocklist from Supabase REST API."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return set()

    url = f"{SUPABASE_URL}/rest/v1/blocklist?active=eq.true&select=domain"
    req = urllib.request.Request(
        url,
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {
                normalized
                for row in data
                if "domain" in row
                for normalized in [_normalize_domain(str(row["domain"]))]
                if normalized
            }
    except Exception as exc:
        print(f"[BlocklistSync] Failed to fetch blocklist: {exc}")
        return set()


def _blocklist_refresh_loop():
    """Background thread: refreshes blocklist from Supabase every 30 seconds."""
    global _blocklist
    while True:
        domains = _load_blocklist()
        with _blocklist_lock:
            _blocklist = domains
        print(f"[BlocklistSync] Loaded {len(domains)} blocked domain(s)")
        threading.Event().wait(timeout=BLOCKLIST_REFRESH_INTERVAL)


def _is_blocked(domain: str) -> bool:
    """Return True if domain or any parent suffix is in the blocklist."""
    normalized_domain = _normalize_domain(domain)
    if not normalized_domain:
        return False

    with _blocklist_lock:
        parts = normalized_domain.split(".")
        for i in range(len(parts) - 1):
            if ".".join(parts[i:]) in _blocklist:
                return True
        return False


# ── DNS proxy ─────────────────────────────────────────────────────────────────

def _forward(data: bytes, upstream_sock: socket.socket) -> bytes | None:
    try:
        upstream_sock.sendto(data, (UPSTREAM_DNS, 53))
        response, _ = upstream_sock.recvfrom(4096)
        return response
    except Exception:
        return None


def _nxdomain(data: bytes) -> bytes:
    reply = DNSRecord.parse(data).reply()
    reply.header.rcode = RCODE.NXDOMAIN
    return reply.pack()


def start_guardian() -> None:
    threading.Thread(target=_flush_loop, daemon=True).start()
    threading.Thread(target=_blocklist_refresh_loop, daemon=True).start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    upstream_sock.settimeout(1.5)

    print(f"[DNS Logger] Listening on {LISTEN_IP}:{LISTEN_PORT} - monitoring {MONITORED_CLIENT_IP}")

    while True:
        data, addr = sock.recvfrom(512)
        client_ip = addr[0]

        try:
            request = DNSRecord.parse(data)
            domain = str(request.q.qname).rstrip(".")
        except Exception:
            domain = "<parse error>"

        if client_ip == MONITORED_CLIENT_IP:
            if _is_blocked(domain):
                _append_entry(domain, client_ip, blocked=True)
                sock.sendto(_nxdomain(data), addr)
                continue
            _append_entry(domain, client_ip)

        upstream_response = _forward(data, upstream_sock)
        if upstream_response:
            sock.sendto(upstream_response, addr)
        else:
            sock.sendto(_nxdomain(data), addr)


if __name__ == "__main__":
    start_guardian()
