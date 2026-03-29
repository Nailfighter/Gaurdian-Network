const input = document.getElementById("serverUrl");
const status = document.getElementById("status");
const statusIndicator = document.getElementById("statusIndicator");
const connectionStatus = document.getElementById("connectionStatus");

// Load saved value
chrome.storage.sync.get({ serverUrl: "http://localhost:8001" }, items => {
  input.value = items.serverUrl;
  checkConnection();
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

