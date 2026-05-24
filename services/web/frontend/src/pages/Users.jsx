import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import Card, { buttonStyle, inputStyle, tableStyle, tdStyle, thStyle } from "../components/Card.jsx";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ email: "", password: "", role: "analyst" });
  const [err, setErr] = useState("");

  const load = () => api("/api/admin/users").then(setUsers).catch((e) => setErr(e.message));
  useEffect(load, []);

  const create = async (e) => {
    e.preventDefault(); setErr("");
    try { await api("/api/admin/users", { method: "POST", body: form });
      setForm({ email: "", password: "", role: "analyst" }); load();
    } catch (e) { setErr(e.message); }
  };

  const toggle = async (u) => {
    await api(`/api/admin/users/${u.id}`, { method: "PATCH", body: { active: u.active ? 0 : 1 } });
    load();
  };

  return (
    <>
      <Card title="Create user">
        <form onSubmit={create} style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
          <div style={{ flex: 2 }}>
            <label style={{ color: "#94a3b8", fontSize: 13 }}>Email</label>
            <input style={inputStyle} type="email" required
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div style={{ flex: 2 }}>
            <label style={{ color: "#94a3b8", fontSize: 13 }}>Password</label>
            <input style={inputStyle} type="password" required minLength={10}
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ color: "#94a3b8", fontSize: 13 }}>Role</label>
            <select style={inputStyle} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="analyst">analyst</option>
              <option value="manager">manager</option>
              <option value="compliance">compliance</option>
              <option value="admin">admin</option>
              <option value="superadmin">superadmin</option>
            </select>
          </div>
          <button style={buttonStyle} type="submit">Create</button>
        </form>
        {err && <p style={{ color: "#f87171", fontSize: 13 }}>{err}</p>}
      </Card>

      <Card title={`Users (${users.length})`}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>ID</th><th style={thStyle}>Email</th>
              <th style={thStyle}>Role</th><th style={thStyle}>TOTP</th>
              <th style={thStyle}>Active</th><th style={thStyle}></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td style={tdStyle}>{u.id}</td><td style={tdStyle}>{u.email}</td>
                <td style={tdStyle}>{u.role}</td>
                <td style={tdStyle}>{u.totp_enabled ? "yes" : "no"}</td>
                <td style={tdStyle}>{u.active ? "yes" : "no"}</td>
                <td style={tdStyle}>
                  <button onClick={() => toggle(u)} style={{ ...buttonStyle, background: "#475569" }}>
                    {u.active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
