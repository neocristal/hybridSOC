<#
.SYNOPSIS
    HybridSOC Web — Windows install & bootstrap script (PowerShell).

.DESCRIPTION
    Sets up the Flask backend, the React/Vite frontend (preferring Bun,
    falling back to Node.js + npm), runs SQLite migrations, and creates
    the bootstrap superadmin. Targets Windows 10/11 with Python 3.10+.

.PARAMETER NoFrontend
    Skip the JS install/build entirely.

.PARAMETER Dev
    Install JS dependencies but skip the production build (useful when
    you intend to run `bun run dev` / `npm run dev`).

.EXAMPLE
    PS> .\scripts\install-web.ps1
    PS> .\scripts\install-web.ps1 -Dev
    PS> .\scripts\install-web.ps1 -NoFrontend
#>

[CmdletBinding()]
param(
    [switch]$NoFrontend,
    [switch]$Dev
)

$ErrorActionPreference = 'Stop'
$PyRequiredMinor       = 10
$NodeRequiredMajor     = 20

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$WebDir   = Join-Path $RepoRoot 'services\web'
$FrontDir = Join-Path $WebDir   'frontend'

function Log  { param([string]$m) Write-Host "[install] $m" -ForegroundColor Cyan }
function Warn { param([string]$m) Write-Host "[warn] $m"    -ForegroundColor Yellow }
function Fail { param([string]$m) Write-Host "[fail] $m"    -ForegroundColor Red; exit 1 }

# ── Python ────────────────────────────────────────────────────────────────
function Test-Python {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { Fail "python not found (need >= 3.$PyRequiredMinor). Install from https://www.python.org/downloads/ or 'winget install Python.Python.3.12'." }
    $minor = & python -c "import sys; print(sys.version_info.minor)"
    if ([int]$minor -lt $PyRequiredMinor) { Fail "python >= 3.$PyRequiredMinor required (have 3.$minor)" }
    Log "Python $(& python --version) detected"
}

function Initialize-Python {
    Test-Python
    Log "Creating Python virtualenv at $WebDir\.venv"
    & python -m venv (Join-Path $WebDir '.venv')
    $pip = Join-Path $WebDir '.venv\Scripts\pip.exe'
    & $pip install --upgrade pip wheel | Out-Null
    Log "Installing Python dependencies"
    & $pip install -r (Join-Path $WebDir 'requirements.txt')
}

# ── .env ──────────────────────────────────────────────────────────────────
function Initialize-Env {
    $envFile = Join-Path $WebDir '.env'
    if (Test-Path $envFile) { Log ".env already exists — leaving it untouched"; return }
    Copy-Item (Join-Path $WebDir '.env.example') $envFile
    $secret = & python -c "import secrets; print(secrets.token_urlsafe(48))"
    $pepper = & python -c "import secrets; print(secrets.token_urlsafe(32))"
    (Get-Content $envFile) `
        -replace '^FLASK_SECRET_KEY=.*', "FLASK_SECRET_KEY=$secret" `
        -replace '^HYBRIDSOC_PEPPER=.*', "HYBRIDSOC_PEPPER=$pepper" `
        | Set-Content -Encoding UTF8 $envFile
    Log "Wrote $envFile (review SMTP / Turnstile / bootstrap values)"
}

# ── Migrations + bootstrap ────────────────────────────────────────────────
function Invoke-Migrations {
    Log "Running SQLite migrations and bootstrapping superadmin"
    Push-Location $RepoRoot
    try {
        # Load .env into the current process scope
        $envPath = Join-Path $WebDir '.env'
        if (Test-Path $envPath) {
            Get-Content $envPath | ForEach-Object {
                if ($_ -match '^\s*#') { return }
                if ($_ -match '^\s*([^=\s]+)\s*=\s*(.*)\s*$') {
                    [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
                }
            }
        }
        $py = Join-Path $WebDir '.venv\Scripts\python.exe'
        & $py -m services.web.migrate --bootstrap
    } finally { Pop-Location }
}

# ── Bun (preferred) / Node.js fallback ───────────────────────────────────
function Install-Bun {
    Log "Installing Bun (https://bun.sh)…"
    # Official Windows installer
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm bun.sh/install.ps1 | iex"
    $bunDir = Join-Path $env:USERPROFILE '.bun\bin'
    if (Test-Path (Join-Path $bunDir 'bun.exe')) {
        $env:PATH = "$bunDir;$env:PATH"
        return $true
    }
    return $false
}

function Test-Node {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) { return $false }
    $major = (& node -v).TrimStart('v').Split('.')[0]
    return ([int]$major -ge $NodeRequiredMajor)
}

function Resolve-JsRunner {
    if (Get-Command bun -ErrorAction SilentlyContinue) {
        Log "Bun $(& bun --version) detected"
        return 'bun'
    }
    if (Install-Bun) {
        Log "Bun $(& bun --version) installed"
        return 'bun'
    }
    Warn "Bun unavailable — checking Node.js"
    if (Test-Node) {
        Log "Node.js $(& node -v) detected"
        return 'npm'
    }
    Fail "Need Bun (https://bun.sh) or Node.js >= $NodeRequiredMajor.x. Install one and re-run, e.g. 'winget install OpenJS.NodeJS.LTS' or 'winget install Oven-sh.Bun'."
}

# ── Frontend ──────────────────────────────────────────────────────────────
function Build-Frontend {
    $runner = Resolve-JsRunner
    Log "Installing frontend dependencies (using $runner)"
    Push-Location $FrontDir
    try {
        if ($runner -eq 'bun') {
            & bun install
            if ($Dev) { Log "Skipping build (-Dev). Run 'bun run dev' in $FrontDir to start Vite." }
            else      { Log "Building frontend (bun run build)"; & bun run build }
        } else {
            & npm install --no-audit --no-fund
            if ($Dev) { Log "Skipping build (-Dev). Run 'npm run dev' in $FrontDir to start Vite." }
            else      { Log "Building frontend (npm run build)"; & npm run build }
        }
    } finally { Pop-Location }
}

# ── Main ──────────────────────────────────────────────────────────────────
Log "HybridSOC Web installer (PowerShell) — repo: $RepoRoot"
Initialize-Python
Initialize-Env
Invoke-Migrations
if (-not $NoFrontend) { Build-Frontend } else { Warn "Skipping frontend (-NoFrontend)" }

@"

────────────────────────────────────────────────────────────────────
HybridSOC Web is ready.

Start the backend (serves the built frontend on the same port):
  cd $WebDir
  .\.venv\Scripts\Activate.ps1
  Get-Content .env | ForEach-Object { if (`$_ -match '^([^=]+)=(.*)') { [Environment]::SetEnvironmentVariable(`$matches[1], `$matches[2], 'Process') } }
  python -m services.web.app          # http://localhost:5000

For frontend hot-reload during development (separate terminal):
  cd $FrontDir
  bun run dev                         # http://localhost:5173 (proxies /api -> :5000)
  # or, if you prefer npm:
  # npm run dev

Default bootstrap login (change the password immediately):
  email:    `$BOOTSTRAP_EMAIL    (see .env)
  password: `$BOOTSTRAP_PASSWORD (see .env)
────────────────────────────────────────────────────────────────────
"@
