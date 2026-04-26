import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import Card, { buttonStyle, inputStyle, tableStyle, tdStyle, thStyle } from "../components/Card.jsx";

const blank = { title: "", severity: "High", type: "ICT_INCIDENT", frameworks: ["DORA", "NIS2"] };

export default function Incidents() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(blank);
  const [err, setErr] = useState("");

  const load = () => api("/api/grc/incidents").then(setItems).catch((e) => setErr(e.message));
  useEffect(load, []);

  const create = async (e) => {
    e.preventDefault(); setErr("");
    try { await api("/api/grc/incidents", { method: "POST", body: form });
      setForm(blank); load();
    } catch (e) { setErr(e.message); }
  };

  return (
    <>
      <Card title="Open incident (starts DORA Art. 17 / NIS2 Art. 21 timers)">
        <form onSubmit={create} style={{ display: "grid", gridTemplateColumns: "3fr 1fr 1fr auto", gap: 12, alignItems: "flex-end" }}>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Title</label>
            <input style={inputStyle} required value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Severity</label>
            <select style={inputStyle} value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}>
              <option>Low</option><option>Medium</option><option>High</option><option>Critical</option>
            </select></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Type</label>
            <select style={inputStyle} value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}>
              <option value="ICT_INCIDENT">ICT incident (DORA)</option>
              <option value="SIGNIFICANT_INCIDENT">Significant (NIS2)</option>
              <option value="DATA_BREACH">Personal data breach (GDPR)</option>
            </select></div>
          <button style={buttonStyle} type="submit">Open</button>
        </form>
        {err && <p style={{ color: "#f87171", fontSize: 13 }}>{err}</p>}
      </Card>

      <Card title={`Incidents (${items.length})`}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>ID</th><th style={thStyle}>Title</th>
              <th style={thStyle}>Severity</th><th style={thStyle}>Status</th>
              <th style={thStyle}>DORA deadline</th><th style={thStyle}>NIS2 deadline</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id}>
                <td style={tdStyle}>{i.id}</td>
                <td style={tdStyle}>{i.title}</td>
                <td style={tdStyle}>{i.severity}</td>
                <td style={tdStyle}>{i.status}</td>
                <td style={tdStyle}>{i.dora_deadline || "-"}</td>
                <td style={tdStyle}>{i.nis2_deadline || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
