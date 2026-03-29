# Client Agent Tasks

**Branch:** `client`
**Folder:** `client/`
**Stack:** HTML · Jinja2 · Flask (thin wrapper) or static fetch calls to server

You own the child-facing UI. Do not edit `parent/` or `server/`.

Server base URL is read from the `SERVER_URL` environment variable (default `http://localhost:5000`).

---

## Folder Layout (create this)

```
client/
├── app.py                  # Thin Flask app serving templates (optional — can be pure static)
├── templates/
│   ├── index.html          # Request page
│   ├── decision.html       # Decision result page
│   └── trust.html          # Trust score / progress page
└── static/
    └── style.css
```

---

## Phase 1 Tasks

### 1.3 Child Request UI
- [ ] `client/templates/index.html` — form: child enters a URL and clicks "Request Access"
  - Fields: URL input, optional context note ("I need this for homework")
  - On submit: `POST {SERVER_URL}/request` with `{ url, context, device_id }`
- [ ] `client/templates/decision.html` — display server response:
  - Decision badge: **ALLOW** (green) / **BLOCK** (red) / **PAUSED** (yellow)
  - Score bar: 0-100
  - Plain-English reason text
  - "Request Override" button — re-posts with `override: true` flag, shows "Parent has been notified"
- [ ] Wire both pages together (form submit → decision display)

---

## Phase 2 Tasks

### 2.5 Multi-Device Identity
- [ ] Read `DEVICE_ID` from environment variable (or localStorage fallback)
- [ ] Display device name on all pages (e.g. "Alex's iPad")
- [ ] Send `device_id` with every request to server

---

## Phase 3 Tasks

### 3.3 Trust Score Progress Page
- [ ] `client/templates/trust.html` — fetch `GET {SERVER_URL}/trust/<device_id>` and display:
  - "Your Trust Score: 62 / 100"
  - Current tier badge: Tier 1 (Strict) / Tier 2 (Balanced) / Tier 3 (High-Trust)
  - Progress bar toward next tier
  - Simple tip: "Read explanations fully to earn more points"
- [ ] Link to trust page from decision page ("See your score →")
- [ ] Send `dwell_time` flag to server when child spends > 5 seconds on the decision/explanation page
  - `POST {SERVER_URL}/request` or a separate `POST /engagement` endpoint — confirm with server agent

### 3.5 Live Reasoning Log Viewer (child-readable summary)
- [ ] On `decision.html`, show collapsible "How did we decide?" section
  - Step 1: Context extracted
  - Step 2: Risk assessed (score + label)
  - Step 3: Policy checked
  - Final verdict
- [ ] Pull data from `agent_trace` field in server decision response — no extra endpoint needed

---

## Integration Checklist

Before marking a task done, verify:
- [ ] `SERVER_URL` env var is used (not hardcoded)
- [ ] `device_id` is sent in every request body
- [ ] UI handles all three decision states: ALLOW, BLOCK, PAUSED
- [ ] Works when server returns an error (show friendly message, not a crash)
