import { useState } from "react";
import Dashboard from "./components/Dashboard";
import Blocklist from "./components/Blocklist";

const tabs = [
  { id: "activity", label: "Browsing Activity" },
  { id: "blocklist", label: "Blocklist" },
];

export default function App() {
  const [tab, setTab] = useState("activity");

  return (
    <div>
      <nav style={{ display: "flex", gap: "0", borderBottom: "1px solid #333", marginBottom: "0" }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: "0.6rem 1.25rem",
              fontSize: "0.9rem",
              fontFamily: "monospace",
              background: tab === t.id ? "#1a1a1a" : "transparent",
              color: tab === t.id ? "#fff" : "#888",
              border: "none",
              borderBottom: tab === t.id ? "2px solid #58a6ff" : "2px solid transparent",
              cursor: "pointer",
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "activity" && <Dashboard />}
      {tab === "blocklist" && <Blocklist />}
    </div>
  );
}
