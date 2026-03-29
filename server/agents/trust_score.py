"""Phase 3 placeholder for trust score logic."""


def score_to_tier(score: int) -> str:
    if score < 40:
        return "Tier 1"
    if score < 70:
        return "Tier 2"
    return "Tier 3"
