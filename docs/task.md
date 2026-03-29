# Guardian Core: Incremental Build Plan

**Goal:** Build trust-enabling parental control with multi-agent reasoning, incrementally toward Phase 1 PDR targets.
**Timeline:** Week 1 Hackathon Sprint
**Approach:** 3 MVPs + 3 Phases, each building on prior work.

---

## MVP Progression Strategy

Each MVP is **showable independently**. If one phase stalls, you have a working demo.

- **MVP 1 (Foundational):** Static reasoning engine + simple UI
- **MVP 2 (Core):** Multi-agent orchestration + network foundation
- **MVP 3 (Full):** Incentive Agent + Reasoning Logs + Multi-device setup

---

## Phase 1: Foundational MVP (Days 1-2)

### Goal
Prove the reasoning concept works. Static decision-maker that evaluates URLs contextually.

### Tasks

#### 1.1 Project Setup & Data Prep
- [ ] Initialize repo structure: `/agents`, `/ui`, `/gateway`, `/tests`, `/data`
- [ ] Create test dataset: 30 URLs labeled "Educational," "Harmful," "Borderline"
  - Examples: biology.edu/explosives, instagram.com, wikipedia.org/chemistry
- [ ] Document reasoning criteria (age, intent, keywords, educational value)
- [ ] **Claude Code:** Use VS Code to scaffold project; write test data as JSON

#### 1.2 Static Reasoning Engine
- [ ] Build `reasoning_engine.py`: LLM-free rule-based classifier
  - Input: URL, user_age, request_context, timestamp
  - Output: decision_score (0-100), reason_text, risk_level
  - Use chain-of-thought logic (keyword analysis → context check → final score)
- [ ] Implement basic guardrails (explicit keyword filters, domain classification)
- [ ] Test on 30-URL dataset; target 70%+ accuracy on "Borderline" classification
- [ ] **Claude Code:** Write and test reasoning_engine.py with unit tests

#### 1.3 Minimal Child UI (CLI or Web)
- [ ] Build simple request interface: "Child wants access to [URL]"
- [ ] Display: Decision (ALLOW/BLOCK/PAUSED), Score (0-100), Plain-English reason
- [ ] Add "Request Override" button (logs request, displays parent notification prompt)
- [ ] **Claude Code:** Use Flask or FastAPI + HTML template for web UI

#### 1.4 Minimal Parent UI (Dashboard)
- [ ] Single page showing: recent child requests, decision log, override buttons
- [ ] Display reasoning for each request (score + rationale)
- [ ] One-tap approval/denial for pending requests
- [ ] **Claude Code:** Add to same Flask app; use Jinja2 templates

#### 1.5 Integration & Testing
- [ ] Wire child UI → reasoning engine → parent UI
- [ ] Manual test flow: child requests site → reason displayed → parent approves/denies
- [ ] Measure request latency (target: < 500ms)
- [ ] **Claude Code:** Write integration tests; demo flow end-to-end

### Deliverable
**Working demo:** Child UI → Reasoning Engine → Parent UI. Request latency <500ms. 70%+ accuracy on test URLs.

---

## Phase 2: Core MVP (Days 2-3)

### Goal
Add multi-agent orchestration and network foundation. Reason becomes "learned" over family preferences.

### Tasks

#### 2.1 Multi-Agent Framework (3 agents)
- [ ] **Gatekeeper Agent:** Extracts request context (URL, time, user_age, historical pattern)
  - Build as simple dict/JSON handler; no complex orchestration yet
- [ ] **Reasoning Agent:** Calls reasoning engine + logs decision rationale
  - Wraps Phase 1 engine; adds reasoning_log output
- [ ] **Negotiation Agent:** For PAUSED requests, generates explanation text
  - Rule-based: if risk_score 40-60, suggest conditions (time limits, supervised access)
- [ ] Build agent coordinator (simple queue or state machine)
- [ ] **Claude Code:** Modularize Phase 1 code; create agent classes in separate files

#### 2.2 Decision Logging & Reasoning Logs
- [ ] Store every decision in `/logs/reasoning_log.json`: decision_id, request, score, reason, agent_trace
- [ ] Build terminal-style log viewer: scrollable list of decisions with reasoning details
- [ ] Each log entry: request_id, semantic_risk, educational_relevance, policy_rule, verdict
- [ ] **Claude Code:** Add logging to reasoning_engine; build log UI component

