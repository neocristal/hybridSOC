import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api.js";
import Card, { inputStyle, buttonStyle } from "../components/Card.jsx";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", turnstile_token: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const result = await api("/api/auth/login", { method: "POST", body: form });
      sessionStorage.setItem("hybridsoc.pending", JSON.stringify(result));
      navigate("/mfa");
    } catch (e) {
      setErr(e.message || "Login failed");
    } finally { setBusy(false); }
  };

  return (
    <div style={{ maxWidth: 420, margin: "80px auto" }}>
      <Card title="Sign in to HybridSOC">
        <form onSubmit={submit}>
          <label style={{ display: "block", color: "#94a3b8", fontSize: 13, marginBottom: 4 }}>Email</label>
          <input style={inputStyle} type="email" required autoFocus
            value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <div style={{ height: 12 }} />
          <label style={{ display: "block", color: "#94a3b8", fontSize: 13, marginBottom: 4 }}>Password</label>
          <input style={inputStyle} type="password" required
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <div style={{ height: 12 }} />
          <label style={{ display: "block", color: "#94a3b8", fontSize: 13, marginBottom: 4 }}>
            Turnstile token (optional in dev)
          </label>
          <input style={inputStyle} type="text"
            value={form.turnstile_token} onChange={(e) => setForm({ ...form, turnstile_token: e.target.value })} />
          {err && <p style={{ color: "#f87171", fontSize: 13, marginTop: 12 }}>{err}</p>}
          <div style={{ height: 16 }} />
          <button style={buttonStyle} disabled={busy} type="submit">
            {busy ? "Signing in…" : "Continue"}
          </button>
        </form>
      </Card>
    </div>
  );
}
