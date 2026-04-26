# AI-Driven HybridSOC with Integrated GRC

> **MSIT Capstone Project** | University of the People | MSIT 5270-01  
> **Author:** Arunas | **Version:** 2.0.0 | **Jurisdiction:** European Union

---

## Overview

HybridSOC is a next-generation Security Operations Center combining:

- **AI-driven detection & automated response** — Isolation Forest, LSTM, LLM-enhanced analysis
- **Zero Trust Architecture** — NIST SP 800-207 compliant, identity-centric, microsegmented
- **IAM + PAM** — Keycloak SSO, HashiCorp Vault, TOTP MFA
- **GRC (Governance, Risk, Compliance)** — ISO 27001:2022, DORA, NIS2, EU AI Act, GDPR
- **Hybrid deployment** — Cloud + On-Premises + MSSP integration
- **Human-AI Collaboration** — AI augments analysts; human-in-the-loop preserved

---

## Python Web Platform (Admin + Analytics)

This project supports a **Python-based website architecture** with:

- **Admin backend** for user, role, policy, and incident administration
- **Frontend analytics views** for SOC statistics, KPIs, and security graphics/charts
- **API control layer** for secure service orchestration and endpoint governance
- **Connection management** between internal microservices and external security tools

### Suggested Implementation Pattern

- **Backend (Python/FastAPI)**
  - Admin modules: users, tenants, RBAC, case/incident workflow
  - API management: rate limits, auth, request validation, audit trails
  - Integrations: SIEM/SOAR/threat intel connectors with health checks
- **Frontend (Dashboard UI)**
  - Security statistics: alerts by severity, MTTR, detection coverage
  - Graphics: trend lines, risk heatmaps, incident distribution charts
  - Operational views: connection status and synchronization metrics
- **Control Plane**
  - API gateway enforcement and token validation
  - Service-to-service trust policies
  - Unified observability for connection reliability and failures

This model enables centralized administration while giving analysts real-time visual insight into platform health, risk posture, and security operations performance.

---

## Architecture

```
Users / Devices
      │
IAM (Keycloak SSO + MFA + HashiCorp Vault PAM)
      │
Zero Trust Gateway (NIST SP 800-207)
      │
Network Security Layer (OPNsense, Suricata, Zeek)
      │
Telemetry Collection (Kafka streaming backbone)
      │
SIEM (Wazuh + Elastic Stack)
      │
Threat Intelligence (MISP + OpenCTI)
      │
AI Analytics Engine (FastAPI + ML pipeline)
      │
SOAR (TheHive + Cortex + Shuffle)
      │
GRC Layer (ISO 27001 / DORA / NIS2 / EU AI Act / GDPR)
      │
Incident Response & Compliance Reporting
```

---

## Key Components

| Layer | Open-Source | Enterprise Alternative |
|---|---|---|
| IAM / SSO | Keycloak | Microsoft Entra ID / Okta |
| PAM | HashiCorp Vault | CyberArk |
| Firewall | OPNsense | Palo Alto NGFW |
| IDS/IPS | Suricata + Zeek | Cisco Firepower |
| SIEM | Wazuh + Elastic | Splunk / IBM QRadar |
| Threat Intel | MISP + OpenCTI | Recorded Future |
| SOAR | TheHive + Cortex | Palo Alto XSOAR |
| AI Engine | FastAPI + scikit-learn | MS Copilot for Security |
| Endpoint | Velociraptor + osquery | CrowdStrike Falcon |
| Orchestration | Kubernetes + ArgoCD | — |

---

## Compliance Frameworks Covered

| Framework | Key Articles / Controls |
|---|---|
| ISO 27001:2022 | Cl.6.1, A.5.x, A.8.x |
| DORA (EU 2022/2554) | Art. 6, 9, 11, 13, 17, 28 |
| NIS2 (EU 2022/2555) | Art. 21(2)(a)–(j) |
| GDPR (EU 2016/679) | Art. 5, 6, 33, 35, 37 |
| EU AI Act (EU 2024/1689) | Art. 5, 6, 9, 13, 14 |

---

## Quick Start

### Docker (Local Development)

