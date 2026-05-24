import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import Card, { buttonStyle, inputStyle, tableStyle, tdStyle, thStyle } from "../components/Card.jsx";

const blank = { title: "", likelihood: 3, impact: 3, framework: "DORA", article: "", treatment: "" };

export default function RiskRegister() {
  const [risks, setRisks] = useState([]);
  const [form, setForm] = useState(blank);
  const [scoreInput, setScoreInput] = useState({
    user: "analyst01", activity: "bulk_file_download", ip: "192.168.10.45",
    bytes_transferred: 524288000,
  });
  const [scoreResult, setScoreResult] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api("/api/risk/").then(setRisks).catch((e) => setErr(e.message));
  useEffect(load, []);

  const create = async (e) => {
    e.preventDefault(); setErr("");
    try { await api("/api/risk/", { method: "POST", body: form });
      setForm(blank); load();
    } catch (e) { setErr(e.message); }
  };

  const score = async (e) => {
    e.preventDefault(); setErr(""); setScoreResult(null);
    try {
      const r = await api("/api/risk/score", { method: "POST", body: scoreInput });
      setScoreResult(r);
    } catch (e) { setErr(e.message); }
  };

  return (
    <>
      <Card title="Add risk">
        <form onSubmit={create} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 2fr auto", gap: 12, alignItems: "flex-end" }}>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Title</label>
            <input style={inputStyle} required value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Likelihood</label>
            <input style={inputStyle} type="number" min={1} max={5} value={form.likelihood}
              onChange={(e) => setForm({ ...form, likelihood: +e.target.value })} /></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Impact</label>
            <input style={inputStyle} type="number" min={1} max={5} value={form.impact}
              onChange={(e) => setForm({ ...form, impact: +e.target.value })} /></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Framework</label>
            <select style={inputStyle} value={form.framework}
              onChange={(e) => setForm({ ...form, framework: e.target.value })}>
              <option>DORA</option><option>NIS2</option><option>ISO27001</option>
              <option>GDPR</option><option>EUAI</option>
            </select></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Treatment</label>
            <input style={inputStyle} value={form.treatment}
              onChange={(e) => setForm({ ...form, treatment: e.target.value })} /></div>
          <button style={buttonStyle} type="submit">Add</button>
        </form>
        {err && <p style={{ color: "#f87171", fontSize: 13 }}>{err}</p>}
      </Card>

      <Card title={`Risk register (${risks.length})`}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>ID</th><th style={thStyle}>Title</th>
              <th style={thStyle}>L×I</th><th style={thStyle}>Framework</th>
              <th style={thStyle}>Status</th>
            </tr>
          </thead>
          <tbody>
            {risks.map((r) => (
              <tr key={r.id}>
                <td style={tdStyle}>{r.id}</td><td style={tdStyle}>{r.title}</td>
                <td style={tdStyle}>{r.likelihood} × {r.impact} = {r.likelihood * r.impact}</td>
                <td style={tdStyle}>{r.framework || "-"}</td>
                <td style={tdStyle}>{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Ad-hoc AI risk score (calls /api/risk/score → AI Engine)">
        <form onSubmit={score} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr auto", gap: 12, alignItems: "flex-end" }}>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>User</label>
            <input style={inputStyle} value={scoreInput.user}
              onChange={(e) => setScoreInput({ ...scoreInput, user: e.target.value })} /></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Activity</label>
            <input style={inputStyle} value={scoreInput.activity}
              onChange={(e) => setScoreInput({ ...scoreInput, activity: e.target.value })} /></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>IP</label>
            <input style={inputStyle} value={scoreInput.ip}
              onChange={(e) => setScoreInput({ ...scoreInput, ip: e.target.value })} /></div>
          <div><label style={{ color: "#94a3b8", fontSize: 13 }}>Bytes</label>
            <input style={inputStyle} type="number" value={scoreInput.bytes_transferred}
              onChange={(e) => setScoreInput({ ...scoreInput, bytes_transferred: +e.target.value })} /></div>
          <button style={buttonStyle} type="submit">Score</button>
        </form>
        {scoreResult && (
          <pre style={{
            marginTop: 16, background: "#0f172a", padding: 12, borderRadius: 4,
            fontSize: 12, color: "#a7f3d0", overflow: "auto",
          }}>{JSON.stringify(scoreResult, null, 2)}</pre>
        )}
      </Card>
    </>
  );
}
