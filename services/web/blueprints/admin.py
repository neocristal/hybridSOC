"""User and tenant administration."""
from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..audit import write_audit
from ..auth import hash_password, login_required
from ..db import get_db

bp = Blueprint("admin", __name__)


@bp.get("/users")
@login_required("admin", "superadmin")
def list_users():
    rows = get_db().execute(
        "SELECT id, email, role, active, totp_enabled, created_at FROM users ORDER BY id"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/users")
@login_required("admin", "superadmin")
def create_user():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    role = body.get("role", "analyst")
    if not email or not password:
        return jsonify(error="email_and_password_required"), 400
    salt, pw_hash = hash_password(password)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users(email, password_salt, password_hash, role) "
            "VALUES (?, ?, ?, ?)",
            (email, salt, pw_hash, role),
        )
        db.commit()
    except Exception as e:
        return jsonify(error=str(e)), 400
    write_audit(user_id=g.user["id"], action="user_created", details=f"new_id={cur.lastrowid} email={email}")
    return jsonify(id=cur.lastrowid, email=email, role=role), 201


@bp.patch("/users/<int:user_id>")
@login_required("admin", "superadmin")
def update_user(user_id: int):
    body = request.get_json(silent=True) or {}
    allowed = {"role", "active"}
    fields = {k: v for k, v in body.items() if k in allowed}
    if not fields:
        return jsonify(error="no_fields"), 400
    db = get_db()
    if "role" in fields and "active" in fields:
        db.execute(
            "UPDATE users SET role = ?, active = ? WHERE id = ?",
            (fields["role"], fields["active"], user_id),
        )
    elif "role" in fields:
        db.execute("UPDATE users SET role = ? WHERE id = ?", (fields["role"], user_id))
    elif "active" in fields:
        db.execute("UPDATE users SET active = ? WHERE id = ?", (fields["active"], user_id))
    db.commit()
    write_audit(user_id=g.user["id"], action="user_updated", details=f"id={user_id} fields={list(fields)}")
    return jsonify(ok=True)


@bp.get("/tenants")
@login_required("admin", "superadmin")
def list_tenants():
    rows = get_db().execute("SELECT id, name, created_at FROM tenants ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/tenants")
@login_required("superadmin")
def create_tenant():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify(error="name_required"), 400
    db = get_db()
    cur = db.execute("INSERT INTO tenants(name) VALUES (?)", (name,))
    db.commit()
    write_audit(user_id=g.user["id"], action="tenant_created", details=f"name={name}")
    return jsonify(id=cur.lastrowid, name=name), 201