```bash
git clone https://github.com/your-org/hybridsoc
cd hybridsoc/docker
cp .env.example .env          # Edit credentials
docker compose up -d
```

**Access points:**

| Service | URL | Default Credentials |
|---|---|---|
| HybridSOC Web (Admin + Dashboard) | http://localhost:5000 | superadmin / `ChangeMeNow!123` (override in `services/web/.env`) |
| Wazuh Dashboard | https://localhost:5601 | admin / (see .env) |
| TheHive | http://localhost:9000 | admin@thehive.local |
| Cortex | http://localhost:9001 | admin |
| AI Engine | http://localhost:8000/docs | — |
| GRC API | http://localhost:8001/docs | — |

### HybridSOC Web — Flask + React 18.3 (Admin & Analytics)

`services/web/` is the consolidated admin and analytics interface described in
[`docs/system-design.md`](docs/system-design.md). Backend: Flask 3 with
blueprints, SQLite (WAL mode) + hash-chained audit log, PBKDF2-SHA256 password
hashing (260 000 iterations + per-user salt + global pepper), TOTP MFA, Email
OTP, and Cloudflare Turnstile. Frontend: React 18.3 / Vite, plain JSX with
inline CSS. Full reference: [`services/web/README.md`](services/web/README.md).

#### One-shot install (Linux/macOS)

```bash
bash scripts/install-web.sh           # backend + frontend build
bash scripts/install-web.sh --dev     # backend + npm install only (no build)
bash scripts/install-web.sh --no-frontend
```

The script detects Python 3.10+, installs Node.js 20.x via NodeSource on
Debian/Ubuntu when missing, creates `services/web/.venv`, installs Python deps,
seeds `services/web/.env` with a freshly generated `FLASK_SECRET_KEY` and
`HYBRIDSOC_PEPPER`, runs migrations, and bootstraps the superadmin.

#### Start the backend (Flask)

```bash
cd services/web
source .venv/bin/activate
set -a && source .env && set +a              # load FLASK_SECRET_KEY, PEPPER, etc.
python -m services.web.migrate                # apply pending migrations (idempotent)
python -m services.web.app                    # http://localhost:5000
```

The Flask app serves the built React bundle on the same port, so once the
frontend has been built the dashboard is reachable directly at
`http://localhost:5000/`. Health probe: `GET /api/health`.

For production / multi-worker:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 'services.web.app:create_app()'
```

#### Start the frontend (React + Vite)

For hot-reload during development (separate terminal from the backend):

```bash
cd services/web/frontend
npm install                                   # first time only
npm run dev                                   # http://localhost:5173 → /api proxied to :5000
```

For a production build (output is served by Flask from `frontend/dist/`):

```bash
cd services/web/frontend
npm run build                                 # produces ./dist
```

Then start Flask as above and open `http://localhost:5000/`.

#### SQLite update service

`services/web/migrate.py` is the schema CLI:

```bash
python -m services.web.migrate              # apply pending migrations
python -m services.web.migrate --status     # show applied vs pending
python -m services.web.migrate --bootstrap  # apply + create superadmin
python -m services.web.migrate --verify     # re-walk the audit hash chain
```

Drop a new `0003_*.sql` file in `services/web/migrations/` and the next backend
start (or `migrate` invocation) will pick it up.

#### Login flow

1. Open `http://localhost:5000/`, sign in with the bootstrap superadmin
   (`BOOTSTRAP_EMAIL` / `BOOTSTRAP_PASSWORD` from `.env`).
2. Pick an MFA method:
   - **Email OTP** — a 6-digit code is sent via SMTP (or printed in the
     backend log when `SMTP_HOST` is empty).
   - **Google TOTP** — once enrolled via `POST /api/auth/totp/enroll` and
     activated via `POST /api/auth/totp/activate`.
3. After verifying the code you receive a Bearer token; the SPA stores it
   in `localStorage` and uses it for subsequent `/api/*` calls.

### Run Admin Backend + Dashboard Frontend

You can run the new **Admin API backend** and **dashboard frontend** in either local Python mode or Docker mode.

#### Option A: Local Python (FastAPI + static frontend)

```bash
cd services/api
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8002 --reload
```

