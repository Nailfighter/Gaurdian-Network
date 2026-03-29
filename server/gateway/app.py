from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from agents.reasoning_engine import evaluate_request


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_FILE = BASE_DIR / "logs" / "reasoning_log.json"
DEVICES_FILE = BASE_DIR / "data" / "devices.json"


def _load_dotenv(env_path: Path) -> None:
	if not env_path.exists():
		return

	for raw_line in env_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, value = line.split("=", 1)
		os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")

DEFAULT_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("BACKEND_PORT", "8001"))

app = FastAPI(title="Guardian Network Gateway", version="0.1.0")


@app.get("/test")
def test_endpoint() -> Dict[str, str]:
	return {
		"status": "ok",
		"message": "Guardian backend reachable",
		"timestamp": datetime.now(timezone.utc).isoformat(),
	}


class RequestPayload(BaseModel):
	url: str = Field(..., min_length=3)
	user_age: int = Field(..., ge=3, le=99)
	request_context: str = ""
	device_id: str = "demo-device-1"
	timestamp: Optional[str] = None


class DecisionPayload(BaseModel):
	action: Literal["approve", "deny"]


RECENT_DECISIONS: List[Dict[str, Any]] = []


def _ensure_json_file(path: Path, default: Any) -> None:
	if not path.exists():
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(json.dumps(default, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
	_ensure_json_file(path, default)
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2)
		handle.write("\n")


def _decision_verdict(score: int) -> str:
	if score >= 70:
		return "BLOCK"
	if score >= 40:
		return "PAUSED"
	return "ALLOW"


def _tier_from_score(score: int) -> str:
	if score < 40:
		return "Tier 1"
	if score < 70:
		return "Tier 2"
	return "Tier 3"


def _append_log(entry: Dict[str, Any]) -> None:
	logs = _read_json(LOG_FILE, [])
	logs.append(entry)
	_write_json(LOG_FILE, logs)


def _to_parent_shape(record: Dict[str, Any]) -> Dict[str, Any]:
	# Parent dashboard currently keys on `id` and `decision_score`.
	return {
		"id": record["decision_id"],
		"decision_id": record["decision_id"],
		"device_id": record["device_id"],
		"url": record["url"],
		"decision_score": record["score"],
		"score": record["score"],
		"reason_text": record["reason_text"],
		"risk_level": record["risk_level"],
		"verdict": record["verdict"],
		"timestamp": record["timestamp"],
		"parent_action": record.get("parent_action"),
	}


@app.post("/request")
def create_request(payload: RequestPayload) -> Dict[str, Any]:
	evaluated = evaluate_request(
		url=payload.url,
		user_age=payload.user_age,
		request_context=payload.request_context,
		timestamp=payload.timestamp or datetime.now(timezone.utc).isoformat(),
	)

	decision_id = str(uuid4())
	record = {
		"decision_id": decision_id,
		"device_id": payload.device_id,
		"url": payload.url,
		"score": int(evaluated["decision_score"]),
		"reason_text": evaluated["reason_text"],
		"risk_level": evaluated["risk_level"],
		"verdict": _decision_verdict(int(evaluated["decision_score"])),
		"timestamp": evaluated.get("evaluated_at", payload.timestamp),
		"parent_action": None,
	}

	RECENT_DECISIONS.append(record)
	RECENT_DECISIONS[:] = RECENT_DECISIONS[-200:]
	_append_log(record)
	return _to_parent_shape(record)


@app.get("/requests")
def list_requests() -> Dict[str, Any]:
	# Keep both keys for compatibility during integration.
	items = [_to_parent_shape(item) for item in RECENT_DECISIONS]
	return {"count": len(items), "requests": items, "items": items}


@app.post("/decision/{decision_id}")
def update_parent_decision(decision_id: str, payload: DecisionPayload) -> Dict[str, Any]:
	found = None
	for item in RECENT_DECISIONS:
		if item["decision_id"] == decision_id:
			item["parent_action"] = payload.action.upper()
			item["verdict"] = "ALLOW" if payload.action == "approve" else "BLOCK"
			found = item
			break

	if not found:
		raise HTTPException(status_code=404, detail="Decision id not found")

	logs = _read_json(LOG_FILE, [])
	for item in logs:
		if item.get("decision_id") == decision_id:
			item["parent_action"] = payload.action.upper()
			item["verdict"] = "ALLOW" if payload.action == "approve" else "BLOCK"
			break
	_write_json(LOG_FILE, logs)

	return _to_parent_shape(found)


@app.get("/logs")
def get_logs(n: int = Query(default=50, ge=1, le=1000)) -> Dict[str, Any]:
	logs = _read_json(LOG_FILE, [])
	sliced = logs[-n:]
	return {"count": len(sliced), "items": sliced}


@app.get("/trust/{device_id}")
def get_trust(device_id: str) -> Dict[str, Any]:
	devices_blob = _read_json(DEVICES_FILE, {"devices": []})
	devices = devices_blob.get("devices", [])

	for device in devices:
		if device.get("device_id") == device_id:
			score = int(device.get("trust_score", 50))
			return {"device_id": device_id, "score": score, "tier": _tier_from_score(score)}

	score = 50
	return {"device_id": device_id, "score": score, "tier": _tier_from_score(score)}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("gateway.app:app", host=DEFAULT_HOST, port=DEFAULT_PORT, reload=False)
