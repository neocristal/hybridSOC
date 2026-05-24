# HybridSOC Web — Admin & Analytics Interface

Flask 3 + React 18.3/Vite implementation of the L7 admin/dashboard module described
in [`docs/system-design.md`](../../docs/system-design.md).

| Layer    | Stack                                                                              |
|----------|------------------------------------------------------------------------------------|
| Backend  | Python 3.10+ / Flask 3.0+, SQLite 3 (WAL mode), blueprints                          |
| Frontend | React 18.3 / Vite, plain JSX with inline CSS                                        |
| Auth     | PBKDF2-SHA256 (260 k iterations + per-user salt + global PEPPER), TOTP, Email OTP, Cloudflare Turnstile |
| AI hook  | Optional: forwards `/api/risk/score` → AI Engine `/risk` (FAISS RAG / Mistral-7B)   |

## Layout

```
services/web/
├── app.py                 # Flask factory, runs migrations on startup
├── config.py              # Env-driven Config dataclass
├── db.py                  # SQLite WAL helper + migration runner
├── auth.py                # PBKDF2, TOTP, Email OTP, Turnstile, sessions, decorators
├── audit.py               # Hash-chained immutable audit log
├── migrate.py             # CLI: --status, --bootstrap, --verify
├── blueprints/            # auth, admin, dashboard, risk, grc, audit
├── migrations/            # 0001_initial.sql, 0002_grc.sql, …
├── frontend/              # Vite + React 18.3
└── requirements.txt
```

## One-shot install

### Linux / macOS (bash)

```bash
bash scripts/install-web.sh           # backend + frontend build
bash scripts/install-web.sh --dev     # backend + frontend deps, no build
bash scripts/install-web.sh --no-frontend
```

The script prefers **Bun** for the JS toolchain and installs it from
`https://bun.sh/install` if it is missing. If Bun cannot be installed, it
falls back to Node.js 20.x (installed via NodeSource on Debian/Ubuntu).

### Windows (PowerShell)

```powershell
# From the repo root, in a PowerShell window
.\scripts\install-web.ps1                  # backend + frontend build
.\scripts\install-web.ps1 -Dev             # backend + frontend deps, no build
.\scripts\install-web.ps1 -NoFrontend
```

If you hit an execution-policy error, allow scripts for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

The PowerShell installer prefers Bun (installed via `irm bun.sh/install.ps1 | iex`)
and falls back to Node.js 20.x. Pre-install Python 3.10+ from python.org
or `winget install Python.Python.3.12` before running it.

## Manual setup

### Backend (cross-platform)

Linux / macOS:

```bash
cd services/web
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                   # edit FLASK_SECRET_KEY, HYBRIDSOC_PEPPER, SMTP, Turnstile
python -m services.web.migrate --bootstrap
python -m services.web.app             # http://localhost:5000
```

Windows PowerShell:

```powershell
cd services\web
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env             # edit values in your editor
Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') } }
python -m services.web.migrate --bootstrap
python -m services.web.app              # http://localhost:5000
```

For production (gunicorn, Linux/macOS only — on Windows use `waitress` or run
behind IIS):

```bash
gunicorn -w 4 -b 0.0.0.0:5000 'services.web.app:create_app()'
```

### Frontend — Bun (recommended)

```bash
cd services/web/frontend
bun install
bun run dev                            # http://localhost:5173 (proxies /api → :5000)
bun run build                          # writes ./dist served by Flask
```

PowerShell uses identical commands (`bun install`, `bun run dev`, `bun run build`).

### Frontend — npm fallback

```bash
cd services/web/frontend
npm install
npm run dev
npm run build
```

## SQLite update service

`migrate.py` is the one-stop CLI for the schema:

```bash
python -m services.web.migrate              # apply pending *.sql migrations
python -m services.web.migrate --status     # list applied vs pending
python -m services.web.migrate --bootstrap  # apply + create superadmin
python -m services.web.migrate --verify     # verify the audit hash chain
```

Migrations are plain SQL files in `migrations/`, applied in lexicographic order
exactly once and recorded in `schema_migrations`. Drop a new `0003_*.sql` file in
that directory and the app picks it up on the next start.

## Auth model

| Step       | Mechanism                                                         |
|------------|-------------------------------------------------------------------|
| Password   | PBKDF2-SHA256, 260 000 iterations, 16-byte per-user salt, global `HYBRIDSOC_PEPPER` not stored in DB |
| Bot defence| Cloudflare Turnstile token (`TURNSTILE_REQUIRED=1` to enforce)    |
| MFA — TOTP | RFC 6238 via `pyotp`, enrolment returns an `otpauth://` URI       |
| MFA — Email| 6-digit OTP, SHA-256 hashed, 5 min TTL, single-use                |
| Session    | 32-byte random Bearer token, SHA-256 hashed in `sessions` table   |
| Audit      | Every auth event written to the hash-chained `audit_log`          |

## API

| Method | Path                              | Roles                                             |
|--------|-----------------------------------|---------------------------------------------------|
| GET    | `/api/health`                     | public                                            |
| POST   | `/api/auth/login`                 | public (Turnstile-gated)                          |
| POST   | `/api/auth/mfa/challenge`         | public                                            |
| POST   | `/api/auth/mfa/verify`            | public → returns Bearer token                     |
| POST   | `/api/auth/totp/enroll`           | authenticated                                     |
| POST   | `/api/auth/totp/activate`         | authenticated                                     |
| POST   | `/api/auth/logout`                | authenticated                                     |
| GET    | `/api/auth/me`                    | authenticated                                     |
| GET    | `/api/dashboard/stats`            | authenticated                                     |
| GET/POST | `/api/admin/users`              | admin / superadmin                                |
| PATCH  | `/api/admin/users/<id>`           | admin / superadmin                                |
| GET/POST | `/api/admin/tenants`            | admin / superadmin (POST: superadmin)             |
| GET/POST | `/api/risk/`                    | authenticated / analyst+                          |
| POST   | `/api/risk/score`                 | authenticated → forwards to AI Engine `/risk`     |
| GET/POST | `/api/grc/incidents`            | authenticated / analyst+ (POST starts DORA timers) |
| GET/POST | `/api/grc/vendors`              | authenticated / compliance+                       |
| GET    | `/api/audit/`                     | admin / superadmin                                |
| GET    | `/api/audit/verify`               | admin / superadmin (re-validates the hash chain)  |

## Frontend pages

`Login → MFA → Dashboard → (Risk Register | Incidents | Users | Audit Log)`.
All pages are plain JSX with inline CSS so there is no global stylesheet to maintain.
