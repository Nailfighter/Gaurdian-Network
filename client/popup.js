const input = document.getElementById("serverUrl");
const status = document.getElementById("status");

// Load saved value
chrome.storage.sync.get({ serverUrl: "http://localhost:8001" }, items => {
  input.value = items.serverUrl;
});

document.getElementById("save").addEventListener("click", () => {
  const url = input.value.trim().replace(/\/$/, "");
  chrome.storage.sync.set({ serverUrl: url }, () => {
    status.textContent = "Saved!";
    setTimeout(() => { status.textContent = ""; }, 2000);
  });
});
