"""GRC: incidents (with DORA / NIS2 timers) and TPRM vendors."""
from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..audit import write_audit
from ..auth import login_required
from ..db import get_db

bp = Blueprint("grc", __name__)


@bp.get("/incidents")
@login_required()
def list_incidents():
    rows = get_db().execute(
        "SELECT id, title, severity, type, frameworks, status, "
        "created_at, dora_deadline, nis2_deadline FROM incidents "
        "ORDER BY id DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/incidents")
@login_required("analyst", "manager", "compliance", "admin", "superadmin")
def create_incident():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(error="title_required"), 400
    db = get_db()
    cur = db.execute(
        """INSERT INTO incidents(title, severity, type, frameworks, status,
                                  dora_deadline, nis2_deadline, owner_id)
           VALUES (?, ?, ?, ?, 'open',
                   datetime('now', '+72 hours'),
                   datetime('now', '+24 hours'),
                   ?)""",
        (
            title,
            body.get("severity", "Medium"),
            body.get("type", "ICT_INCIDENT"),
            ",".join(body.get("frameworks", []) or []),
            g.user["id"],
        ),
    )
    db.commit()
    write_audit(
        user_id=g.user["id"],
        action="incident_created",
        details=f"id={cur.lastrowid} title={title}",
    )
    return jsonify(id=cur.lastrowid, dora_deadline_hours=72, nis2_deadline_hours=24), 201


@bp.get("/vendors")
@login_required()
def list_vendors():
    rows = get_db().execute(
        "SELECT id, name, criticality, dora_art28, services FROM vendors ORDER BY id"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/vendors")
@login_required("compliance", "admin", "superadmin")
def create_vendor():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify(error="name_required"), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO vendors(name, criticality, dora_art28, services) VALUES (?, ?, ?, ?)",
        (
            name,
            body.get("criticality", "Medium"),
            1 if body.get("dora_art28_applicable") else 0,
            ",".join(body.get("services", []) or []),
        ),
    )
    db.commit()
    write_audit(user_id=g.user["id"], action="vendor_created", details=f"id={cur.lastrowid} {name}")
    return jsonify(id=cur.lastrowid), 201
