# Guardian Core: Incremental Build Plan

**Goal:** Build trust-enabling parental control with multi-agent reasoning.
**Timeline:** Week 1 Hackathon Sprint

---

## Folder Structure

```
/
├── client/    # Child-facing UI
├── parent/    # Parent dashboard UI
└── server/    # Backend: agents, reasoning engine, gateway, data, tests
```

---

## Agent Branch Ownership

| Branch | Folder | Task File |
|--------|--------|-----------|
| `client` | `client/` | [client.md](client.md) |
| `parent` | `parent/` | [parent.md](parent.md) |
| `server` | `server/` | [server.md](server.md) |

Each agent works **only in its own folder and task file**. Do not edit other folders.

---

## MVP Progression

| MVP | Phase | Deliverable |
|-----|-------|-------------|
| MVP 1 (Foundational) | Days 1-2 | Static reasoning engine + Child UI + Parent UI wired end-to-end |
| MVP 2 (Core) | Days 2-3 | Multi-agent orchestration + reasoning logs + family policy + multi-device |
| MVP 3 (Full) | Days 3-4 | Incentive Agent + Trust Score + live logs + 100-URL test set |

Each MVP is **showable independently**.

---

## Integration Contract (shared API)

All three agents communicate through the server gateway. The server exposes:

```
POST /request          # child submits URL request
GET  /requests         # parent polls pending requests
POST /decision/<id>    # parent approves or denies
GET  /logs             # reasoning log stream
GET  /trust/<device>   # trust score for a device
```

Base URL configured via `SERVER_URL` environment variable in client and parent.

---

## Week 1 Timeline

| Day | Focus | Deliverable |
|-----|-------|-------------|
| 1 AM | Setup + reasoning engine | Static engine, 70%+ on test URLs |
| 1 PM | UIs + integration | Child + Parent wired; demo flow |
| 2 AM | Multi-agent framework | Gatekeeper, Reasoning, Negotiation agents |
| 2 PM | Logging + policy | Reasoning logs visible; family rules applied |
| 3 AM | Multi-device | Emulation working; personalises by age |
| 3 PM | Incentive Agent | Trust Score + tiers working |
| 4 AM | Metrics + polish | 80%+ accuracy; demo script ready |
| 4 PM | Live logs + stretch | Real network layer if time; final demo |

---

## Fallback Plan

- **Stuck on reasoning?** Use hardcoded rule-based classifier — still demonstrates concept.
- **Stuck on multi-agent?** Collapse to single agent with decision history.
- **Stuck on network?** Emulate traffic via CLI input.
- **Stuck on Trust Score?** Show explanation read-time metric instead.
