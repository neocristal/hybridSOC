"""Runtime configuration for the HybridSOC web service."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _env(name: str, default: str | None = None, *, required: bool = False) -> str:
    val = os.environ.get(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val or ""


@dataclass(frozen=True)
class Config:
    SECRET_KEY: str
    PEPPER: str  # Global PBKDF2 pepper, kept out of the DB
    DATABASE_PATH: Path
    MIGRATIONS_DIR: Path
    FRONTEND_DIST: Path

    # Auth tuning
    PBKDF2_ITERATIONS: int = 260_000
    SESSION_TTL_SECONDS: int = 8 * 60 * 60
    OTP_TTL_SECONDS: int = 5 * 60

    # Email OTP / SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "no-reply@hybridsoc.local"

    # Cloudflare Turnstile
    TURNSTILE_SECRET: str = ""
    TURNSTILE_REQUIRED: bool = False

    # AI engine integration
    AI_ENGINE_URL: str = "http://localhost:8000"

    @classmethod
    def from_env(cls) -> "Config":
        db_path = Path(_env("HYBRIDSOC_DB", str(BASE_DIR / "hybridsoc.db")))
        return cls(
            SECRET_KEY=_env("FLASK_SECRET_KEY", "change-me-in-prod"),
            PEPPER=_env("HYBRIDSOC_PEPPER", "change-me-pepper"),
            DATABASE_PATH=db_path,
            MIGRATIONS_DIR=BASE_DIR / "migrations",
            FRONTEND_DIST=Path(_env("FRONTEND_DIST", str(BASE_DIR / "frontend" / "dist"))),
            PBKDF2_ITERATIONS=int(_env("PBKDF2_ITERATIONS", "260000")),
            SESSION_TTL_SECONDS=int(_env("SESSION_TTL_SECONDS", str(8 * 3600))),
            OTP_TTL_SECONDS=int(_env("OTP_TTL_SECONDS", "300")),
            SMTP_HOST=_env("SMTP_HOST", ""),
            SMTP_PORT=int(_env("SMTP_PORT", "587")),
            SMTP_USER=_env("SMTP_USER", ""),
            SMTP_PASS=_env("SMTP_PASS", ""),
            SMTP_FROM=_env("SMTP_FROM", "no-reply@hybridsoc.local"),
            TURNSTILE_SECRET=_env("TURNSTILE_SECRET", ""),
            TURNSTILE_REQUIRED=_env("TURNSTILE_REQUIRED", "0") == "1",
            AI_ENGINE_URL=_env("AI_ENGINE_URL", "http://localhost:8000"),
        )
