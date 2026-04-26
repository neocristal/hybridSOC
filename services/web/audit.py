"""Hash-chained immutable audit log helper (matches INTEGRITY.md §2.1)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .db import get_db


def _row_hash(prev_hash: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()


def write_audit(
    *,
    user_id: int | None,
    action: str,
    details: str = "",
    ip_address: str | None = None,
) -> int:
    db = get_db()
    last = db.execute(
        "SELECT row_hash FROM audit_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    prev_hash = last["row_hash"] if last else "0" * 64
    payload = {
        "user_id": user_id,
        "action": action,
        "details": details,
        "ip_address": ip_address or "",
    }
    row_hash = _row_hash(prev_hash, payload)
    cursor = db.execute(
        """INSERT INTO audit_log(user_id, action, details, ip_address, prev_hash, row_hash)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, action, details, ip_address, prev_hash, row_hash),
    )
    db.commit()
    return int(cursor.lastrowid)


def verify_chain() -> tuple[bool, int | None]:
    """Recompute the chain; return (ok, first_bad_id)."""
    db = get_db()
    prev = "0" * 64
    for row in db.execute(
        "SELECT id, user_id, action, details, ip_address, prev_hash, row_hash "
        "FROM audit_log ORDER BY id ASC"
    ):
        if row["prev_hash"] != prev:
            return False, row["id"]
        expected = _row_hash(prev, {
            "user_id": row["user_id"],
            "action": row["action"],
            "details": row["details"],
            "ip_address": row["ip_address"] or "",
        })
        if expected != row["row_hash"]:
            return False, row["id"]
        prev = row["row_hash"]
    return True, None
