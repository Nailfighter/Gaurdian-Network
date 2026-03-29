from __future__ import annotations

import json
import os
import sys
import threading
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

def _load_dotenv() -> None:
    """Load server/.env into os.environ (no external deps)."""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

_load_dotenv()


def _inject_sudo_user_site_packages() -> None:
    sudo_user = os.getenv("SUDO_USER")
    if not sudo_user:
        return

    pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
    candidate = f"/home/{sudo_user}/.local/lib/python{pyver}/site-packages"
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.append(candidate)


try:
    from fastapi import FastAPI, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ModuleNotFoundError:
    _inject_sudo_user_site_packages()
    from fastapi import FastAPI, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
from guardian_dns import start_guardian

BASE_DIR = Path(__file__).resolve().parents[1]
DNS_LOG_FILE = BASE_DIR / "logs" / "dns_log.json"
HTTP_LOG_FILE = BASE_DIR / "logs" / "http_log.json"
HTTP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_http_log: deque = deque(maxlen=1000)
_http_dirty = threading.Event()


def _http_flush_loop() -> None:
    while True:
        _http_dirty.wait(timeout=1.0)
        _http_dirty.clear()
        snapshot = list(_http_log)
        try:
            HTTP_LOG_FILE.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass


threading.Thread(target=_http_flush_loop, daemon=True).start()

app = FastAPI(title="Guardian DNS Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def _supa_headers() -> dict:
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _supa_request(method: str, path: str, body: bytes | None = None) -> Any:
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}",
        data=body,
        headers=_supa_headers(),
        method=method,
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


@app.on_event("startup")
def start_dns_service() -> None:
    # Run DNS proxy/logger in the background when the API starts.
    def _run() -> None:
        try:
            start_guardian()
        except Exception as exc:
            print(f"[GuardianDNS] Failed to start DNS service: {exc}")

    threading.Thread(target=_run, daemon=True).start()

    # Optionally start the HTTP proxy (set GUARDIAN_HTTP_PROXY_ENABLED=true to enable).
    if os.getenv("GUARDIAN_HTTP_PROXY_ENABLED", "false").lower() == "true":
        import asyncio
        import sys
        sys.path.insert(0, str(BASE_DIR))

        async def _run_proxy() -> None:
            try:
                from mitmproxy.options import Options
                from mitmproxy.tools.dump import DumpMaster
                from guardian_http import GuardianHTTPAddon
            except ImportError:
                print("[GuardianHTTP] mitmproxy not installed — HTTP proxy disabled")
                return

            listen_port = int(os.getenv("GUARDIAN_HTTP_LISTEN_PORT", "8080"))
            opts = Options(listen_host="0.0.0.0", listen_port=listen_port)
            master = DumpMaster(opts, with_termlog=False, with_dumper=False)
            master.addons.add(GuardianHTTPAddon())
            print(f"[GuardianHTTP] Proxy listening on 0.0.0.0:{listen_port}")
            await master.run()

        def _proxy_thread() -> None:
            asyncio.run(_run_proxy())

        threading.Thread(target=_proxy_thread, daemon=True).start()


def _read_dns_log() -> list[dict[str, Any]]:
    if not DNS_LOG_FILE.exists():
        return []

    try:
        raw = json.loads(DNS_LOG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    return [entry for entry in raw if isinstance(entry, dict)]


@app.get("/test")
def test_endpoint() -> Dict[str, str]:
    return {
        "status": "ok",
        "message": "Guardian backend reachable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/dns-log")
def get_dns_log(n: int = Query(default=100, ge=1, le=1000)) -> Dict[str, Any]:
    entries = _read_dns_log()
    sliced = entries[-n:]
    sliced.reverse()
    return {"count": len(sliced), "entries": sliced}


class UrlEntry(BaseModel):
    url: str
    domain: Optional[str] = None
    method: Optional[str] = "GET"
    timestamp: Optional[str] = None


@app.post("/url-log")
def post_url_log(entry: UrlEntry, request: Request) -> Dict[str, str]:
    domain = entry.domain or urlparse(entry.url).hostname or ""
    _http_log.append({
        "url": entry.url,
        "domain": domain,
        "method": entry.method or "GET",
        "client_ip": request.client.host if request.client else "unknown",
        "timestamp": entry.timestamp or datetime.now(timezone.utc).isoformat(),
    })
    _http_dirty.set()
    return {"status": "ok"}


@app.get("/url-log")
def get_url_log(n: int = Query(default=100, ge=1, le=1000)) -> Dict[str, Any]:
    entries = list(_http_log)
    sliced = entries[-n:]
    sliced.reverse()
    return {"count": len(sliced), "entries": sliced}


class BlocklistEntry(BaseModel):
    domain: str


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


@app.get("/blocklist")
def get_blocklist() -> Dict[str, Any]:
    try:
        rows = _supa_request("GET", "blocklist?select=id,domain,active,created_at&order=created_at.desc")
        return {"count": len(rows), "entries": rows}
    except Exception as exc:
        return {"error": str(exc), "entries": []}


@app.post("/blocklist")
def add_to_blocklist(entry: BlocklistEntry) -> Dict[str, Any]:
    domain = _normalize_domain(entry.domain)
    if not domain:
        return {"error": "Invalid domain"}

    body = json.dumps({"domain": domain, "active": True}).encode()
    try:
        rows = _supa_request("POST", "blocklist", body=body)
        return {"status": "ok", "entry": rows[0] if rows else {}}
    except Exception as exc:
        return {"error": str(exc)}


@app.delete("/blocklist/{domain}")
def remove_from_blocklist(domain: str) -> Dict[str, str]:
    normalized = _normalize_domain(domain)
    if not normalized:
        return {"error": "Invalid domain"}

    body = json.dumps({"active": False}).encode()
    try:
        _supa_request("PATCH", f"blocklist?domain=eq.{normalized}", body=body)
        return {"status": "ok"}
    except Exception as exc:
        return {"error": str(exc)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("gateway.app:app", host="0.0.0.0", port=8001, reload=False)
