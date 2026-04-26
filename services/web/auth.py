"""Authentication primitives: PBKDF2-SHA256, TOTP, Email OTP, Turnstile, sessions."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import smtplib
import time
from email.message import EmailMessage
from functools import wraps
from typing import Any, Callable

import pyotp
import requests
from flask import current_app, g, jsonify, request

from .db import get_db


# ─── Password hashing ────────────────────────────────────────────────────────

def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Return (salt_b64, hash_b64) using PBKDF2-SHA256 with the configured pepper.

    The pepper is concatenated to the password (kept outside the database) so
    a DB-only leak still requires the pepper to mount an offline attack.
    """
    salt = salt or secrets.token_bytes(16)
    iterations = int(current_app.config["PBKDF2_ITERATIONS"])
    pepper = current_app.config["PEPPER"].encode("utf-8")
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8") + pepper, salt, iterations, dklen=32
    )
    return base64.b64encode(salt).decode(), base64.b64encode(derived).decode()


def verify_password(password: str, salt_b64: str, expected_b64: str) -> bool:
    salt = base64.b64decode(salt_b64)
    _, candidate_b64 = hash_password(password, salt)
    return hmac.compare_digest(candidate_b64, expected_b64)


# ─── TOTP MFA ────────────────────────────────────────────────────────────────

def new_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    try:
        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except Exception:
        return False


def totp_provisioning_uri(secret: str, email: str, issuer: str = "HybridSOC") -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


# ─── Email OTP ───────────────────────────────────────────────────────────────

def issue_email_otp(user_id: int) -> str:
    """Generate a 6-digit OTP, store its hash, return the plaintext code."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    ttl = int(current_app.config["OTP_TTL_SECONDS"])
    db = get_db()
    db.execute(
        """INSERT INTO email_otp(user_id, code_hash, expires_at)
           VALUES (?, ?, datetime('now', ?))""",
        (user_id, code_hash, f"+{ttl} seconds"),
    )
    db.commit()
    return code


def verify_email_otp(user_id: int, code: str) -> bool:
    db = get_db()
    row = db.execute(
        """SELECT id, code_hash FROM email_otp
           WHERE user_id = ? AND consumed = 0
             AND expires_at > datetime('now')
           ORDER BY id DESC LIMIT 1""",
        (user_id,),
    ).fetchone()
    if not row:
        return False
    if not hmac.compare_digest(row["code_hash"], hashlib.sha256(code.encode()).hexdigest()):
        return False
    db.execute("UPDATE email_otp SET consumed = 1 WHERE id = ?", (row["id"],))
    db.commit()
    return True


def send_email_otp(to: str, code: str) -> None:
    cfg = current_app.config
    if not cfg.get("SMTP_HOST"):
        current_app.logger.warning("SMTP not configured — OTP for %s = %s", to, code)
        return
    msg = EmailMessage()
    msg["From"] = cfg["SMTP_FROM"]
    msg["To"] = to
    msg["Subject"] = "Your HybridSOC verification code"
    msg.set_content(f"Your one-time code is: {code}\nIt expires in 5 minutes.")
    with smtplib.SMTP(cfg["SMTP_HOST"], int(cfg["SMTP_PORT"])) as s:
        s.starttls()
        if cfg.get("SMTP_USER"):
            s.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
        s.send_message(msg)


# ─── Cloudflare Turnstile ────────────────────────────────────────────────────

def verify_turnstile(token: str | None, remote_ip: str | None) -> bool:
    cfg = current_app.config
    if not cfg.get("TURNSTILE_REQUIRED"):
        return True
    secret = cfg.get("TURNSTILE_SECRET")
    if not secret or not token:
        return False
    try:
        r = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": secret, "response": token, "remoteip": remote_ip or ""},
            timeout=5,
        )
        return bool(r.ok and r.json().get("success"))
    except Exception:
        return False


# ─── Session tokens ──────────────────────────────────────────────────────────

def issue_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    ttl = int(current_app.config["SESSION_TTL_SECONDS"])
    db = get_db()
    db.execute(
        """INSERT INTO sessions(user_id, token_hash, expires_at)
           VALUES (?, ?, datetime('now', ?))""",
        (user_id, token_hash, f"+{ttl} seconds"),
    )
    db.commit()
    return token


def revoke_session(token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db = get_db()
    db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
    db.commit()


def _user_from_token(token: str) -> dict[str, Any] | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    row = get_db().execute(
        """SELECT u.id, u.email, u.role, u.totp_enabled
             FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > datetime('now')""",
        (token_hash,),
    ).fetchone()
    return dict(row) if row else None


def login_required(*roles: str) -> Callable:
    """Decorator: require Bearer auth, optionally restrict by role."""
    def deco(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify(error="unauthorized"), 401
            user = _user_from_token(header[7:])
            if not user:
                return jsonify(error="unauthorized"), 401
            if roles and user["role"] not in roles:
                return jsonify(error="forbidden"), 403
            g.user = user
            return fn(*args, **kwargs)
        return wrapper
    return deco
