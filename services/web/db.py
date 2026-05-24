"""SQLite connection helper, WAL mode, and migration runner."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app, g


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = _connect(Path(current_app.config["DATABASE_PATH"]))
    return g.db


def close_connection(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def run_migrations(db: sqlite3.Connection, migrations_dir: Path) -> list[str]:
    """Apply every *.sql file in `migrations_dir` exactly once.

    The migration name is recorded in `schema_migrations`; existing files are
    re-applied only if they have not been recorded yet. Returns the list of
    migration names applied during this call.
    """
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name        TEXT PRIMARY KEY,
            applied_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    applied = {row["name"] for row in db.execute("SELECT name FROM schema_migrations")}
    just_applied: list[str] = []
    for path in sorted(Path(migrations_dir).glob("*.sql")):
        if path.name in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        with db:  # implicit transaction
            db.executescript(sql)
            db.execute("INSERT INTO schema_migrations(name) VALUES (?)", (path.name,))
        just_applied.append(path.name)
        current_app.logger.info("Applied migration %s", path.name)
    return just_applied
