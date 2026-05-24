import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, auth } from "../api.js";
import Card, { inputStyle, buttonStyle } from "../components/Card.jsx";

export default function MFA() {
  const navigate = useNavigate();
  const pending = JSON.parse(sessionStorage.getItem("hybridsoc.pending") || "null");
  const [method, setMethod] = useState(pending?.totp_enabled ? "google_totp" : "email_otp");
  const [code, setCode] = useState("");
  const [info, setInfo] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => { if (!pending) navigate("/login"); }, [pending, navigate]);

  const sendChallenge = async () => {
    setInfo(""); setErr("");
    try {
      const r = await api("/api/auth/mfa/challenge", {
        method: "POST",
        body: { user_id: pending.user_id, method },
      });
      setInfo(r.method === "email_otp"
        ? `Code sent to ${r.sent_to}.`
        : "Open your authenticator and enter the current 6-digit code.");
    } catch (e) { setErr(e.message); }
  };

  const verify = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const r = await api("/api/auth/mfa/verify", {
        method: "POST",
        body: { user_id: pending.user_id, method, code },
      });
      auth.token = r.access_token;
      sessionStorage.removeItem("hybridsoc.pending");
      navigate("/dashboard");
      window.location.reload();
    } catch (e) { setErr(e.message); }
  };

  if (!pending) return null;

  return (
    <div style={{ maxWidth: 420, margin: "80px auto" }}>
      <Card title="Multi-factor authentication">
        <p style={{ color: "#94a3b8", fontSize: 13, marginTop: 0 }}>
          Verifying <strong style={{ color: "#e2e8f0" }}>{pending.email}</strong>
        </p>
        <label style={{ display: "block", color: "#94a3b8", fontSize: 13, marginBottom: 4 }}>Method</label>
        <select style={inputStyle} value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="email_otp">Email OTP</option>
          {pending.totp_enabled && <option value="google_totp">Google Authenticator (TOTP)</option>}
        </select>
        <div style={{ height: 12 }} />
        {method === "email_otp" && (
          <button style={{ ...buttonStyle, background: "#475569" }} type="button" onClick={sendChallenge}>
            Send code
          </button>
        )}
        <form onSubmit={verify} style={{ marginTop: 16 }}>
          <label style={{ display: "block", color: "#94a3b8", fontSize: 13, marginBottom: 4 }}>6-digit code</label>
          <input style={inputStyle} required pattern="[0-9]{6}" inputMode="numeric"
            value={code} onChange={(e) => setCode(e.target.value)} />
          {info && <p style={{ color: "#34d399", fontSize: 13, marginTop: 12 }}>{info}</p>}
          {err && <p style={{ color: "#f87171", fontSize: 13, marginTop: 12 }}>{err}</p>}
          <div style={{ height: 12 }} />
          <button style={buttonStyle} type="submit">Verify</button>
        </form>
      </Card>
    </div>
  );
}
