import { useEffect, useState, useCallback } from "react";

const SERVER_URL = "/api";

export default function Dashboard() {
  const [entries, setEntries] = useState([]);
  const [offline, setOffline] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadLog = useCallback(async () => {
    try {
      const res = await fetch(`${SERVER_URL}/dns-log?n=200`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setEntries(data.entries ?? []);
      setOffline(false);
    } catch {
      setOffline(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLog();
    const interval = setInterval(loadLog, 3000);
    return () => clearInterval(interval);
  }, [loadLog]);

  return (
    <div style={{ fontFamily: "monospace", padding: "1rem" }}>
      <header style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.25rem" }}>Guardian — DNS Log</h1>
        <span
          title={offline ? "Server offline" : "Connected"}
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: offline ? "#e55" : "#4c4",
            display: "inline-block",
          }}
        />
      </header>

      {offline && (
        <p style={{ color: "#e55" }}>Server offline — retrying&hellip;</p>
      )}

      {loading && <p>Loading&hellip;</p>}

      {!loading && entries.length === 0 && (
        <p style={{ color: "#888" }}>No DNS queries logged yet.</p>
      )}

      {entries.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #444", textAlign: "left" }}>
              <th style={{ padding: "0.4rem 0.75rem" }}>Time</th>
              <th style={{ padding: "0.4rem 0.75rem" }}>Device</th>
              <th style={{ padding: "0.4rem 0.75rem" }}>Device ID</th>
              <th style={{ padding: "0.4rem 0.75rem" }}>Client IP</th>
              <th style={{ padding: "0.4rem 0.75rem" }}>Domain</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr
                key={i}
                style={{
                  borderBottom: "1px solid #222",
                  background: i % 2 === 0 ? "transparent" : "#0a0a0a",
                }}
              >
                <td style={{ padding: "0.35rem 0.75rem", color: "#888", whiteSpace: "nowrap" }}>
                  {new Date(e.timestamp).toLocaleTimeString()}
                </td>
                <td style={{ padding: "0.35rem 0.75rem", color: "#e2e8f0" }}>
                  {e.device_name || "Unknown Device"}
                </td>
                <td style={{ padding: "0.35rem 0.75rem", color: "#94a3b8", fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" }}>
                  {e.device_id || "unknown-device"}
                </td>
                <td style={{ padding: "0.35rem 0.75rem", color: "#aaa" }}>{e.client_ip}</td>
                <td style={{ padding: "0.35rem 0.75rem" }}>{e.domain}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
