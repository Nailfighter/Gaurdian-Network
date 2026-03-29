const DEFAULT_SERVER = "http://localhost:8001";

function getServerUrl() {
  return new Promise(resolve => {
    chrome.storage.sync.get({ serverUrl: DEFAULT_SERVER }, items => {
      resolve(items.serverUrl);
    });
  });
}

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
      body: JSON.stringify({
        url: url,
        domain: domain,
        method: "GET",
        timestamp: new Date().toISOString()
      })
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

// SPA navigation (YouTube, Twitter, Gmail etc. — URL changes without full reload)
chrome.webNavigation.onHistoryStateUpdated.addListener(details => {
  sendUrl(details.url);
});
