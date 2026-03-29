from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from urllib.parse import urlparse


BLOCKED_DOMAINS = {
    "dark-web.example",
    "malware-downloads.example",
    "illegal-market.example",
    "adult-content.example",
}

EXPLICIT_RISK_KEYWORDS = {
    "explosive",
    "explosives",
    "bomb",
    "weapon",
    "drugs",
    "meth",
    "suicide",
    "self-harm",
    "porn",
    "gambling",
    "bypass",
    "hack",
}

SOFT_RISK_KEYWORDS = {
    "social",
    "stream",
    "video",
    "chat",
    "forum",
    "gaming",
    "reels",
    "reddit",
    "instagram",
    "tiktok",
    "discord",
    "youtube",
}

EDUCATIONAL_KEYWORDS = {
    "wikipedia",
    "edu",
    "academy",
    "course",
    "tutorial",
    "science",
    "biology",
    "chemistry",
    "math",
    "history",
    "nasa",
    "coursera",
    "code",
}

EDUCATIONAL_CONTEXT_HINTS = {
    "homework",
    "assignment",
    "school",
    "project",
    "study",
    "research",
}


def _normalize_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://{url}"


def _extract_domain_and_path(url: str) -> tuple[str, str]:
    parsed = urlparse(_normalize_url(url))
    domain = (parsed.netloc or "").lower().strip()
    path = (parsed.path or "").lower().strip()
    return domain, path


def _risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def evaluate_request(
    url: str,
    user_age: int,
    request_context: str,
    timestamp: str | None = None,
) -> Dict[str, str | int]:
    """Evaluate a URL request using a static reasoning pipeline."""
    if not timestamp:
        timestamp = datetime.utcnow().isoformat()

    domain, path = _extract_domain_and_path(url)
    context = (request_context or "").lower()
    combined_text = f"{domain} {path}".lower()

    score = 50
    reasons: List[str] = []

    if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in BLOCKED_DOMAINS):
        score = 95
        reasons.append("Domain appears in explicit block-list")

    explicit_hits = [k for k in EXPLICIT_RISK_KEYWORDS if k in combined_text]
    soft_hits = [k for k in SOFT_RISK_KEYWORDS if k in combined_text]
    edu_hits = [k for k in EDUCATIONAL_KEYWORDS if k in combined_text]

    if explicit_hits:
        score += min(40, 18 * len(explicit_hits))
        reasons.append(f"Explicit risk keywords detected: {', '.join(sorted(explicit_hits))}")

    if soft_hits:
        score += min(16, 4 * len(soft_hits))
        reasons.append(f"Potentially distracting content markers: {', '.join(sorted(soft_hits))}")

    if edu_hits:
        score -= min(20, 5 * len(edu_hits))
        reasons.append(f"Educational indicators found: {', '.join(sorted(edu_hits))}")

    if any(hint in context for hint in EDUCATIONAL_CONTEXT_HINTS):
        score -= 12
        reasons.append("Request context suggests educational intent")

    if "supervised" in context or "with parent" in context:
        score -= 8
        reasons.append("Supervised access context lowers risk")

    if any(token in context for token in ["late night", "bored", "no reason", "just browsing"]):
        score += 10
        reasons.append("Context indicates low-intent browsing")

    if user_age <= 12:
        score += 6
        reasons.append("Younger user age raises safety sensitivity")
    elif user_age <= 15:
        score += 3

    score = max(0, min(100, score))

    if not reasons:
        reasons.append("No notable safety indicators found")

    return {
        "decision_score": score,
        "reason_text": " | ".join(reasons),
        "risk_level": _risk_level(score),
        "evaluated_at": timestamp,
    }
