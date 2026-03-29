from __future__ import annotations

from typing import Dict


def attach_device_context(payload: Dict, default_device_id: str = "demo-device-1") -> Dict:
    cloned = dict(payload)
    cloned.setdefault("device_id", default_device_id)
    return cloned
