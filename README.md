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
| Wazuh Dashboard | https://localhost:5601 | admin / (see .env) |
| TheHive | http://localhost:9000 | admin@thehive.local |
| Cortex | http://localhost:9001 | admin |
| AI Engine | http://localhost:8000/docs | — |
| GRC API | http://localhost:8001/docs | — |

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
