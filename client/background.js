const DEFAULT_SERVER = "http://localhost:8001";
const SUPABASE_URL = "https://vqsqjetineezxtvchvbj.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxc3FqZXRpbmVlenh0dmNodmJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NjYyNzEsImV4cCI6MjA5MDM0MjI3MX0.SCx6yUZ7v8a6wAeuvAWHFE32bi3Wh4LfdA3QOAh5YZg";
const BLOCKLIST_REFRESH_MS = 30000; // 30 seconds
const BLOCKLIST_ALARM = "guardian-refresh-blocklist";
const BLOCKLIST_REFRESH_MINUTES = Math.max(1, Math.ceil(BLOCKLIST_REFRESH_MS / 60000));

function setLocalStorage(data) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set(data, () => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      resolve();
    });
  });
}

function getLocalStorage(defaults) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.get(defaults, items => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      resolve(items);
    });
  });
}

function getDynamicRules() {
  return new Promise((resolve, reject) => {
    chrome.declarativeNetRequest.getDynamicRules(rules => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      resolve(rules || []);
    });
  });
}

function updateDynamicRules(payload) {
  return new Promise((resolve, reject) => {
    chrome.declarativeNetRequest.updateDynamicRules(payload, () => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      resolve();
    });
  });
}

function normalizeDomain(value) {
  let candidate = String(value || "").trim().toLowerCase();
  if (!candidate) return "";

  try {
    const parsed = new URL(candidate);
    candidate = parsed.hostname || "";
  } catch {
    candidate = candidate.split("/")[0].split(":")[0];
  }

  candidate = candidate.replace(/\.$/, "");
  if (candidate.startsWith("www.")) {
    candidate = candidate.slice(4);
  }

  return candidate;
}

// ── Server URL ────────────────────────────────────────────────────────────────

function getServerUrl() {
  return new Promise(resolve => {
    chrome.storage.sync.get({ serverUrl: DEFAULT_SERVER }, items => {
      resolve(items.serverUrl);
    });
  });
}

// ── URL logging ───────────────────────────────────────────────────────────────

async function sendUrl(url) {
  if (!url) return;
  if (url.startsWith("chrome://") || url.startsWith("chrome-extension://")) return;

  let domain;
  try {
    domain = new URL(url).hostname;
  } catch {
    return;
  }

  const serverUrl = await getServerUrl();
  try {
    await fetch(`${serverUrl}/url-log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, domain, method: "GET", timestamp: new Date().toISOString() })
    });
  } catch (err) {
    console.warn("[Guardian] Could not reach server:", err.message);
  }
}

// Normal page loads
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url) {
    sendUrl(tab.url);
  }
});

// SPA navigation (YouTube, Twitter, Gmail, etc.)
chrome.webNavigation.onHistoryStateUpdated.addListener(details => {
  sendUrl(details.url);
});

// ── Blocklist / blocking ──────────────────────────────────────────────────────

async function fetchBlocklist() {
  try {
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/blocklist?active=eq.true&select=domain`,
      {
        headers: {
          "apikey": SUPABASE_ANON_KEY,
          "Authorization": `Bearer ${SUPABASE_ANON_KEY}`
        }
      }
    );
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Supabase ${res.status}: ${body.slice(0, 180)}`);
    }

    const data = await res.json();
    if (!Array.isArray(data)) {
      throw new Error("Unexpected Supabase response shape");
    }

    const normalized = data
      .map(row => normalizeDomain(row && row.domain))
      .filter(Boolean);

    return [...new Set(normalized)];
  } catch (err) {
    console.warn("[Guardian] Failed to fetch blocklist:", err.message);
    return [];
  }
}

async function updateBlockRules(domains) {
  const existing = await getDynamicRules();
  const removeRuleIds = existing.map(r => r.id);

  const addRules = domains.map((domain, i) => ({
    id: i + 1,
    priority: 1,
    action: {
      type: "redirect",
      redirect: { extensionPath: "/blocked.html" }
    },
    condition: {
      urlFilter: `||${domain}^`,
      resourceTypes: ["main_frame"]
    }
  }));

  await updateDynamicRules({ removeRuleIds, addRules });
  console.log(`[Guardian] Blocking ${domains.length} domain(s):`, domains);
}

async function refreshBlocklist() {
  try {
    const domains = await fetchBlocklist();
    await updateBlockRules(domains);
    await setLocalStorage({
      guardianBlockingStatus: {
        ok: true,
        lastRefreshAt: new Date().toISOString(),
        blockedDomains: domains,
        blockedRuleCount: domains.length,
        error: ""
      }
    });
  } catch (err) {
    console.warn("[Guardian] Could not refresh blocking rules:", err.message);
    await setLocalStorage({
      guardianBlockingStatus: {
        ok: false,
        lastRefreshAt: new Date().toISOString(),
        blockedDomains: [],
        blockedRuleCount: 0,
        error: err.message
      }
    });
  }
}

function ensureRefreshAlarm() {
  chrome.alarms.create(BLOCKLIST_ALARM, { periodInMinutes: BLOCKLIST_REFRESH_MINUTES });
}

chrome.runtime.onInstalled.addListener(() => {
  ensureRefreshAlarm();
  refreshBlocklist();
});

chrome.runtime.onStartup.addListener(() => {
  ensureRefreshAlarm();
  refreshBlocklist();
});

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === BLOCKLIST_ALARM) {
    refreshBlocklist();
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === "guardian.refreshBlocklist") {
    refreshBlocklist()
      .then(async () => {
        const rules = await getDynamicRules();
        sendResponse({ ok: true, ruleCount: rules.length });
      })
      .catch(err => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  if (message && message.type === "guardian.getBlockingStatus") {
    Promise.all([getDynamicRules(), getLocalStorage({ guardianBlockingStatus: null })])
      .then(([rules, status]) => {
        sendResponse({
          ok: true,
          ruleCount: rules.length,
          status: status.guardianBlockingStatus
        });
      })
      .catch(err => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  return false;
});

// Initial load when worker wakes
ensureRefreshAlarm();
refreshBlocklist();
