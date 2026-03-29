import { useEffect, useState, useCallback } from "react";

const SERVER_URL = "/api";

export default function Dashboard() {
  const [entries, setEntries] = useState([]);
  const [offline, setOffline] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadLog = useCallback(async () => {
    try {
      const res = await fetch(`${SERVER_URL}/url-log?n=200`);
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
    const interval = setInterval(loadLog, 5000);
    return () => clearInterval(interval);
  }, [loadLog]);

  return (
    <div style={{ fontFamily: "monospace", padding: "1rem" }}>
      <header style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.25rem" }}>Guardian — Browsing Activity</h1>
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
        <p style={{ color: "#888" }}>No activity yet — install the Chrome extension on the child's browser.</p>
      )}

      {entries.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #444", textAlign: "left" }}>
              <th style={{ padding: "0.4rem 0.75rem" }}>Time</th>
              <th style={{ padding: "0.4rem 0.75rem" }}>Domain</th>
              <th style={{ padding: "0.4rem 0.75rem" }}>Full URL</th>
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
                <td style={{ padding: "0.35rem 0.75rem", color: "#aaa", whiteSpace: "nowrap" }}>
                  {e.domain}
                </td>
                <td style={{ padding: "0.35rem 0.75rem", maxWidth: "600px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  <a href={e.url} target="_blank" rel="noopener noreferrer" style={{ color: "#58a6ff" }}>
                    {e.url}
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
