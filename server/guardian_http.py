"""
guardian_http.py — mitmproxy addon that logs full URLs from the monitored client.

Run via start_proxy.py, or directly:
    mitmdump -s guardian_http.py --listen-port 8080

Environment variables:
    GUARDIAN_HTTP_MONITORED_CLIENT_IP  — IP to monitor (default: 100.73.141.11)
    GUARDIAN_HTTP_MAX_LOG_ENTRIES      — max entries kept in memory (default: 1000)
    GUARDIAN_HTTP_FLUSH_INTERVAL       — seconds between disk writes (default: 1.0)
"""

from __future__ import annotations

import json
import os
import threading
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def _load_dotenv() -> None:
    """Load server/.env into os.environ (no external deps)."""
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

MONITORED_CLIENT_IP = os.getenv("GUARDIAN_HTTP_MONITORED_CLIENT_IP", "100.73.141.11")
MAX_LOG_ENTRIES = int(os.getenv("GUARDIAN_HTTP_MAX_LOG_ENTRIES", "1000"))
FLUSH_INTERVAL = float(os.getenv("GUARDIAN_HTTP_FLUSH_INTERVAL", "1.0"))
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
BLOCKLIST_REFRESH_INTERVAL = int(os.getenv("GUARDIAN_HTTP_BLOCKLIST_REFRESH_INTERVAL", "30"))

LOG_FILE = Path(__file__).resolve().parent / "logs" / "http_log.json"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_log: deque = deque(maxlen=MAX_LOG_ENTRIES)
_dirty = threading.Event()
_flush_started = False
_lock = threading.Lock()
_blocklist: set[str] = set()
_blocklist_lock = threading.Lock()


def _normalize_domain(value: str) -> str:
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


def _load_blocklist() -> set[str]:
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
        print(f"[GuardianHTTP] Blocklist fetch failed: {exc}")
        return set()


def _blocklist_refresh_loop() -> None:
    while True:
        domains = _load_blocklist()
        with _blocklist_lock:
            _blocklist.clear()
            _blocklist.update(domains)
        threading.Event().wait(timeout=BLOCKLIST_REFRESH_INTERVAL)


def _is_blocked(domain: str) -> bool:
    normalized_domain = _normalize_domain(domain)
    if not normalized_domain:
        return False

    with _blocklist_lock:
        parts = normalized_domain.split(".")
        for i in range(len(parts) - 1):
            if ".".join(parts[i:]) in _blocklist:
                return True
    return False


def _flush_loop() -> None:
    while True:
        _dirty.wait(timeout=FLUSH_INTERVAL)
        _dirty.clear()
        snapshot = list(_log)
        try:
            LOG_FILE.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass


def _ensure_flush_thread() -> None:
    global _flush_started
    with _lock:
        if not _flush_started:
            threading.Thread(target=_flush_loop, daemon=True).start()
            threading.Thread(target=_blocklist_refresh_loop, daemon=True).start()
            _flush_started = True


def _append_entry(url: str, domain: str, method: str, client_ip: str) -> None:
    _log.append({
        "url": url,
        "domain": domain,
        "method": method,
        "client_ip": client_ip,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _dirty.set()


class GuardianHTTPAddon:
    """mitmproxy addon: logs full request URLs for the monitored client IP."""

    def __init__(self) -> None:
        _ensure_flush_thread()

    def request(self, flow) -> None:
        from mitmproxy import http

        client_ip = flow.client_conn.peername[0] if flow.client_conn.peername else ""
        if client_ip != MONITORED_CLIENT_IP:
            return

        url = flow.request.pretty_url
        method = flow.request.method
        domain = urlparse(url).hostname or flow.request.host

        if _is_blocked(domain):
            flow.response = http.Response.make(
                403,
                b"Blocked by Guardian Network",
                {"Content-Type": "text/plain"},
            )

        _append_entry(url, domain, method, client_ip)


addons = [GuardianHTTPAddon()]
