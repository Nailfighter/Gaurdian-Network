import { useEffect, useState, useCallback } from "react";
import { supabase } from "../lib/supabase";

export default function Blocklist() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const { data, error } = await supabase
      .from("blocklist")
      .select("*")
      .order("created_at", { ascending: false });
    if (!error) setEntries(data ?? []);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  async function addDomain() {
    const domain = input.trim().toLowerCase().replace(/^www\./, "").replace(/^https?:\/\//, "").split("/")[0];
    if (!domain) return;
    setAdding(true);
    setError("");
    const { error } = await supabase.from("blocklist").insert({ domain, active: true });
    if (error) {
      setError(error.message.includes("unique") ? `${domain} is already in the blocklist` : error.message);
    } else {
      setInput("");
      await load();
    }
    setAdding(false);
  }

  async function toggleActive(id, current) {
    await supabase.from("blocklist").update({ active: !current }).eq("id", id);
    await load();
  }

  async function remove(id) {
    await supabase.from("blocklist").delete().eq("id", id);
    await load();
  }

  const s = {
    container: { fontFamily: "monospace", padding: "1rem" },
    row: { display: "flex", gap: "0.5rem", marginBottom: "1rem" },
    input: { flex: 1, padding: "0.4rem 0.6rem", fontSize: "0.9rem", background: "#111", color: "#eee", border: "1px solid #444", borderRadius: 4 },
    btn: (color) => ({ padding: "0.4rem 0.9rem", fontSize: "0.85rem", background: color, color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }),
    error: { color: "#e55", fontSize: "0.85rem", marginBottom: "0.75rem" },
    table: { width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" },
    th: { padding: "0.4rem 0.75rem", borderBottom: "1px solid #444", textAlign: "left" },
    td: { padding: "0.35rem 0.75rem", borderBottom: "1px solid #222" },
    badge: (active) => ({ display: "inline-block", padding: "0.2rem 0.5rem", borderRadius: 3, fontSize: "0.75rem", background: active ? "#166534" : "#555", color: "#fff" }),
  };

  return (
    <div style={s.container}>
      <h1 style={{ margin: "0 0 1rem", fontSize: "1.25rem" }}>Blocklist</h1>

      <div style={s.row}>
        <input
          style={s.input}
          type="text"
          placeholder="youtube.com or https://tiktok.com"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && addDomain()}
        />
        <button style={s.btn("#dc2626")} onClick={addDomain} disabled={adding}>
          {adding ? "Adding…" : "Block"}
        </button>
      </div>

      {error && <p style={s.error}>{error}</p>}

      {loading && <p>Loading…</p>}

      {!loading && entries.length === 0 && (
        <p style={{ color: "#888" }}>No domains blocked yet.</p>
      )}

      {entries.length > 0 && (
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>Domain</th>
              <th style={s.th}>Status</th>
              <th style={s.th}>Added</th>
              <th style={s.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(e => (
              <tr key={e.id} style={{ background: e.active ? "transparent" : "#0d0d0d" }}>
                <td style={s.td}>{e.domain}</td>
                <td style={s.td}>
                  <span style={s.badge(e.active)}>{e.active ? "Blocked" : "Inactive"}</span>
                </td>
                <td style={{ ...s.td, color: "#888", whiteSpace: "nowrap" }}>
                  {new Date(e.created_at).toLocaleDateString()}
                </td>
                <td style={s.td}>
                  <button style={{ ...s.btn("#374151"), marginRight: "0.4rem" }} onClick={() => toggleActive(e.id, e.active)}>
                    {e.active ? "Disable" : "Enable"}
                  </button>
                  <button style={s.btn("#7f1d1d")} onClick={() => remove(e.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
