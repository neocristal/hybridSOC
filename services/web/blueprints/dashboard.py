"""Dashboard KPIs / aggregate metrics for analyst views."""
from __future__ import annotations

from flask import Blueprint, jsonify

from ..auth import login_required
from ..db import get_db

bp = Blueprint("dashboard", __name__)


@bp.get("/stats")
@login_required()
def stats():
    db = get_db()
    counts = {
        "users": db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"],
        "open_incidents": db.execute(
            "SELECT COUNT(*) AS c FROM incidents WHERE status = 'open'"
        ).fetchone()["c"],
        "risks": db.execute("SELECT COUNT(*) AS c FROM risks").fetchone()["c"],
        "audit_entries": db.execute("SELECT COUNT(*) AS c FROM audit_log").fetchone()["c"],
    }
    severity = [
        dict(r)
        for r in db.execute(
            "SELECT severity, COUNT(*) AS count FROM incidents "
            "GROUP BY severity ORDER BY count DESC"
        )
    ]
    risk_buckets = [
        dict(r)
        for r in db.execute(
            "SELECT CASE "
            "  WHEN likelihood * impact >= 20 THEN 'Critical' "
            "  WHEN likelihood * impact >= 12 THEN 'High' "
            "  WHEN likelihood * impact >= 6  THEN 'Medium' "
            "  ELSE 'Low' END AS bucket, "
            "COUNT(*) AS count FROM risks GROUP BY bucket"
        )
    ]
    return jsonify(counts=counts, severity=severity, risk_buckets=risk_buckets)
