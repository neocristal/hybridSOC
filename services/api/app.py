"""
HybridSOC Admin + Analytics API
Suggested implementation pattern for backend admin modules, integrations,
and dashboard data feeds.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Literal
import time
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(
    title="HybridSOC Admin + Dashboard API",
    version="1.0.0",
    description=(
        "Admin modules (users, tenants, RBAC, incidents), API management, "
        "connector health checks, and dashboard security metrics."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="services/api/static"), name="static")


# ── In-memory data stores (replace with persistent DB in production) ─────────
users: dict[str, dict] = {}
tenants: dict[str, dict] = {}
roles: dict[str, dict] = {}
incidents: dict[str, dict] = {}
audit_trail: list[dict] = []

# rate limit tracking: api key -> timestamps
rate_buckets: dict[str, deque] = defaultdict(deque)

connectors = {
    "wazuh": {"type": "siem", "last_sync": "2026-04-24T00:00:00Z", "latency_ms": 92},
    "thehive": {"type": "soar", "last_sync": "2026-04-24T00:00:00Z", "latency_ms": 145},
    "misp": {"type": "threat_intel", "last_sync": "2026-04-24T00:00:00Z", "latency_ms": 111},
    "opencti": {"type": "threat_intel", "last_sync": "2026-04-24T00:00:00Z", "latency_ms": 170},
}


# ── Models ────────────────────────────────────────────────────────────────────
class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    region: str = Field(default="eu-west-1")


class UserCreate(BaseModel):
    email: str
    tenant_id: str
    display_name: str
    role_ids: list[str] = Field(default_factory=list)


class RoleCreate(BaseModel):
    name: str
    permissions: list[str] = Field(default_factory=list)


class IncidentCreate(BaseModel):
    tenant_id: str
    title: str = Field(min_length=5)
    severity: Literal["low", "medium", "high", "critical"]
    source: str


class IncidentTransition(BaseModel):
    state: Literal["new", "triage", "investigating", "contained", "closed"]
    note: str = Field(default="")


# ── API security, validation, and audit helpers ──────────────────────────────
def _audit(event: str, actor: str, details: dict | None = None) -> None:
    audit_trail.append(
        {
            "id": str(uuid.uuid4()),
            "event": event,
            "actor": actor,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def _token_from_header(auth_header: str | None) -> str:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = auth_header.replace("Bearer ", "", 1).strip()
    if token != "hybridsoc-admin-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token


async def require_auth(authorization: str | None = Header(default=None)) -> str:
    return _token_from_header(authorization)


@app.middleware("http")
async def rate_limit_and_validate(request: Request, call_next):
    # health/docs/static are exempt to keep onboarding smooth
    exempt_prefixes = ("/health", "/docs", "/openapi.json", "/static", "/dashboard")
    if request.url.path.startswith(exempt_prefixes):
        return await call_next(request)

    # token presence check at middleware for gateway-like enforcement
    auth = request.headers.get("authorization")
    token = _token_from_header(auth)

    # simple fixed-window limit: 60 requests/min per token
    window = 60
    limit = 60
    now = time.time()
    bucket = rate_buckets[token]
    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= limit:
        _audit("rate_limit_exceeded", actor="gateway", details={"path": request.url.path})
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    bucket.append(now)
    response = await call_next(request)
    return response


# ── System and control-plane endpoints ────────────────────────────────────────
@app.get("/health", tags=["System"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "admin-api",
        "version": "1.0.0",
        "token_validation": "enabled",
        "s2s_trust_policy": "zero-trust-baseline",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/control-plane/observability", tags=["Control Plane"], dependencies=[Depends(require_auth)])
def observability_overview() -> dict:
    connector_total = len(connectors)
    degraded = sum(1 for c in connectors.values() if c["latency_ms"] > 150)
    unreachable = 0
    return {
        "gateway_enforcement": "active",
        "token_validation": "active",
        "service_to_service_trust": "mTLS-intended",
        "connection_reliability_pct": round(((connector_total - degraded - unreachable) / connector_total) * 100, 2),
        "degraded_connections": degraded,
        "failed_connections": unreachable,
        "last_evaluated": datetime.now(timezone.utc).isoformat(),
    }


# ── Admin modules ─────────────────────────────────────────────────────────────
@app.post("/admin/tenants", tags=["Admin"], dependencies=[Depends(require_auth)])
def create_tenant(payload: TenantCreate):
    tenant_id = f"ten-{uuid.uuid4().hex[:8]}"
    tenants[tenant_id] = {"id": tenant_id, **payload.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    _audit("tenant_created", actor="admin", details={"tenant_id": tenant_id})
    return tenants[tenant_id]


@app.post("/admin/rbac/roles", tags=["Admin"], dependencies=[Depends(require_auth)])
def create_role(payload: RoleCreate):
    role_id = f"rol-{uuid.uuid4().hex[:8]}"
    roles[role_id] = {"id": role_id, **payload.model_dump()}
    _audit("role_created", actor="admin", details={"role_id": role_id})
    return roles[role_id]


@app.post("/admin/users", tags=["Admin"], dependencies=[Depends(require_auth)])
def create_user(payload: UserCreate):
    if payload.tenant_id not in tenants:
        raise HTTPException(status_code=404, detail="Tenant not found")
    unknown_roles = [r for r in payload.role_ids if r not in roles]
    if unknown_roles:
        raise HTTPException(status_code=400, detail=f"Unknown roles: {unknown_roles}")

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    users[user_id] = {"id": user_id, **payload.model_dump(), "status": "active"}
    _audit("user_created", actor="admin", details={"user_id": user_id})
    return users[user_id]


@app.get("/admin/audit", tags=["Admin"], dependencies=[Depends(require_auth)])
def list_audit(limit: int = 50):
    return {"items": audit_trail[-limit:]}


@app.post("/cases/incidents", tags=["Cases"], dependencies=[Depends(require_auth)])
def create_incident(payload: IncidentCreate):
    if payload.tenant_id not in tenants:
        raise HTTPException(status_code=404, detail="Tenant not found")
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    incidents[incident_id] = {
        "id": incident_id,
        **payload.model_dump(),
        "state": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "history": [],
    }
    _audit("incident_created", actor="analyst", details={"incident_id": incident_id})
    return incidents[incident_id]


@app.post("/cases/incidents/{incident_id}/transition", tags=["Cases"], dependencies=[Depends(require_auth)])
def transition_incident(incident_id: str, payload: IncidentTransition):
    incident = incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    previous = incident["state"]
    incident["state"] = payload.state
    incident["history"].append(
        {
            "from": previous,
            "to": payload.state,
            "note": payload.note,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    _audit("incident_transition", actor="analyst", details={"incident_id": incident_id, "to": payload.state})
    return incident


# ── Integration and health-check endpoints ────────────────────────────────────
@app.get("/integrations/health", tags=["Integrations"], dependencies=[Depends(require_auth)])
def integration_health_check():
    now = datetime.now(timezone.utc)
    results = []
    for name, meta in connectors.items():
        age_minutes = int((now - datetime.fromisoformat(meta["last_sync"].replace("Z", "+00:00"))).total_seconds() / 60)
        status_value = "healthy"
        if meta["latency_ms"] > 160 or age_minutes > 30:
            status_value = "degraded"
        results.append(
            {
                "connector": name,
                "type": meta["type"],
                "status": status_value,
                "latency_ms": meta["latency_ms"],
                "last_sync": meta["last_sync"],
                "sync_delay_minutes": age_minutes,
            }
        )
    _audit("integration_health_queried", actor="system")
    return {"items": results}


# ── Dashboard UI + metrics feed ───────────────────────────────────────────────
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard_page():
    with open("services/api/static/dashboard.html", "r", encoding="utf-8") as handle:
        return HTMLResponse(handle.read())


@app.get("/dashboard/metrics", tags=["Dashboard"], dependencies=[Depends(require_auth)])
def dashboard_metrics():
    severity_distribution = {
        "critical": 7,
        "high": 18,
        "medium": 34,
        "low": 22,
    }
    mttr_hours = [6.8, 6.1, 5.4, 5.0, 4.7, 4.5]
    detection_coverage_pct = [72, 74, 77, 79, 82, 84]
    trend = [52, 49, 60, 58, 63, 55, 48]
    risk_heatmap = [
        {"domain": "Identity", "risk": 0.81},
        {"domain": "Endpoint", "risk": 0.62},
        {"domain": "Cloud", "risk": 0.73},
        {"domain": "Network", "risk": 0.58},
    ]

    connector_status = []
    for name, meta in connectors.items():
        connector_status.append(
            {
                "name": name,
                "type": meta["type"],
                "status": "connected" if meta["latency_ms"] <= 160 else "degraded",
                "latency_ms": meta["latency_ms"],
                "sync_lag_seconds": int((meta["latency_ms"] / 10) + 2),
            }
        )

    return {
        "period": "last_7_days",
        "alerts_by_severity": severity_distribution,
        "mttr_hours": mttr_hours,
        "detection_coverage": detection_coverage_pct,
        "trend_line_alerts": trend,
        "risk_heatmap": risk_heatmap,
        "incident_distribution": [
            {"stage": "new", "count": 9},
            {"stage": "triage", "count": 11},
            {"stage": "investigating", "count": 8},
            {"stage": "contained", "count": 5},
            {"stage": "closed", "count": 14},
        ],
        "operational_status": connector_status,
        "sync_success_rate_pct": 98.6,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/dashboard/architecture", tags=["Dashboard"], dependencies=[Depends(require_auth)])
def architecture_chain():
    return {
        "flow": [
            "Users / Devices",
            "IAM (Keycloak SSO + MFA + HashiCorp Vault PAM)",
            "Zero Trust Gateway (NIST SP 800-207)",
            "Network Security Layer (OPNsense, Suricata, Zeek)",
            "Telemetry Collection (Kafka streaming backbone)",
            "SIEM (Wazuh + Elastic Stack)",
            "Threat Intelligence (MISP + OpenCTI)",
            "AI Analytics Engine (FastAPI + ML pipeline)",
            "SOAR (TheHive + Cortex + Shuffle)",
            "GRC Layer (ISO 27001 / DORA / NIS2 / EU AI Act / GDPR)",
            "Incident Response & Compliance Reporting",
        ]
    }