Open:
- API docs: `http://localhost:8002/docs`
- Dashboard UI (frontend): `http://localhost:8002/dashboard`

Authentication flow:
1. Login with email/password at `POST /auth/login`
2. Request MFA challenge via `POST /auth/mfa/challenge` using either:
   - `email_otp` (SMTP-delivered OTP)
   - `google_totp` (Google Authenticator-compatible OTP)
3. Verify OTP at `POST /auth/mfa/verify` to receive a Bearer access token.

Default bootstrap superadmin (change in `.env`):
- Email: `superadmin@hybridsoc.example.com`
- Password: `ChangeMeNow!123`


#### IAM + PAM Notes

- **HashiCorp Vault PAM** is modeled as the primary IAM integration endpoint (`VAULT_ADDR`, `VAULT_ROLE`) and is used for user-provisioning sync hooks.
- **Keycloak SSO** is modeled as the federated SSO integration endpoint (`KEYCLOAK_URL`, `KEYCLOAK_REALM`).
- SQLite is used as the local metadata/auth fallback store for development.

#### Option B: Docker Compose

From the `docker/` folder:

```bash
cd docker
docker compose up -d admin-api
```

Open:
- API docs: `http://localhost:8002/docs`
- Dashboard UI: `http://localhost:8002/dashboard`



### Ansible Deployment Baseline

```bash
cd ansible
ansible-playbook -i inventories/hosts.ini site.yml
```

The playbook includes role scaffolding for:
- Network Security Layer (OPNsense, Suricata, Zeek)
- Telemetry Collection (Kafka)
- SIEM (Wazuh + Elastic)
- Threat Intelligence (MISP + OpenCTI)
- AI Analytics Engine (FastAPI + ML pipeline)
- SOAR (TheHive + Cortex + Shuffle)

### Kubernetes (Enterprise)

```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -k k8s/overlays/prod
```

---

## Research Alignment

This platform is grounded in peer-reviewed research:

- **Bhandari (2025)** — AI improves threat detection accuracy by up to 92.5% and reduces response times by 40%
  `doi:10.1080/07366981.2025.2544363`
- **Zeijlemaker et al. (2025)** — AI transforms systemic cyber risk management through dynamic feedback loops
  `doi:10.3390/systems13100835`
- **Mohsin et al. (2025)** — Unified framework for human-AI collaboration in SOC with trusted autonomy
  `arXiv:2502.xxxxx`
- **NIST SP 800-207** — Zero Trust Architecture baseline
- **MITRE ATT&CK** — Threat detection and SOAR playbook alignment

---

## Repository Structure

```
hybridsoc/
├── README.md            ← This file
├── SECURITY.md          ← Security policy & controls
├── ARCHITECTURE.md      ← Full architecture documentation
├── AI.md                ← AI engine design & ethics
├── INTEGRITY.md         ← Data integrity & trust model
├── API.md               ← REST API reference
├── docker/              ← Docker Compose (dev/local)
├── k8s/                 ← Kubernetes manifests
├── helm/                ← Helm chart
├── argo/                ← ArgoCD GitOps application
├── services/
│   ├── ai-engine/       ← ML/AI microservice (FastAPI)
│   ├── grc-engine/      ← GRC compliance microservice
│   └── api-gateway/     ← API gateway / router
├── kafka/               ← Kafka topic configuration
├── scripts/             ← setup.sh, deploy.sh
└── docs/                ← Extended documentation
```

---

## License

MIT License — see [LICENSE](LICENSE)

---

## References

Bhandari, R. (2025). AI and cybersecurity: Opportunities, challenges, and governance. *EDPACS, 71*(4), 1–9. https://doi.org/10.1080/07366981.2025.2544363

Zeijlemaker, S., Lemiesa, Y. K., Schröer, S. L., Abhishta, A., & Siegel, M. (2025). How does AI transform cyber risk management? *Systems, 13*(10), 835. https://doi.org/10.3390/systems13100835

Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero Trust Architecture* (NIST SP 800-207). NIST. https://doi.org/10.6028/NIST.SP.800-207

NIST. (2024). *Cybersecurity Framework (CSF) 2.0*. https://doi.org/10.6028/NIST.CSWP.29
