import React from "react";

export default function Card({ title, children, style }) {
  return (
    <div style={{
      background: "#1e293b",
      border: "1px solid #334155",
      borderRadius: 8,
      padding: 20,
      marginBottom: 20,
      ...style,
    }}>
      {title && <h3 style={{ marginTop: 0, color: "#f1f5f9", fontSize: 16 }}>{title}</h3>}
      {children}
    </div>
  );
}

export const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: 14,
};

export const thStyle = {
  textAlign: "left",
  padding: "8px 12px",
  borderBottom: "1px solid #475569",
  color: "#94a3b8",
  fontWeight: 600,
};

export const tdStyle = {
  padding: "8px 12px",
  borderBottom: "1px solid #334155",
  color: "#e2e8f0",
};

export const inputStyle = {
  background: "#0f172a",
  color: "#e2e8f0",
  border: "1px solid #334155",
  borderRadius: 4,
  padding: "8px 12px",
  fontSize: 14,
  width: "100%",
  boxSizing: "border-box",
};

export const buttonStyle = {
  background: "#2563eb",
  color: "white",
  border: 0,
  borderRadius: 4,
  padding: "8px 16px",
  fontSize: 14,
  cursor: "pointer",
};
