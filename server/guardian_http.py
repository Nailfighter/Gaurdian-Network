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
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MONITORED_CLIENT_IP = os.getenv("GUARDIAN_HTTP_MONITORED_CLIENT_IP", "100.73.141.11")
MAX_LOG_ENTRIES = int(os.getenv("GUARDIAN_HTTP_MAX_LOG_ENTRIES", "1000"))
FLUSH_INTERVAL = float(os.getenv("GUARDIAN_HTTP_FLUSH_INTERVAL", "1.0"))

LOG_FILE = Path(__file__).resolve().parent / "logs" / "http_log.json"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_log: deque = deque(maxlen=MAX_LOG_ENTRIES)
_dirty = threading.Event()
_flush_started = False
_lock = threading.Lock()


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
        client_ip = flow.client_conn.peername[0] if flow.client_conn.peername else ""
        if client_ip != MONITORED_CLIENT_IP:
            return

        url = flow.request.pretty_url
        method = flow.request.method
        domain = urlparse(url).hostname or flow.request.host
        _append_entry(url, domain, method, client_ip)


addons = [GuardianHTTPAddon()]
