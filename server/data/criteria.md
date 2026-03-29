# Static Reasoning Criteria

## Inputs
- URL
- User age
- Request context
- Timestamp

## Scoring Flow
1. Keyword analysis
- Start at score 50.
- Increase score for explicit risk keywords and known blocked domains.
- Increase score for soft-risk/social/distraction markers.
- Decrease score for educational indicators.

2. Context check
- Decrease score for school intent like homework, assignment, study, research.
- Decrease score for supervised access context.
- Increase score for low-intent browsing hints.

3. Final mapping
- Clamp to 0-100.
- Risk levels: LOW (0-39), MEDIUM (40-69), HIGH (70-100).

## Guardrails
- Explicit-risk keywords are weighted stronger than educational signals.
- Block-list domains strongly increase score regardless of context.
