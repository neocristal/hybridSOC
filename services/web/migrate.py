"""CLI for the SQLite update service.

Usage:
    python -m services.web.migrate              # apply pending migrations
    python -m services.web.migrate --status     # show applied vs pending
    python -m services.web.migrate --bootstrap  # apply + create superadmin
    python -m services.web.migrate --verify     # verify the audit hash chain
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

# Allow running as a script (`python migrate.py`) or as a module
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.web.app import create_app  # noqa: E402
from services.web.audit import verify_chain, write_audit  # noqa: E402
from services.web.auth import hash_password  # noqa: E402
from services.web.config import Config  # noqa: E402
from services.web.db import get_db, run_migrations  # noqa: E402


def _list(cfg: Config) -> tuple[list[str], list[str]]:
    db = sqlite3.connect(str(cfg.DATABASE_PATH))
    db.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(name TEXT PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )
    applied = {r[0] for r in db.execute("SELECT name FROM schema_migrations")}
    db.close()
    all_files = sorted(p.name for p in cfg.MIGRATIONS_DIR.glob("*.sql"))
    pending = [n for n in all_files if n not in applied]
    return sorted(applied), pending


def _bootstrap_superadmin(app) -> None:
    email = os.environ.get("BOOTSTRAP_EMAIL", "superadmin@hybridsoc.local").lower()
    password = os.environ.get("BOOTSTRAP_PASSWORD", "ChangeMeNow!123")
    with app.app_context():
        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            print(f"Superadmin {email} already exists (id={existing['id']})")
            return
        salt, pw_hash = hash_password(password)
        cur = db.execute(
            "INSERT INTO users(email, password_salt, password_hash, role) "
            "VALUES (?, ?, ?, 'superadmin')",
            (email, salt, pw_hash),
        )
        db.commit()
        write_audit(user_id=cur.lastrowid, action="superadmin_bootstrapped", details=email)
        print(f"Created superadmin {email} (change the password immediately)")


def main() -> int:
    parser = argparse.ArgumentParser(description="HybridSOC SQLite update service")
    parser.add_argument("--status", action="store_true", help="show migration status only")
    parser.add_argument("--bootstrap", action="store_true", help="create superadmin after migrating")
    parser.add_argument("--verify", action="store_true", help="verify audit hash chain")
    args = parser.parse_args()

    cfg = Config.from_env()
    if args.status:
        applied, pending = _list(cfg)
        print(f"DB:        {cfg.DATABASE_PATH}")
        print(f"Applied:   {applied or '(none)'}")
        print(f"Pending:   {pending or '(none)'}")
        return 0

    app = create_app(cfg)

    if args.verify:
        with app.app_context():
            ok, bad = verify_chain()
        print("Audit chain OK" if ok else f"Audit chain BROKEN at id={bad}")
        return 0 if ok else 2

    with app.app_context():
        applied = run_migrations(get_db(), cfg.MIGRATIONS_DIR)
    if applied:
        print("Applied:", ", ".join(applied))
    else:
        print("Schema is up to date.")

    if args.bootstrap:
        _bootstrap_superadmin(app)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
