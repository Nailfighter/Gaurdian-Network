const DEFAULT_SERVER = "http://localhost:8001";
const SUPABASE_URL = "https://vqsqjetineezxtvchvbj.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxc3FqZXRpbmVlenh0dmNodmJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NjYyNzEsImV4cCI6MjA5MDM0MjI3MX0.SCx6yUZ7v8a6wAeuvAWHFE32bi3Wh4LfdA3QOAh5YZg";
const BLOCKLIST_REFRESH_MS = 30000; // 30 seconds

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
    const data = await res.json();
    return data.map(r => r.domain).filter(Boolean);
  } catch (err) {
    console.warn("[Guardian] Failed to fetch blocklist:", err.message);
    return [];
  }
}

async function updateBlockRules(domains) {
  const existing = await chrome.declarativeNetRequest.getDynamicRules();
  const removeRuleIds = existing.map(r => r.id);

  const addRules = domains.map((domain, i) => ({
    id: i + 1,
    priority: 1,
    action: {
      type: "redirect",
      redirect: { extensionPath: "/blocked.html" }
    },
    condition: {
      urlFilter: `||${domain}`,
      resourceTypes: ["main_frame"]
    }
  }));

  await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds, addRules });
  console.log(`[Guardian] Blocking ${domains.length} domain(s):`, domains);
}

async function refreshBlocklist() {
  const domains = await fetchBlocklist();
  await updateBlockRules(domains);
}

// Initial load + periodic refresh
refreshBlocklist();
setInterval(refreshBlocklist, BLOCKLIST_REFRESH_MS);
