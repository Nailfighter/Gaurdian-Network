# Server Agent Tasks

**Branch:** `server`
**Folder:** `server/`
**Stack:** Python 3.9+ · Flask or FastAPI · JSON storage · pytest

You own the backend. Do not edit `client/` or `parent/`.

---

## Folder Layout (create this)

```
server/
├── agents/
│   ├── reasoning_engine.py
│   ├── gatekeeper.py
│   ├── reasoning_agent.py
│   ├── negotiation_agent.py
│   ├── coordinator.py
│   └── trust_score.py
├── gateway/
│   ├── app.py            # Flask/FastAPI entry point
│   └── network_emulator.py
├── data/
│   ├── urls.json         # 30-URL test dataset
│   ├── criteria.md       # reasoning criteria docs
│   ├── family_policy.json
│   └── devices.json
├── logs/
│   └── reasoning_log.json
└── tests/
    ├── test_reasoning.py
    └── test_integration.py
```

---

## Phase 1 Tasks

### 1.1 Project Setup & Data Prep
- [ ] Scaffold `server/` folder layout above
- [ ] Create `server/data/urls.json` — 30 URLs labelled `Educational`, `Harmful`, or `Borderline`
  - Include edge cases: `biology.edu/explosives`, `instagram.com`, `wikipedia.org/chemistry`
- [ ] Write `server/data/criteria.md` — document scoring criteria (age, intent, keywords, educational value)

### 1.2 Static Reasoning Engine
- [ ] Build `server/agents/reasoning_engine.py`
  - Input: `url`, `user_age`, `request_context`, `timestamp`
  - Output: `{ decision_score: 0-100, reason_text: str, risk_level: "LOW"|"MEDIUM"|"HIGH" }`
  - Chain-of-thought logic: keyword analysis → context check → final score
  - Guardrails: explicit keyword filter, domain block-list
- [ ] Expose via `server/gateway/app.py`:
  - `POST /request` → run engine → return decision JSON
  - `GET /requests` → list recent decisions
  - `POST /decision/<id>` → parent approve/deny
  - `GET /logs` → stream reasoning log
  - `GET /trust/<device_id>` → return trust score
- [ ] Write `server/tests/test_reasoning.py` — unit tests on 30-URL dataset; target **70%+ accuracy on Borderline**

---

## Phase 2 Tasks

### 2.1 Multi-Agent Framework
- [ ] **Gatekeeper** (`server/agents/gatekeeper.py`): parse incoming request into structured context dict `{ url, user_age, timestamp, device_id, history }`
- [ ] **Reasoning Agent** (`server/agents/reasoning_agent.py`): wrap Phase 1 engine; append `reasoning_log` trace to each decision
- [ ] **Negotiation Agent** (`server/agents/negotiation_agent.py`): if `decision_score` 40-60, generate conditions string (e.g. "Allow with 30-min time limit, supervised")
- [ ] **Coordinator** (`server/agents/coordinator.py`): route request through Gatekeeper → Reasoning Agent → Negotiation Agent (if PAUSED)

### 2.2 Decision Logging
- [ ] Append every decision to `server/logs/reasoning_log.json`
  - Fields: `decision_id`, `device_id`, `url`, `score`, `reason_text`, `agent_trace`, `verdict`, `timestamp`
- [ ] `GET /logs` endpoint returns last N entries (query param `?n=50`)

### 2.3 Family Policy
- [ ] Create `server/data/family_policy.json` — parent-defined rules:
  ```json
  { "rules": [
      { "pattern": "physics.*", "action": "always_allow" },
      { "pattern": "social_media", "action": "block", "hours": "08:00-15:00" }
  ]}
  ```
- [ ] Coordinator applies policy before calling Reasoning Agent
- [ ] Negotiation Agent lowers threshold when parent repeatedly approves same pattern (store frequency in `devices.json`)

### 2.4 Device Enrolment & Network Emulator
- [ ] `server/data/devices.json` — `{ device_id, user_age, name }`
- [ ] `server/gateway/network_emulator.py` — fake traffic interception: wrap incoming requests with `device_id` lookup
- [ ] `POST /enrol` endpoint — register a new device

---

## Phase 3 Tasks

### 3.1 Incentive Agent & Trust Score
- [ ] Build `server/agents/trust_score.py` — per-device score (0-100) persisted in `devices.json`
  - +3: child reads explanation (client sends `dwell_time > 5s` flag)
  - +5: accepts terms without dispute
  - +2: follows time-limited approval
  - -5: repeated bypass attempts
- [ ] Three tiers:
  - Tier 1 (0-39): Strict — more parent confirmations required
  - Tier 2 (40-69): Balanced — allow borderline with explanation
  - Tier 3 (70-100): High-trust — fewer blocks, faster approvals
- [ ] `GET /trust/<device_id>` returns `{ score, tier }`

### 3.2 Dynamic Policy Adaptation
- [ ] Coordinator fetches Trust Tier before calling Reasoning Agent
- [ ] Pass tier into reasoning engine to adjust decision threshold:
  - Tier 1: threshold 30 (stricter)
  - Tier 2: threshold 50 (default)
  - Tier 3: threshold 70 (more permissive)

### 3.3 Test Dataset Expansion
- [ ] Expand `server/data/urls.json` to 100 URLs
- [ ] Add accuracy benchmark script `server/tests/test_accuracy.py` — report % correct per category
- [ ] Target: **80%+ on Borderline**

### 3.4 Real Network Layer (optional — if time permits)
- [ ] Set up WireGuard or Tailscale config scripts in `server/gateway/`
- [ ] Route DNS/HTTP through gateway; intercept real URLs
- [ ] Test with 2 physical or VM devices

---

## Success Targets

| Phase | Accuracy | Latency |
|-------|----------|---------|
| 1 | 70%+ Borderline | < 500ms |
| 2 | 75%+ Borderline | < 500ms |
| 3 | 80%+ Borderline | < 500ms |
