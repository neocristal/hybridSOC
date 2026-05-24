"""Login, MFA challenge / verify, logout."""
from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from ..audit import write_audit
from ..auth import (
    issue_email_otp,
    issue_session,
    login_required,
    new_totp_secret,
    revoke_session,
    send_email_otp,
    totp_provisioning_uri,
    verify_email_otp,
    verify_password,
    verify_totp,
    verify_turnstile,
)
from ..db import get_db

bp = Blueprint("auth", __name__)


def _client_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()


@bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    turnstile = body.get("turnstile_token")

    if not verify_turnstile(turnstile, _client_ip()):
        return jsonify(error="captcha_failed"), 400

    row = get_db().execute(
        "SELECT id, email, password_salt, password_hash, role, totp_enabled "
        "FROM users WHERE email = ? AND active = 1",
        (email,),
    ).fetchone()
    if not row or not verify_password(password, row["password_salt"], row["password_hash"]):
        write_audit(user_id=None, action="login_failed", details=f"email={email}", ip_address=_client_ip())
        return jsonify(error="invalid_credentials"), 401

    write_audit(user_id=row["id"], action="login_password_ok", ip_address=_client_ip())
    return jsonify(
        user_id=row["id"],
        email=row["email"],
        mfa_required=True,
        totp_enabled=bool(row["totp_enabled"]),
        methods=["google_totp", "email_otp"] if row["totp_enabled"] else ["email_otp"],
    )


@bp.post("/mfa/challenge")
def mfa_challenge():
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id")
    method = body.get("method", "email_otp")

    user = get_db().execute(
        "SELECT id, email FROM users WHERE id = ? AND active = 1", (user_id,)
    ).fetchone()
    if not user:
        return jsonify(error="user_not_found"), 404

    if method == "email_otp":
        code = issue_email_otp(user["id"])
        send_email_otp(user["email"], code)
        write_audit(user_id=user["id"], action="mfa_email_otp_sent", ip_address=_client_ip())
        return jsonify(method="email_otp", sent_to=user["email"])

    if method == "google_totp":
        return jsonify(method="google_totp", note="Provide the current 6-digit TOTP code.")

    return jsonify(error="unsupported_method"), 400


@bp.post("/mfa/verify")
def mfa_verify():
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id")
    method = body.get("method", "email_otp")
    code = (body.get("code") or "").strip()

    db = get_db()
    user = db.execute(
        "SELECT id, email, role, totp_secret, totp_enabled "
        "FROM users WHERE id = ? AND active = 1",
        (user_id,),
    ).fetchone()
    if not user:
        return jsonify(error="user_not_found"), 404

    ok = False
    if method == "email_otp":
        ok = verify_email_otp(user["id"], code)
    elif method == "google_totp" and user["totp_enabled"]:
        ok = verify_totp(user["totp_secret"], code)

    if not ok:
        write_audit(user_id=user["id"], action="mfa_failed", details=method, ip_address=_client_ip())
        return jsonify(error="invalid_code"), 401

    token = issue_session(user["id"])
    write_audit(user_id=user["id"], action="login_mfa_ok", details=method, ip_address=_client_ip())
    return jsonify(
        access_token=token,
        token_type="Bearer",
        expires_in=int(current_app.config["SESSION_TTL_SECONDS"]),
        user={"id": user["id"], "email": user["email"], "role": user["role"]},
    )


@bp.post("/totp/enroll")
@login_required()
def totp_enroll():
    secret = new_totp_secret()
    db = get_db()
    db.execute(
        "UPDATE users SET totp_secret = ?, totp_enabled = 0 WHERE id = ?",
        (secret, g.user["id"]),
    )
    db.commit()
    return jsonify(
        secret=secret,
        otpauth_url=totp_provisioning_uri(secret, g.user["email"]),
    )


@bp.post("/totp/activate")
@login_required()
def totp_activate():
    body = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute("SELECT totp_secret FROM users WHERE id = ?", (g.user["id"],)).fetchone()
    if not row or not row["totp_secret"]:
        return jsonify(error="no_totp_pending"), 400
    if not verify_totp(row["totp_secret"], (body.get("code") or "").strip()):
        return jsonify(error="invalid_code"), 401
    db.execute("UPDATE users SET totp_enabled = 1 WHERE id = ?", (g.user["id"],))
    db.commit()
    write_audit(user_id=g.user["id"], action="totp_activated", ip_address=_client_ip())
    return jsonify(totp_enabled=True)


@bp.post("/logout")
@login_required()
def logout():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        revoke_session(header[7:])
    write_audit(user_id=g.user["id"], action="logout", ip_address=_client_ip())
    return jsonify(ok=True)


@bp.get("/me")
@login_required()
def me():
    return jsonify(g.user)
