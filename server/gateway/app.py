from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parents[1]
DNS_LOG_FILE = BASE_DIR / "logs" / "dns_log.json"

app = FastAPI(title="Guardian DNS Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("gateway.app:app", host="0.0.0.0", port=8001, reload=False)
