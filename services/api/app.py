"""
HybridSOC Admin + Analytics API
SQLite-backed IAM/authentication + admin/control-plane endpoints.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Literal
import base64
import hashlib
import hmac
import struct
import os
import secrets
import smtplib
import sqlite3
import time
import uuid

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

load_dotenv(Path(__file__).resolve().parent / ".env")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "hybridsoc.db"))

SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", "superadmin@hybridsoc.example.com")
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "ChangeMeNow!123")
ACCESS_TOKEN_TTL_MINUTES = int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "60"))
PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "310000"))
PBKDF2_SALT_BYTES = 16

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@hybridsoc.local")
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() == "true"

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_ROLE = os.getenv("VAULT_ROLE", "hybridsoc-pam")
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "hybridsoc")

app = FastAPI(
    title="HybridSOC Admin + Dashboard API",
    version="2.0.0",
    description="IAM-backed admin API with SQLite, MFA, SMTP OTP delivery, and dashboard feeds.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

rate_buckets: dict[str, deque] = defaultdict(deque)
sessions: dict[str, dict] = {}
pending_logins: dict[str, dict] = {}
audit_trail: list[dict] = []

connectors = {
    "wazuh": {"type": "siem", "last_sync": "2026-04-24T00:00:00Z", "latency_ms": 92},
    "thehive": {"type": "soar", "last_sync": "2026-04-24T00:00:00Z", "latency_ms": 145},
    "misp": {"type": "threat_intel", "last_sync": "2026-04-24T00:00:00Z", "latency_ms": 111},
    "opencti": {"type": "threat_intel", "last_sync": "2026-04-24T00:00:00Z", "latency_ms": 170},
}


# ── Models ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MFAChallengeRequest(BaseModel):
    pending_token: str
    method: Literal["email_otp", "google_totp"]


class MFAVerifyRequest(BaseModel):
    pending_token: str
    otp_code: str = Field(min_length=6, max_length=8)


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    region: str = Field(default="eu-west-1")


class RoleCreate(BaseModel):
    name: str
    permissions: list[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    email: EmailStr
    tenant_id: str
    display_name: str
    role: Literal["superadmin", "admin", "analyst", "viewer"] = "analyst"
    password: str = Field(min_length=10)
    mfa_method: Literal["email_otp", "google_totp"] = "email_otp"


class IncidentCreate(BaseModel):
    tenant_id: str
    title: str = Field(min_length=5)
    severity: Literal["low", "medium", "high", "critical"]
    source: str


class IncidentTransition(BaseModel):
    state: Literal["new", "triage", "investigating", "contained", "closed"]
    note: str = Field(default="")


# ── DB and utility helpers ────────────────────────────────────────────────────
def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(raw: str) -> str:
    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(raw: str, stored: str) -> bool:
    try:
        algorithm, iterations_str, salt_b64, digest_b64 = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
    except (ValueError, TypeError):
        return False

    computed = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(computed, expected)


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").replace("=", "")


def _totp_code(secret: str, for_time: int | None = None, interval: int = 30) -> str:
    if for_time is None:
        for_time = int(time.time())
    key = base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8), casefold=True)
    counter = int(for_time / interval)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = ((digest[offset] & 0x7F) << 24) | ((digest[offset + 1] & 0xFF) << 16) | ((digest[offset + 2] & 0xFF) << 8) | (digest[offset + 3] & 0xFF)
    return str(binary % 1000000).zfill(6)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    now = int(time.time())
    for w in range(-window, window + 1):
        if _totp_code(secret, for_time=now + (w * 30)) == code:
            return True
    return False


def totp_provisioning_uri(email: str, secret: str, issuer: str = "HybridSOC") -> str:
    return f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"

# ── API security, validation, and audit helpers ──────────────────────────────
def _audit(event: str, actor: str, details: dict | None = None) -> None:
    audit_trail.append(
        {
            "id": str(uuid.uuid4()),
            "event": event,
            "actor": actor,
            "details": details or {},
            "timestamp": now_utc(),
        }
    )


def send_email_otp(to_email: str, otp_code: str) -> None:
    msg = MIMEText(f"Your HybridSOC OTP code is: {otp_code}. It expires in 5 minutes.")
    msg["Subject"] = "HybridSOC MFA OTP"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        if SMTP_TLS:
            server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_email], msg.as_string())


def vault_sync_user(user_row: sqlite3.Row) -> dict:
    # Placeholder hook: replace with hvac calls in production.
    return {
        "vault_addr": VAULT_ADDR,
        "vault_role": VAULT_ROLE,
        "status": "queued",
        "user": user_row["email"],
    }


def keycloak_sync_user(user_row: sqlite3.Row) -> dict:
    # Placeholder hook: replace with Keycloak Admin API integration in production.
    return {
        "keycloak_url": KEYCLOAK_URL,
        "realm": KEYCLOAK_REALM,
        "status": "queued",
        "user": user_row["email"],
    }


def init_db() -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tenants (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          region TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY,
          email TEXT UNIQUE NOT NULL,
          display_name TEXT NOT NULL,
          tenant_id TEXT NOT NULL,
          role TEXT NOT NULL,
          password_hash TEXT NOT NULL,
          mfa_method TEXT NOT NULL,
          totp_secret TEXT,
          is_active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
          id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          title TEXT NOT NULL,
          severity TEXT NOT NULL,
          source TEXT NOT NULL,
          state TEXT NOT NULL,
          created_at TEXT NOT NULL,
          history_json TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mfa_codes (
          id TEXT PRIMARY KEY,
          user_id TEXT NOT NULL,
          code_hash TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          consumed INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    tenant_id = "ten-root"
    cur.execute("INSERT OR IGNORE INTO tenants(id,name,region,created_at) VALUES(?,?,?,?)", (tenant_id, "HybridSOC Root", "global", now_utc()))

    superadmin_id = "usr-superadmin"
    cur.execute(
        """
        INSERT INTO users(id,email,display_name,tenant_id,role,password_hash,mfa_method,totp_secret,is_active,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
          email=excluded.email,
          display_name=excluded.display_name,
          tenant_id=excluded.tenant_id,
          role=excluded.role,
          password_hash=excluded.password_hash,
          mfa_method=excluded.mfa_method,
          is_active=1
        """,
        (
            superadmin_id,
            SUPERADMIN_EMAIL,
            "HybridSOC Superadmin",
            tenant_id,
            "superadmin",
            hash_password(SUPERADMIN_PASSWORD),
            "google_totp",
            generate_totp_secret(),
            1,
            now_utc(),
        ),
    )
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup() -> None:
    init_db()


# ── Auth/access control ───────────────────────────────────────────────────────
def require_role(roles: set[str]):
    async def checker(authorization: str | None = Header(default=None)) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")
        token = authorization.replace("Bearer ", "", 1).strip()
        session = sessions.get(token)
        if not session or session["expires_at"] < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        if session["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return session

    return checker


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    exempt_prefixes = ("/health", "/docs", "/openapi.json", "/static", "/dashboard", "/auth")
    if request.url.path.startswith(exempt_prefixes):
        return await call_next(request)

    auth = request.headers.get("authorization", "")
    token = auth.replace("Bearer ", "", 1).strip() if auth.startswith("Bearer ") else request.client.host

    window, limit = 60, 120
    now = time.time()
    bucket = rate_buckets[token]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)
    return await call_next(request)


# ── IAM/authentication endpoints ──────────────────────────────────────────────
@app.post("/auth/login", tags=["Auth"])
def login(payload: LoginRequest):
    conn = db_connect()
    user = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (payload.email.lower(),)).fetchone()
    conn.close()
    if not user or not verify_password(payload.password, user["password_hash"]):
        _audit("login_failed", actor=payload.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    pending_token = secrets.token_urlsafe(24)
    pending_logins[pending_token] = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "tenant_id": user["tenant_id"],
        "mfa_method": user["mfa_method"],
        "totp_secret": user["totp_secret"],
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    _audit("login_password_verified", actor=user["email"])
    return {
        "pending_token": pending_token,
        "mfa_options": ["email_otp", "google_totp"],
        "preferred_mfa": user["mfa_method"],
    }


@app.post("/auth/mfa/challenge", tags=["Auth"])
def mfa_challenge(payload: MFAChallengeRequest):
    ctx = pending_logins.get(payload.pending_token)
    if not ctx or ctx["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Pending login expired")

    if payload.method == "email_otp":
        otp_code = f"{secrets.randbelow(900000) + 100000}"
        conn = db_connect()
        conn.execute(
            "INSERT INTO mfa_codes(id,user_id,code_hash,expires_at,consumed) VALUES(?,?,?,?,0)",
            (str(uuid.uuid4()), ctx["user_id"], hash_password(otp_code), (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()),
        )
        conn.commit()
        conn.close()
        send_email_otp(ctx["email"], otp_code)
        _audit("mfa_challenge_email_sent", actor=ctx["email"])
        return {"status": "sent", "method": "email_otp"}

    # google_totp enrollment/verification path
    if not ctx.get("totp_secret"):
        new_secret = generate_totp_secret()
        ctx["totp_secret"] = new_secret
        conn = db_connect()
        conn.execute("UPDATE users SET totp_secret = ? WHERE id = ?", (new_secret, ctx["user_id"]))
        conn.commit()
        conn.close()

    uri = totp_provisioning_uri(ctx["email"], ctx["totp_secret"])
    _audit("mfa_challenge_totp", actor=ctx["email"])
    return {"status": "ready", "method": "google_totp", "otpauth_uri": uri}


@app.post("/auth/mfa/verify", tags=["Auth"])
def mfa_verify(payload: MFAVerifyRequest):
    ctx = pending_logins.get(payload.pending_token)
    if not ctx or ctx["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Pending login expired")

    verified = False

    # Try TOTP first
    secret = ctx.get("totp_secret")
    if secret and verify_totp(secret, payload.otp_code, window=1):
        verified = True

    # Fallback: check email OTP table
    if not verified:
        conn = db_connect()
        row = conn.execute(
            """
            SELECT * FROM mfa_codes
            WHERE user_id = ? AND consumed = 0
            ORDER BY expires_at DESC LIMIT 1
            """,
            (ctx["user_id"],),
        ).fetchone()
        if row and row["expires_at"] > datetime.now(timezone.utc).isoformat() and row["code_hash"] == hash_password(payload.otp_code):
            conn.execute("UPDATE mfa_codes SET consumed = 1 WHERE id = ?", (row["id"],))
            conn.commit()
            verified = True
        conn.close()

    if not verified:
        _audit("mfa_verify_failed", actor=ctx["email"])
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    access_token = secrets.token_urlsafe(32)
    sessions[access_token] = {
        "user_id": ctx["user_id"],
        "email": ctx["email"],
        "role": ctx["role"],
        "tenant_id": ctx["tenant_id"],
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES),
    }
    pending_logins.pop(payload.pending_token, None)
    _audit("login_success", actor=ctx["email"])
    return {"access_token": access_token, "token_type": "bearer", "expires_in_minutes": ACCESS_TOKEN_TTL_MINUTES}


@app.get("/auth/me", tags=["Auth"])
def auth_me(session=Depends(require_role({"superadmin", "admin", "analyst", "viewer"}))):
    return {k: v for k, v in session.items() if k != "expires_at"}


# ── Core endpoints ────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "admin-api",
        "version": "2.0.0",
        "iam": {
            "vault": VAULT_ADDR,
            "keycloak": f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}",
        },
        "timestamp": now_utc(),
    }


@app.get("/control-plane/observability", tags=["Control Plane"], dependencies=[Depends(require_role({"superadmin", "admin"}))])
def observability_overview() -> dict:
    connector_total = len(connectors)
    degraded = sum(1 for c in connectors.values() if c["latency_ms"] > 150)
    return {
        "gateway_enforcement": "active",
        "token_validation": "active",
        "service_to_service_trust": "zero-trust-baseline",
        "connection_reliability_pct": round(((connector_total - degraded) / connector_total) * 100, 2),
        "degraded_connections": degraded,
        "failed_connections": 0,
        "last_evaluated": now_utc(),
    }


@app.post("/admin/tenants", tags=["Admin"], dependencies=[Depends(require_role({"superadmin"}))])
def create_tenant(payload: TenantCreate):
    tenant_id = f"ten-{uuid.uuid4().hex[:8]}"
    conn = db_connect()
    conn.execute("INSERT INTO tenants(id,name,region,created_at) VALUES(?,?,?,?)", (tenant_id, payload.name, payload.region, now_utc()))
    conn.commit()
    conn.close()
    _audit("tenant_created", actor="superadmin", details={"tenant_id": tenant_id})
    return {"id": tenant_id, **payload.model_dump()}


@app.post("/admin/users", tags=["Admin"], dependencies=[Depends(require_role({"superadmin", "admin"}))])
def create_user(payload: UserCreate, session=Depends(require_role({"superadmin", "admin"}))):
    # Admin can only create users inside same tenant unless superadmin
    if session["role"] != "superadmin" and payload.tenant_id != session["tenant_id"]:
        raise HTTPException(status_code=403, detail="Admins can only manage their own tenant")

    conn = db_connect()
    tenant = conn.execute("SELECT id FROM tenants WHERE id = ?", (payload.tenant_id,)).fetchone()
    if not tenant:
        conn.close()
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    totp_secret = generate_totp_secret() if payload.mfa_method == "google_totp" else None
    conn.execute(
        """
        INSERT INTO users(id,email,display_name,tenant_id,role,password_hash,mfa_method,totp_secret,is_active,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (
            user_id,
            payload.email.lower(),
            payload.display_name,
            payload.tenant_id,
            payload.role,
            hash_password(payload.password),
            payload.mfa_method,
            totp_secret,
            1,
            now_utc(),
        ),
    )
    created_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.commit()
    conn.close()

    _audit("user_created", actor=session["email"], details={"user_id": user_id, "role": payload.role})
    return {
        "id": user_id,
        "email": payload.email,
        "display_name": payload.display_name,
        "tenant_id": payload.tenant_id,
        "role": payload.role,
        "mfa_method": payload.mfa_method,
        "vault_sync": vault_sync_user(created_user),
        "keycloak_sync": keycloak_sync_user(created_user),
    }


@app.get("/admin/audit", tags=["Admin"], dependencies=[Depends(require_role({"superadmin", "admin"}))])
def list_audit(limit: int = 100):
    return {"items": audit_trail[-limit:]}


@app.post("/cases/incidents", tags=["Cases"], dependencies=[Depends(require_role({"superadmin", "admin", "analyst"}))])
def create_incident(payload: IncidentCreate):
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    conn = db_connect()
    conn.execute(
        "INSERT INTO incidents(id,tenant_id,title,severity,source,state,created_at,history_json) VALUES(?,?,?,?,?,?,?,?)",
        (incident_id, payload.tenant_id, payload.title, payload.severity, payload.source, "new", now_utc(), "[]"),
    )
    conn.commit()
    conn.close()
    _audit("incident_created", actor="analyst", details={"incident_id": incident_id})
    return {"id": incident_id, **payload.model_dump(), "state": "new"}


@app.post("/cases/incidents/{incident_id}/transition", tags=["Cases"], dependencies=[Depends(require_role({"superadmin", "admin", "analyst"}))])
def transition_incident(incident_id: str, payload: IncidentTransition):
    conn = db_connect()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Incident not found")
    conn.execute("UPDATE incidents SET state = ? WHERE id = ?", (payload.state, incident_id))
    conn.commit()
    conn.close()
    _audit("incident_transition", actor="analyst", details={"incident_id": incident_id, "to": payload.state})
    return {"id": incident_id, "state": payload.state, "note": payload.note}


@app.get("/integrations/health", tags=["Integrations"], dependencies=[Depends(require_role({"superadmin", "admin", "analyst", "viewer"}))])
def integration_health_check():
    now = datetime.now(timezone.utc)
    results = []
    for name, meta in connectors.items():
        age_minutes = int((now - datetime.fromisoformat(meta["last_sync"].replace("Z", "+00:00"))).total_seconds() / 60)
        status_value = "healthy" if meta["latency_ms"] <= 160 and age_minutes <= 30 else "degraded"
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
    return {"items": results}


@app.get("/iam/status", tags=["IAM"], dependencies=[Depends(require_role({"superadmin", "admin"}))])
def iam_status():
    return {
        "vault": {"addr": VAULT_ADDR, "role": VAULT_ROLE, "mode": "pam-primary"},
        "keycloak": {"url": KEYCLOAK_URL, "realm": KEYCLOAK_REALM, "mode": "sso"},
        "sqlite": {"path": DB_PATH, "purpose": "local fallback + metadata"},
    }


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard_page():
    dashboard_file = STATIC_DIR / "dashboard.html"
    return HTMLResponse(dashboard_file.read_text(encoding="utf-8"))


@app.get("/dashboard/metrics", tags=["Dashboard"], dependencies=[Depends(require_role({"superadmin", "admin", "analyst", "viewer"}))])
def dashboard_metrics():
    return {
        "period": "last_7_days",
        "alerts_by_severity": {"critical": 7, "high": 18, "medium": 34, "low": 22},
        "mttr_hours": [6.8, 6.1, 5.4, 5.0, 4.7, 4.5],
        "detection_coverage": [72, 74, 77, 79, 82, 84],
        "trend_line_alerts": [52, 49, 60, 58, 63, 55, 48],
        "risk_heatmap": [
            {"domain": "Identity", "risk": 0.81},
            {"domain": "Endpoint", "risk": 0.62},
            {"domain": "Cloud", "risk": 0.73},
            {"domain": "Network", "risk": 0.58},
        ],
        "incident_distribution": [
            {"stage": "new", "count": 9},
            {"stage": "triage", "count": 11},
            {"stage": "investigating", "count": 8},
            {"stage": "contained", "count": 5},
            {"stage": "closed", "count": 14},
        ],
        "operational_status": [
            {
                "name": name,
                "type": meta["type"],
                "status": "connected" if meta["latency_ms"] <= 160 else "degraded",
                "latency_ms": meta["latency_ms"],
                "sync_lag_seconds": int((meta["latency_ms"] / 10) + 2),
            }
            for name, meta in connectors.items()
        ],
        "sync_success_rate_pct": 98.6,
        "updated_at": now_utc(),
    }
