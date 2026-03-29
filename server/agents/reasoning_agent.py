"""Phase 2 placeholder for reasoning agent wrapper."""

from agents.reasoning_engine import evaluate_request


def run(payload):
    return evaluate_request(
        url=payload["url"],
        user_age=payload["user_age"],
        request_context=payload.get("request_context", ""),
        timestamp=payload.get("timestamp"),
    )
