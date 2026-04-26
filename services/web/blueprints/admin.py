"""User and tenant administration."""
from __future__ import annotations

import sqlite3

from flask import Blueprint, current_app, g, jsonify, request

from ..audit import write_audit
from ..auth import hash_password, login_required
from ..db import get_db

bp = Blueprint("admin", __name__)

VALID_ROLES = {"analyst", "manager", "compliance", "admin", "superadmin"}


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
    if role not in VALID_ROLES:
        return jsonify(error="invalid_role"), 400
    salt, pw_hash = hash_password(password)
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users(email, password_salt, password_hash, role) "
            "VALUES (?, ?, ?, ?)",
            (email, salt, pw_hash, role),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="email_already_exists"), 409
    except sqlite3.DatabaseError:
        current_app.logger.exception("Failed to create user")
        return jsonify(error="user_creation_failed"), 400
    write_audit(user_id=g.user["id"], action="user_created", details=f"new_id={cur.lastrowid} email={email}")
    return jsonify(id=cur.lastrowid, email=email, role=role), 201


@bp.patch("/users/<int:user_id>")
@login_required("admin", "superadmin")
def update_user(user_id: int):
    body = request.get_json(silent=True) or {}
    has_role = "role" in body
    has_active = "active" in body
    if not (has_role or has_active):
        return jsonify(error="no_fields"), 400
    if has_role and body["role"] not in VALID_ROLES:
        return jsonify(error="invalid_role"), 400

    role = body["role"] if has_role else None
    active = (1 if body["active"] else 0) if has_active else None

    db = get_db()
    if has_role and has_active:
        db.execute(
            "UPDATE users SET role = ?, active = ? WHERE id = ?",
            (role, active, user_id),
        )
    elif has_role:
        db.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    else:
        db.execute("UPDATE users SET active = ? WHERE id = ?", (active, user_id))
    db.commit()

    touched = [n for n, present in (("role", has_role), ("active", has_active)) if present]
    write_audit(user_id=g.user["id"], action="user_updated", details=f"id={user_id} fields={touched}")
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
