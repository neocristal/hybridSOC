import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import { api, auth } from "./api.js";
import Login from "./pages/Login.jsx";
import MFA from "./pages/MFA.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Users from "./pages/Users.jsx";
import RiskRegister from "./pages/RiskRegister.jsx";
import Incidents from "./pages/Incidents.jsx";
import AuditLog from "./pages/AuditLog.jsx";

const navStyle = {
  display: "flex",
  gap: 16,
  padding: "12px 24px",
  background: "#1e293b",
  borderBottom: "1px solid #334155",
  alignItems: "center",
};
const linkStyle = { color: "#cbd5e1", textDecoration: "none", fontSize: 14 };
const linkActive = { ...linkStyle, color: "#60a5fa", fontWeight: 600 };
const containerStyle = { maxWidth: 1200, margin: "0 auto", padding: 24 };

function NavBar({ user, onLogout }) {
  return (
    <nav style={navStyle}>
      <strong style={{ color: "#f1f5f9", marginRight: 24 }}>HybridSOC</strong>
      <Link to="/dashboard" style={linkStyle}>Dashboard</Link>
      <Link to="/risks" style={linkStyle}>Risk Register</Link>
      <Link to="/incidents" style={linkStyle}>Incidents</Link>
      {(user?.role === "admin" || user?.role === "superadmin") && (
        <>
          <Link to="/users" style={linkStyle}>Users</Link>
          <Link to="/audit" style={linkStyle}>Audit Log</Link>
        </>
      )}
      <span style={{ flex: 1 }} />
      <span style={{ color: "#94a3b8", fontSize: 13 }}>
        {user?.email} ({user?.role})
      </span>
      <button onClick={onLogout} style={{
        marginLeft: 12, padding: "4px 12px", background: "#334155",
        color: "#e2e8f0", border: 0, borderRadius: 4, cursor: "pointer",
      }}>Logout</button>
    </nav>
  );
}

function RequireAuth({ user, children }) {
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [bootstrapped, setBootstrapped] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!auth.token) { setBootstrapped(true); return; }
    api("/api/auth/me").then(setUser).catch(() => auth.clear()).finally(() => setBootstrapped(true));
  }, []);

  const onLogout = async () => {
    try { await api("/api/auth/logout", { method: "POST" }); } catch {}
    auth.clear(); setUser(null); navigate("/login");
  };

  if (!bootstrapped) return <div style={{ padding: 24 }}>Loading…</div>;

  return (
    <div style={{ minHeight: "100vh" }}>
      {user && <NavBar user={user} onLogout={onLogout} />}
      <div style={containerStyle}>
        <Routes>
          <Route path="/login" element={<Login onLogged={(u) => { setUser(u); navigate("/dashboard"); }} />} />
          <Route path="/mfa" element={<MFA onLogged={(u) => { setUser(u); navigate("/dashboard"); }} />} />
          <Route path="/dashboard" element={<RequireAuth user={user}><Dashboard /></RequireAuth>} />
          <Route path="/risks" element={<RequireAuth user={user}><RiskRegister /></RequireAuth>} />
          <Route path="/incidents" element={<RequireAuth user={user}><Incidents /></RequireAuth>} />
          <Route path="/users" element={<RequireAuth user={user}><Users /></RequireAuth>} />
          <Route path="/audit" element={<RequireAuth user={user}><AuditLog /></RequireAuth>} />
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </div>
    </div>
  );
}

export { linkStyle, linkActive };
