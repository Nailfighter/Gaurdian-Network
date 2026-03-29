# Parent Agent Tasks

**Branch:** `parent`
**Folder:** `parent/`
**Stack:** HTML · Jinja2 · Flask (thin wrapper) or static fetch calls to server

You own the parent dashboard UI. Do not edit `client/` or `server/`.

Server base URL is read from the `SERVER_URL` environment variable (default `http://localhost:5000`).

---

## Folder Layout (create this)

```
parent/
├── app.py                  # Thin Flask app serving templates (optional — can be pure static)
├── templates/
│   ├── dashboard.html      # Main request review page
│   ├── logs.html           # Reasoning log viewer
│   └── policy.html         # Family policy configuration
└── static/
    └── style.css
```

---

## Phase 1 Tasks

### 1.4 Parent Dashboard
  - List of recent child requests (URL, device name, timestamp)
  - For each request: decision badge (ALLOW / BLOCK / PAUSED), score (0-100), reason text
  - For PAUSED requests: **Approve** and **Deny** buttons
    - Approve: `POST {SERVER_URL}/decision/<id>` with `{ action: "approve" }`
    - Deny: `POST {SERVER_URL}/decision/<id>` with `{ action: "deny" }`
  - Auto-refresh every 5 seconds (simple `setTimeout` + fetch, no WebSocket needed for Phase 1)

---

## Phase 2 Tasks

### 2.5 Multi-Device Dashboard
- [ ] Group requests by device/child name (use `device_id` + `name` from server response)
- [ ] Show each child's device in a separate section or tab
- [ ] Display child age alongside device name (from server's device record)

### 2.2 Reasoning Log Viewer
- [ ] `parent/templates/logs.html` — terminal-style scrollable log
  - Fetch `GET {SERVER_URL}/logs?n=50`
  - Each row: timestamp · device · URL · verdict badge · score
  - Expandable row: show full `agent_trace` (step-by-step reasoning)
  - Auto-refresh every 10 seconds
- [ ] Link from dashboard header: "View Reasoning Logs →"

### 2.3 Family Policy Editor
- [ ] `parent/templates/policy.html` — view and edit family rules
  - Fetch current rules from `GET {SERVER_URL}/policy` (confirm endpoint with server agent)
  - List existing rules with pattern, action, and optional time restriction
  - "Add Rule" form: pattern (text), action (dropdown: always_allow / block / ask), hours (optional)
  - Save: `POST {SERVER_URL}/policy` with updated rules JSON
  - "Delete" button per rule

---

## Phase 3 Tasks

### 3.3 Trust Score Overview
- [ ] Add trust score column to each device section on `dashboard.html`
  - Fetch `GET {SERVER_URL}/trust/<device_id>` per device
  - Show score badge and tier label next to device name
  - Small note: "+5 pts next time they accept terms without dispute"

### 3.5 Live Reasoning Log (streaming)
- [ ] Upgrade `logs.html` to use Server-Sent Events or WebSocket if server supports it
  - Confirm with server agent whether `GET /logs/stream` SSE endpoint is available
  - Fall back to polling if not implemented
- [ ] Highlight the most recent entry with a pulse animation
- [ ] Colour-code verdict: green (ALLOW), red (BLOCK), yellow (PAUSED)

---

## Integration Checklist

Before marking a task done, verify:
- [ ] `SERVER_URL` env var is used (not hardcoded)
- [ ] Dashboard handles empty request list gracefully (show "No requests yet")
- [ ] Approve/Deny buttons disable after click to prevent double-submit
- [ ] Policy page validates that pattern field is not empty before saving
- [ ] Works when server is temporarily unreachable (show "Server offline" banner, not a crash)
