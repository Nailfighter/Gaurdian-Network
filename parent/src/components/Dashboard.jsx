import { useEffect, useState, useCallback } from "react";

const SERVER_URL = "/api";

const VERDICT_STYLES = {
  ALLOW:  { label: "ALLOW",  className: "badge allow" },
  BLOCK:  { label: "BLOCK",  className: "badge block" },
  PAUSED: { label: "PAUSED", className: "badge paused" },
};

function Badge({ verdict }) {
  const s = VERDICT_STYLES[verdict] ?? { label: verdict ?? "PENDING", className: "badge" };
  return <span className={s.className}>{s.label}</span>;
}

function RequestCard({ request, onDecide }) {
  const [deciding, setDeciding] = useState(false);

  async function handleDecide(action) {
    setDeciding(true);
    await onDecide(request.id, action);
    setDeciding(false);
  }

  return (
    <div className="request-card">
      <div className="request-header">
        <Badge verdict={request.verdict} />
        <span className="score">Score: {request.decision_score ?? "—"}/100</span>
        <span className="device">{request.device_id ?? "unknown device"}</span>
        <span className="timestamp">{request.timestamp ? new Date(request.timestamp).toLocaleTimeString() : "—"}</span>
      </div>
      <div className="url">
        <a href={request.url} target="_blank" rel="noopener noreferrer">{request.url}</a>
      </div>
      {request.reason_text && <p className="reason">{request.reason_text}</p>}
      {request.verdict === "PAUSED" && (
        <div className="actions">
          <button className="btn approve" disabled={deciding} onClick={() => handleDecide("approve")}>
            Approve
          </button>
          <button className="btn deny" disabled={deciding} onClick={() => handleDecide("deny")}>
            Deny
          </button>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [requests, setRequests] = useState([]);
  const [offline, setOffline]   = useState(false);
  const [loading, setLoading]   = useState(true);

  const loadRequests = useCallback(async () => {
    try {
      const res = await fetch(`${SERVER_URL}/requests`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list = data.requests ?? data;
      setRequests(Array.isArray(list) ? list : Object.values(list ?? {}));
      setOffline(false);
    } catch {
      setOffline(true);
    } finally {
      setLoading(false);
    }
  }, []);

  async function handleDecide(id, action) {
    try {
      const res = await fetch(`${SERVER_URL}/decision/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setRequests((prev) =>
        prev.map((r) =>
          r.id === id ? { ...r, verdict: action === "approve" ? "ALLOW" : "BLOCK" } : r
        )
      );
    } catch {
      alert("Failed to submit decision — please try again.");
    }
  }

  useEffect(() => {
    loadRequests();
    const interval = setInterval(loadRequests, 5000);
    return () => clearInterval(interval);
  }, [loadRequests]);

  return (
    <div>
      <header>
        <h1>Guardian Parent Dashboard</h1>
        <span className={`status-dot ${offline ? "offline" : "online"}`} title={offline ? "Server offline" : "Connected"} />
      </header>

      <main>
        {offline && (
          <div className="banner error">Server offline — retrying&hellip;</div>
        )}

        <section>
          <h2>Child Requests</h2>
          {loading && <p className="empty-state">Loading&hellip;</p>}
          {!loading && requests.length === 0 && (
            <p className="empty-state">No requests yet.</p>
          )}
          {requests.map((r) => (
            <RequestCard key={r.id} request={r} onDecide={handleDecide} />
          ))}
        </section>
      </main>
    </div>
  );
}
