const input = document.getElementById("serverUrl");
const status = document.getElementById("status");
const statusIndicator = document.getElementById("statusIndicator");
const connectionStatus = document.getElementById("connectionStatus");
const blockStatus = document.getElementById("blockStatus");
const refreshBlocklistBtn = document.getElementById("refreshBlocklist");
const SUPABASE_URL = "https://vqsqjetineezxtvchvbj.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxc3FqZXRpbmVlenh0dmNodmJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NjYyNzEsImV4cCI6MjA5MDM0MjI3MX0.SCx6yUZ7v8a6wAeuvAWHFE32bi3Wh4LfdA3QOAh5YZg";

// Load saved value
chrome.storage.sync.get({ serverUrl: "http://localhost:8001" }, items => {
  input.value = items.serverUrl;
  checkConnection();
  loadBlockingStatus();
});

// Recheck connection when input changes
input.addEventListener("change", checkConnection);

// Check connection to backend
async function checkConnection() {
  const url = input.value.trim().replace(/\/$/, "");
  statusIndicator.className = "status-indicator status-checking";
  connectionStatus.textContent = "Checking connection...";

  try {
    const response = await Promise.race([
      fetch(`${url}/test`, { method: "GET" }),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("timeout")), 3000)
      )
    ]);

    if (response && response.ok) {
      statusIndicator.className = "status-indicator status-connected";
      connectionStatus.textContent = `✓ Connected to ${url}`;
    } else {
      throw new Error("Server responded but status not ok");
    }
  } catch (err) {
    statusIndicator.className = "status-indicator status-disconnected";
    connectionStatus.textContent = `✗ Cannot reach ${url}`;
    console.warn("[Guardian] Connection check failed:", err.message);
  }
}

document.getElementById("save").addEventListener("click", () => {
  const url = input.value.trim().replace(/\/$/, "");
  chrome.storage.sync.set({ serverUrl: url }, () => {
    status.textContent = "Saved!";
    setTimeout(() => { status.textContent = ""; }, 2000);
    checkConnection();
  });
});

function sendMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, response => {
      const runtimeError = chrome.runtime.lastError;
      if (runtimeError) {
        reject(new Error(runtimeError.message));
        return;
      }
      resolve(response);
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
  if (candidate.startsWith("www.")) candidate = candidate.slice(4);
  return candidate;
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

async function fetchBlocklistDirect() {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/blocklist?active=eq.true&select=domain`, {
    headers: {
      "apikey": SUPABASE_ANON_KEY,
      "Authorization": `Bearer ${SUPABASE_ANON_KEY}`
    }
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Supabase ${res.status}: ${body.slice(0, 180)}`);
  }

  const rows = await res.json();
  if (!Array.isArray(rows)) {
    throw new Error("Unexpected Supabase response shape");
  }

  const domains = rows.map(r => normalizeDomain(r && r.domain)).filter(Boolean);
  return [...new Set(domains)];
}

async function refreshBlocklistDirect() {
  const domains = await fetchBlocklistDirect();
  const existing = await getDynamicRules();
  const removeRuleIds = existing.map(r => r.id);
  const addRules = domains.map((domain, i) => ({
    id: i + 1,
    priority: 1,
    action: { type: "redirect", redirect: { extensionPath: "/blocked.html" } },
    condition: {
      urlFilter: `||${domain}^`,
      resourceTypes: ["main_frame"]
    }
  }));

  await updateDynamicRules({ removeRuleIds, addRules });
  await setLocalStorage({
    guardianBlockingStatus: {
      ok: true,
      lastRefreshAt: new Date().toISOString(),
      blockedDomains: domains,
      blockedRuleCount: addRules.length,
      error: ""
    }
  });

  return addRules.length;
}

function formatTime(iso) {
  if (!iso) return "never";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "unknown";
  return date.toLocaleTimeString();
}

async function loadBlockingStatus() {
  blockStatus.textContent = "Block rules: checking...";
  try {
    let ruleCount = 0;
    let statusData = null;

    try {
      const response = await sendMessage({ type: "guardian.getBlockingStatus" });
      if (!response || !response.ok) {
        throw new Error((response && response.error) || "Unknown status error");
      }
      ruleCount = response.ruleCount;
      statusData = response.status || {};
    } catch {
      const rules = await getDynamicRules();
      const local = await getLocalStorage({ guardianBlockingStatus: null });
      ruleCount = rules.length;
      statusData = local.guardianBlockingStatus || {};
    }

    const lastRefresh = formatTime(statusData.lastRefreshAt);
    const errorText = statusData.error ? ` | error: ${statusData.error}` : "";
    blockStatus.textContent = `Block rules: ${ruleCount} | last sync: ${lastRefresh}${errorText}`;
  } catch (err) {
    blockStatus.textContent = `Block rules: unavailable (${err.message})`;
  }
}

refreshBlocklistBtn.addEventListener("click", async () => {
  refreshBlocklistBtn.disabled = true;
  blockStatus.textContent = "Syncing blocklist...";
  try {
    let ruleCount;
    try {
      const response = await sendMessage({ type: "guardian.refreshBlocklist" });
      if (!response || !response.ok) {
        throw new Error((response && response.error) || "Unknown refresh error");
      }
      ruleCount = response.ruleCount;
    } catch {
      ruleCount = await refreshBlocklistDirect();
    }

    blockStatus.textContent = `Block rules: ${ruleCount} | synced now`;
    setTimeout(loadBlockingStatus, 500);
  } catch (err) {
    blockStatus.textContent = `Sync failed: ${err.message}`;
  } finally {
    refreshBlocklistBtn.disabled = false;
  }
});

