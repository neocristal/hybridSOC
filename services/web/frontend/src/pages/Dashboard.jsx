import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import Card, { tableStyle, thStyle, tdStyle } from "../components/Card.jsx";

const tile = {
  background: "#0f172a", border: "1px solid #334155", borderRadius: 6,
  padding: 16, flex: 1,
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api("/api/dashboard/stats").then(setStats).catch((e) => setErr(e.message));
  }, []);

  if (err) return <Card title="Dashboard"><p style={{ color: "#f87171" }}>{err}</p></Card>;
  if (!stats) return <Card title="Dashboard"><p>Loading…</p></Card>;

  return (
    <>
      <h2 style={{ color: "#f1f5f9" }}>Overview</h2>
      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <div style={tile}><div style={{ color: "#94a3b8", fontSize: 13 }}>Users</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.counts.users}</div></div>
        <div style={tile}><div style={{ color: "#94a3b8", fontSize: 13 }}>Open incidents</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.counts.open_incidents}</div></div>
        <div style={tile}><div style={{ color: "#94a3b8", fontSize: 13 }}>Risks</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.counts.risks}</div></div>
        <div style={tile}><div style={{ color: "#94a3b8", fontSize: 13 }}>Audit entries</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.counts.audit_entries}</div></div>
      </div>

      <Card title="Incidents by severity">
        {stats.severity.length === 0
          ? <p style={{ color: "#94a3b8" }}>No incidents recorded.</p>
          : <SeverityBars data={stats.severity} />}
      </Card>

      <Card title="Risk distribution (likelihood × impact)">
        <table style={tableStyle}>
          <thead><tr><th style={thStyle}>Bucket</th><th style={thStyle}>Count</th></tr></thead>
          <tbody>
            {stats.risk_buckets.map((b) => (
              <tr key={b.bucket}><td style={tdStyle}>{b.bucket}</td><td style={tdStyle}>{b.count}</td></tr>
            ))}
            {stats.risk_buckets.length === 0 && (
              <tr><td colSpan={2} style={{ ...tdStyle, color: "#94a3b8" }}>No risks recorded.</td></tr>
            )}
          </tbody>
        </table>
      </Card>
    </>
  );
}

function SeverityBars({ data }) {
  const max = Math.max(...data.map((d) => d.count), 1);
  const colors = { Critical: "#ef4444", High: "#f97316", Medium: "#eab308", Low: "#22c55e" };
  return (
    <div>
      {data.map((d) => (
        <div key={d.severity} style={{ marginBottom: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
            <span>{d.severity}</span><span>{d.count}</span>
          </div>
          <div style={{ background: "#0f172a", borderRadius: 4, height: 8 }}>
            <div style={{
              width: `${(d.count / max) * 100}%`, height: "100%",
              background: colors[d.severity] || "#60a5fa", borderRadius: 4,
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}
