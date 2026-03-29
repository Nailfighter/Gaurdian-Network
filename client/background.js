const DEFAULT_SERVER = "http://localhost:8001";

function getServerUrl() {
  return new Promise(resolve => {
    chrome.storage.sync.get({ serverUrl: DEFAULT_SERVER }, items => {
      resolve(items.serverUrl);
    });
  });
}

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  // Only fire when the page finishes loading and has a real URL
  if (changeInfo.status !== "complete") return;
  if (!tab.url) return;
  if (tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://")) return;

  const serverUrl = await getServerUrl();
  const domain = new URL(tab.url).hostname;

  try {
    await fetch(`${serverUrl}/url-log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: tab.url,
        domain: domain,
        method: "GET",
        timestamp: new Date().toISOString()
      })
    });
  } catch (err) {
    console.warn("[Guardian] Could not reach server:", err.message);
  }
});
