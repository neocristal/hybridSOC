"""Read-only access to the immutable audit log."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..audit import verify_chain
from ..auth import login_required
from ..db import get_db

bp = Blueprint("audit", __name__)


@bp.get("/")
@login_required("admin", "superadmin")
def list_audit():
    limit = min(int(request.args.get("limit", 200)), 1000)
    rows = get_db().execute(
        "SELECT id, user_id, action, details, ip_address, timestamp, prev_hash, row_hash "
        "FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.get("/verify")
@login_required("admin", "superadmin")
def verify():
    ok, bad_id = verify_chain()
    return jsonify(ok=ok, first_bad_id=bad_id)
