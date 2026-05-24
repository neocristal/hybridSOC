#!/usr/bin/env bash
# HybridSOC Web — install & bootstrap script
#
# Sets up the Flask backend, the React/Vite frontend, runs SQLite migrations,
# and creates the bootstrap superadmin. Targets Linux/macOS with Python 3.10+
# and (optionally) Node.js 20.x. Pass --no-frontend to skip the JS build.
#
# Usage:
#   bash scripts/install-web.sh                # full install + frontend build
#   bash scripts/install-web.sh --no-frontend  # backend only
#   bash scripts/install-web.sh --dev          # do not build, run dev server

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="${REPO_ROOT}/services/web"
FRONT_DIR="${WEB_DIR}/frontend"
NODE_REQUIRED_MAJOR=20
PY_REQUIRED_MINOR=10

WITH_FRONTEND=1
DEV_MODE=0
for arg in "$@"; do
  case "$arg" in
    --no-frontend) WITH_FRONTEND=0 ;;
    --dev)         DEV_MODE=1 ;;
    -h|--help)
      sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

log()  { printf '\033[1;34m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[fail]\033[0m %s\n' "$*" >&2; exit 1; }

# ── Python ────────────────────────────────────────────────────────────────
need_python() {
  command -v python3 >/dev/null || fail "python3 not found (need >= 3.${PY_REQUIRED_MINOR})"
  local minor
  minor="$(python3 -c 'import sys; print(sys.version_info.minor)')"
  [[ "$minor" -ge "$PY_REQUIRED_MINOR" ]] || fail "python3 >= 3.${PY_REQUIRED_MINOR} required (have 3.${minor})"
}

# ── Bun (preferred) — falls back to Node.js + npm if unavailable ─────────
JS_RUNNER=""

ensure_bun() {
  if command -v bun >/dev/null; then
    log "Bun $(bun --version) detected"
    JS_RUNNER="bun"; return 0
  fi
  log "Bun not found — installing official build (https://bun.sh)…"
  if curl -fsSL https://bun.sh/install | bash; then
    # Bun installs to ~/.bun/bin
    export PATH="$HOME/.bun/bin:$PATH"
    if command -v bun >/dev/null; then
      log "Bun $(bun --version) installed"
      JS_RUNNER="bun"; return 0
    fi
  fi
  warn "Bun install failed — falling back to npm"
}

ensure_node() {
  if command -v node >/dev/null; then
    local ver
    ver="$(node -v | sed 's/v//' | cut -d. -f1)"
    if [[ "$ver" -ge "$NODE_REQUIRED_MAJOR" ]]; then
      log "Node.js $(node -v) detected"
      JS_RUNNER="npm"; return 0
    fi
    warn "Node.js $(node -v) detected; need >= ${NODE_REQUIRED_MAJOR}.x"
  else
    warn "Node.js not found"
  fi

  if [[ "$(uname)" == "Linux" ]] && command -v apt-get >/dev/null; then
    log "Installing Node.js ${NODE_REQUIRED_MAJOR}.x via NodeSource…"
    if [[ "$EUID" -ne 0 ]] && ! command -v sudo >/dev/null; then
      fail "Need root or sudo to install Node.js. Install Node.js >= ${NODE_REQUIRED_MAJOR}.x manually and re-run."
    fi
    local SUDO=""
    [[ "$EUID" -ne 0 ]] && SUDO="sudo"
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_REQUIRED_MAJOR}.x" | $SUDO bash -
    $SUDO apt-get install -y nodejs
  else
    fail "Please install Bun (https://bun.sh) or Node.js >= ${NODE_REQUIRED_MAJOR}.x and re-run."
  fi
  JS_RUNNER="npm"
}

ensure_js_runner() {
  ensure_bun
  [[ -z "$JS_RUNNER" ]] && ensure_node
}

# ── Python venv + deps ────────────────────────────────────────────────────
setup_python() {
  need_python
  log "Creating Python virtualenv at ${WEB_DIR}/.venv"
  python3 -m venv "${WEB_DIR}/.venv"
  # shellcheck disable=SC1091
  source "${WEB_DIR}/.venv/bin/activate"
  pip install --upgrade pip wheel >/dev/null
  log "Installing Python dependencies"
  pip install -r "${WEB_DIR}/requirements.txt"
  deactivate
}

# ── .env ──────────────────────────────────────────────────────────────────
seed_env() {
  if [[ ! -f "${WEB_DIR}/.env" ]]; then
    cp "${WEB_DIR}/.env.example" "${WEB_DIR}/.env"
    # Generate a real secret key + pepper
    local secret pepper
    secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
    pepper="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
    sed -i.bak "s|^FLASK_SECRET_KEY=.*|FLASK_SECRET_KEY=${secret}|; s|^HYBRIDSOC_PEPPER=.*|HYBRIDSOC_PEPPER=${pepper}|" "${WEB_DIR}/.env"
    rm -f "${WEB_DIR}/.env.bak"
    log "Wrote ${WEB_DIR}/.env (review SMTP / Turnstile / bootstrap values)"
  else
    log ".env already exists — leaving it untouched"
  fi
}

# ── Migrations + bootstrap ────────────────────────────────────────────────
run_migrations() {
  log "Running SQLite migrations and bootstrapping superadmin"
  ( cd "$REPO_ROOT" && \
    set -a && source "${WEB_DIR}/.env" && set +a && \
    "${WEB_DIR}/.venv/bin/python" -m services.web.migrate --bootstrap )
}

# ── Frontend ──────────────────────────────────────────────────────────────
build_frontend() {
  ensure_js_runner
  log "Installing frontend dependencies (using ${JS_RUNNER})"
  if [[ "$JS_RUNNER" == "bun" ]]; then
    ( cd "$FRONT_DIR" && bun install )
    if [[ "$DEV_MODE" -eq 1 ]]; then
      log "Skipping production build (--dev). Run 'bun run dev' inside ${FRONT_DIR} to start Vite."
    else
      log "Building frontend (bun run build)"
      ( cd "$FRONT_DIR" && bun run build )
    fi
  else
    ( cd "$FRONT_DIR" && npm install --no-audit --no-fund )
    if [[ "$DEV_MODE" -eq 1 ]]; then
      log "Skipping production build (--dev). Run 'npm run dev' inside ${FRONT_DIR} to start Vite."
    else
      log "Building frontend (vite build)"
      ( cd "$FRONT_DIR" && npm run build )
    fi
  fi
}

main() {
  log "HybridSOC Web installer — repo: $REPO_ROOT"
  setup_python
  seed_env
  run_migrations
  if [[ "$WITH_FRONTEND" -eq 1 ]]; then
    build_frontend
  else
    warn "Skipping frontend (--no-frontend)"
  fi

  cat <<EOF

────────────────────────────────────────────────────────────────────
HybridSOC Web is ready.

Start the backend (serves the built frontend on the same port):
  cd ${WEB_DIR}
  source .venv/bin/activate
  set -a && source .env && set +a
  python -m services.web.app          # http://localhost:5000

For frontend hot-reload during development (separate terminal):
  cd ${FRONT_DIR}
  bun run dev                         # http://localhost:5173 (proxies /api → :5000)
  # or, if you prefer npm:
  # npm run dev

Default bootstrap login (change the password immediately):
  email:    \$BOOTSTRAP_EMAIL    (see .env)
  password: \$BOOTSTRAP_PASSWORD (see .env)
────────────────────────────────────────────────────────────────────
EOF
}

main "$@"
