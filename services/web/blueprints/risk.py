"""Risk register CRUD and AI-engine proxy for ad-hoc risk scoring."""
from __future__ import annotations

import requests
from flask import Blueprint, current_app, g, jsonify, request

from ..audit import write_audit
from ..auth import login_required
from ..db import get_db

bp = Blueprint("risk", __name__)


@bp.get("/")
@login_required()
def list_risks():
    rows = get_db().execute(
        "SELECT id, title, likelihood, impact, framework, article, treatment, status, created_at "
        "FROM risks ORDER BY likelihood * impact DESC, id DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/")
@login_required("analyst", "manager", "compliance", "admin", "superadmin")
def create_risk():
    body = request.get_json(silent=True) or {}
    required = {"title", "likelihood", "impact"}
    if not required.issubset(body):
        return jsonify(error="missing_fields", required=list(required)), 400
    db = get_db()
    cur = db.execute(
        """INSERT INTO risks(title, likelihood, impact, framework, article, treatment, status, owner_id)
           VALUES (?, ?, ?, ?, ?, ?, COALESCE(?, 'open'), ?)""",
        (
            body["title"],
            int(body["likelihood"]),
            int(body["impact"]),
            body.get("framework"),
            body.get("article"),
            body.get("treatment"),
            body.get("status"),
            g.user["id"],
        ),
    )
    db.commit()
    write_audit(user_id=g.user["id"], action="risk_created", details=f"id={cur.lastrowid} {body['title']}")
    return jsonify(id=cur.lastrowid), 201


@bp.post("/score")
@login_required()
def score_event():
    """Forward a payload to the AI Engine's /risk endpoint."""
    payload = request.get_json(silent=True) or {}
    url = current_app.config["AI_ENGINE_URL"].rstrip("/") + "/risk"
    try:
        r = requests.post(url, json=payload, timeout=5)
        r.raise_for_status()
        result = r.json()
    except requests.RequestException:
        current_app.logger.exception("AI engine risk scoring request failed")
        return jsonify(error="ai_engine_unreachable"), 502
    write_audit(
        user_id=g.user["id"],
        action="ai_risk_scored",
        details=f"score={result.get('risk_score')} severity={result.get('severity')}",
    )
    return jsonify(result)