#### 2.3 Family Policy Customization
- [ ] Allow parent to define per-family rules: "Physics sites always allow," "Social media blocks during school hours"
- [ ] Agents adapt decision thresholds based on rules
- [ ] Negotiation agent learns: if parent always approves "chemistry" + "educational," lower future threshold
- [ ] **Claude Code:** Add policy JSON file; modify agents to apply rules before deciding

#### 2.4 Simple Mesh Network Foundation (Single Device Emulation)
- [ ] Build mock network layer: emulate device traffic interception (no real WireGuard yet)
- [ ] Device enrolls to "family network" (just stores device ID + user_age)
- [ ] Each device request routed through gateway (simulated; single machine for now)
- [ ] **Claude Code:** Add network emulation module; test with multiple device IDs

#### 2.5 Multi-Device Support (Emulation)
- [ ] Extend parent UI: show requests from multiple children/devices
- [ ] Reasoning engine personalizes by device (e.g., 10-year-old vs. 14-year-old gets different thresholds)
- [ ] **Claude Code:** Add device table to DB; extend parent dashboard

### Deliverable
**Core demo:** Multi-agent system + terminal reasoning logs + family policy rules + multi-device emulation. 75%+ accuracy on borderline classification.

---

## Phase 3: Full MVP (Days 3-4)

### Goal
Add Incentive Agent + trust-aware policies. Optionally add real network foundation.

### Tasks

#### 3.1 Incentive Agent & Trust Score System
- [ ] Build Trust Score tracker (per child, 0-100)
- [ ] Scoring rules:
  - +3 points: Child reads explanation (dwell time > 5s)
  - +5 points: Accepts terms without dispute
  - +2 points: Follows time-limited approval
  - -5 points: Repeated bypass attempts
- [ ] Three policy tiers based on score:
  - Tier 1 (0-39): Strict (more parent confirmations)
  - Tier 2 (40-69): Balanced (allow borderline with explanation)
  - Tier 3 (70-100): High-trust (fewer blocks, faster approvals)
- [ ] **Claude Code:** Add Trust Score tracking module; tie to Negotiation Agent logic

#### 3.2 Dynamic Policy Adaptation
- [ ] Reasoning agent consults child's current Trust Score tier before deciding
- [ ] Higher tier = lower decision threshold (more permissive)
- [ ] Parent can override thresholds per policy rule
- [ ] **Claude Code:** Modify reasoning engine to accept Trust Tier input

#### 3.3 Child Engagement Metrics
- [ ] Track explanation completion rate (did child read before requesting override?)
- [ ] Track request approval rate (% of requests that succeed without parent escalation)
- [ ] Build child-facing progress UI: "Your Trust Score: 62/100 → Tier 2 (Balanced Mode)"
- [ ] **Claude Code:** Add metrics tracking; extend child UI

#### 3.4 Real Network Layer (Optional, if time permits)
- [ ] Set up actual WireGuard mesh (or Tailscale emulation) connecting 2 test devices
- [ ] Route traffic through Python gateway (intercept DNS/HTTP requests)
- [ ] Reason on real URLs instead of emulated requests
- [ ] **Claude Code:** Add network config scripts; test with 2 physical/VM devices

#### 3.5 Terminal Reasoning Log UI (Live Streaming)
- [ ] Build live terminal-style log viewer showing real-time reasoning steps
- [ ] Each decision logs: step 1 (context extraction) → step 2 (risk assessment) → step 3 (policy check) → verdict
- [ ] Show confidence scores for each step
- [ ] Highlight final decision code (ALLOW/BLOCK/BORDERLINE)
- [ ] **Claude Code:** Create live-update UI using Flask + WebSocket or Server-Sent Events

#### 3.6 Test Dataset Expansion & Accuracy Validation
- [ ] Expand test dataset to 100 URLs
- [ ] Benchmark reasoning on ALLOW, BLOCK, BORDERLINE test sets
- [ ] Target accuracy: 80%+ on Borderline classification
- [ ] Document edge cases and reasoning failures
- [ ] **Claude Code:** Build test harness; generate accuracy report

#### 3.7 Demo Flow Documentation
- [ ] Write step-by-step demo script showing:
  - Request 1: Educational site (ALLOW)
  - Request 2: Explicit content (BLOCK)
  - Request 3: Borderline with conditions (escalate to parent)
  - Trust Score adaptation after child completes explanation
