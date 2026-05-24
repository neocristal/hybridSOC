import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import Card, { buttonStyle, tableStyle, tdStyle, thStyle } from "../components/Card.jsx";

export default function AuditLog() {
  const [rows, setRows] = useState([]);
  const [verify, setVerify] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api("/api/audit/?limit=200").then(setRows).catch((e) => setErr(e.message));
  useEffect(load, []);

  const runVerify = async () => {
    try { setVerify(await api("/api/audit/verify")); }
    catch (e) { setErr(e.message); }
  };

  return (
    <>
      <Card title="Hash chain integrity">
        <button style={buttonStyle} onClick={runVerify}>Verify chain</button>
        {verify && (
          <p style={{ marginTop: 12, color: verify.ok ? "#34d399" : "#f87171" }}>
            {verify.ok
              ? "Chain valid — no tampering detected."
              : `Chain BROKEN at row id=${verify.first_bad_id}`}
          </p>
        )}
        {err && <p style={{ color: "#f87171", fontSize: 13 }}>{err}</p>}
      </Card>

      <Card title={`Audit log (most recent ${rows.length})`}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>ID</th><th style={thStyle}>Timestamp</th>
              <th style={thStyle}>User</th><th style={thStyle}>Action</th>
              <th style={thStyle}>Details</th><th style={thStyle}>IP</th>
              <th style={thStyle}>Row hash</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td style={tdStyle}>{r.id}</td>
                <td style={tdStyle}>{r.timestamp}</td>
                <td style={tdStyle}>{r.user_id ?? "-"}</td>
                <td style={tdStyle}>{r.action}</td>
                <td style={{ ...tdStyle, fontSize: 12, color: "#94a3b8" }}>{r.details}</td>
                <td style={tdStyle}>{r.ip_address || "-"}</td>
                <td style={{ ...tdStyle, fontFamily: "monospace", fontSize: 11 }}>
                  {r.row_hash?.slice(0, 12)}…
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