- [ ] Record or screenshot each step
- [ ] **Claude Code:** Document in DEMO.md

### Deliverable
**Full MVP:** Incentive Agent + Trust Score tiers + dynamic policies + live reasoning logs + 100-URL test set. 80%+ accuracy on borderline classification. Ready-to-demo multi-agent system.

---

## Success Criteria by MVP

### MVP 1 (Foundational)
- ✅ Request latency < 500ms
- ✅ Static reasoning engine accuracy 70%+ on test set
- ✅ Child + Parent UI working end-to-end
- ✅ Showable: "Here's how we reason about requests"

### MVP 2 (Core)
- ✅ Multi-agent system running
- ✅ Reasoning logs visible in terminal UI
- ✅ Family policy rules working
- ✅ Multi-device emulation
- ✅ Accuracy 75%+ on borderline
- ✅ Showable: "Here's how agents coordinate and learn family preferences"

### MVP 3 (Full)
- ✅ Incentive Agent + Trust Score system
- ✅ Dynamic policy adaptation
- ✅ Explanation completion tracking
- ✅ Live reasoning log streaming
- ✅ Accuracy 80%+ on 100-URL test set
- ✅ Real network layer (if time permits)
- ✅ Showable: "Here's a trust-aware system that gamifies digital responsibility"

---

## Track Alignment Mapping

### Harper (Personal AI Agents)
- **MVP 2+:** Multi-agent negotiation (Gatekeeper → Reasoning → Negotiation)
- **MVP 3:** Trust Score adaptation = preference learning over time
- **Demo:** Show 5+ interactions where agents learn family policy

### MBZUAI (Advanced Reasoning)
- **MVP 1+:** Chain-of-thought reasoning visible in decision logs
- **MVP 3:** Terminal-style reasoning logs with confidence scores
- **Demo:** Live reasoning trace showing risk assessment → policy check → decision

### Societal Impact
- **MVP 3:** Trust Score gamification + explanation-driven access
- **Demo:** Pre/post survey showing engagement increase; show how system reduces family conflict

---

## Technical Stack (Claude Code Friendly)

- **Backend:** Python 3.9+ (Flask/FastAPI)
- **Frontend:** HTML + Jinja2 templates (no build step needed)
- **Storage:** JSON files (expandable to SQLite)
- **Reasoning Model:** Rule-based (Phase 1) → integrate 7B model post-hackathon
- **Testing:** pytest, manual end-to-end tests
- **VCS:** Git (all work committed incrementally)

---

## Week 1 Timeline (Rough)

| Day | Phase | Focus | Deliverable |
|-----|-------|-------|-------------|
| 1 AM | Phase 1 | Setup + reasoning engine | Static engine working, 70%+ on test URLs |
| 1 PM | Phase 1 | UI + integration | Child + Parent UI wired; demo flow |
| 2 AM | Phase 2 | Multi-agent framework | Gatekeeper, Reasoning, Negotiation agents |
| 2 PM | Phase 2 | Logging + policy | Reasoning logs visible; family rules applied |
| 3 AM | Phase 2 | Multi-device | Emulation working; personalizes by age |
| 3 PM | Phase 3 | Incentive Agent | Trust Score + tiers working |
| 4 AM | Phase 3 | Metrics + polish | Accuracy 80%+; demo script ready |
| 4 PM | Phase 3 | Live logs + stretch goals | Real network layer (if time); final demo |

---

## Fallback Plan (If Stuck)

- **Stuck on reasoning model?** Use hardcoded rule-based classifier (Phase 1 engine). Still demonstrates concept.
- **Stuck on multi-agent?** Collapse to single agent with decision history. Still shows learning over time.
- **Stuck on network layer?** Emulate traffic via CLI input. Still end-to-end.
- **Stuck on Trust Score?** Show simpler engagement metrics (explanation read time). Still gamification.

**Showable at any point:** Current MVP is always demoed. Judge won't see incomplete work.

---

## Next Steps

1. Start Phase 1, Task 1.1: Project setup
2. Build test dataset (30 URLs with labels)
3. Implement reasoning_engine.py
4. Use Claude Code to write and test each module
5. Commit frequently; each completed task = new commit

**Ready to start?**
