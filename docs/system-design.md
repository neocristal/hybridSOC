# HybridSOC — System Requirements Specification & System Design

> MSIT 5270-01 Capstone | Combined SRS and System Design
> Companion: `docs/system-architecture.drawio`, `docs/system-architecture.mmd`

---

## 1. Introduction

Traditional SOCs rely on static, signature-based detection that produces high alert volumes, slow MTTR, and weak alignment with the EU regulatory stack (DORA, NIS2, GDPR, EU AI Act). HybridSOC addresses this gap with an **AI-augmented, Zero-Trust, GRC-integrated** SOC. The platform fuses telemetry from endpoints, network sensors, and identity systems into a Kafka backbone, applies ML analytics, and routes prioritised events to SOAR playbooks — while continuously mapping every event to compliance obligations and preserving human-in-the-loop oversight (Mohsin et al., 2025).

---

## 2. System Components and Interactions

The platform is structured as a **seven-layer stack** with three horizontal microservices.

| Layer | Components | Interaction |
|---|---|---|
| L1 Endpoint | Velociraptor, osquery, Wazuh agents | Push telemetry to L5 |
| L2 Identity | Keycloak SSO, HashiCorp Vault PAM, TOTP MFA | Issues tokens consumed by L3 |
| L3 Zero-Trust Gateway | ZTNA policy engine (NIST SP 800-207) | Verifies every API call |
| L4 Network | OPNsense, Suricata IDS/IPS, Zeek NSM | Emits flows/alerts to L5 |
| L5 Telemetry | Kafka topics (`soc-alerts`, `network-events`, `api-logs`) | Streams to L6 |
| L6 Analytics | Wazuh + Elastic SIEM, MISP/OpenCTI TI, AI Engine | Produces risk scores |
| L7 Response & GRC | TheHive + Cortex + Shuffle SOAR, GRC Engine | Triggers playbooks, files reports |

Cross-cutting microservices — **API Gateway (:8080)**, **AI Engine (:8000)**, **GRC Engine (:8001)** — communicate over REST/JSON with mutual auth, with SQLite (WAL + hash-chain) and Elasticsearch as the persistence tier.

---

## 3. Module-Wise Functional Specification

### 3.1 Identity & Access
- **In:** credentials, TOTP, SSO assertions. **Out:** bearer token, RBAC claims, audit entry.
- **Method:** PBKDF2-SHA256, TOTP RFC 6238, Keycloak OIDC, Vault secret brokering.

### 3.2 Telemetry Ingestion
- **In:** Wazuh alerts, Suricata `eve.json`, Zeek conn logs, EDR events. **Out:** normalised JSON on Kafka.
- **Method:** Beats shippers → Kafka producers → schema validation → Elasticsearch indexing.

### 3.3 AI Risk-Scoring (`services/ai-engine`)
- **In:** event `{user, activity, ip, bytes, timestamp}` (`POST /risk`). **Out:** score 0–100, features, regulatory tags, explanation.
- **Method:** Isolation Forest (anomaly), LSTM (UEBA), graph ML (lateral movement), FAISS RAG for regulatory enrichment, Mistral-7B for commentary. Scores ≥ 75 escalate to SOAR; ≥ 90 require analyst review within 1 h (EU AI Act Art. 14).

### 3.4 SIEM & Threat Intelligence
- **In:** Kafka streams, MISP/OpenCTI feeds. **Out:** alerts mapped to MITRE ATT&CK.
- **Method:** 50+ Wazuh correlation rules, IoC enrichment via Cortex analysers.

### 3.5 SOAR Orchestration
- **In:** AI score above threshold or analyst trigger. **Out:** TheHive case + Shuffle playbook (IP block, account quarantine).
- **Method:** TheHive REST + Cortex + Shuffle; each action logged with score and approver.

### 3.6 GRC Engine (`services/grc-engine`)
- **In:** L6 events, document uploads, risk register entries. **Out:** per-framework scores, DORA Art. 17 / NIS2 Art. 21 timers, DPIA/BCP DOCX/PDF.
- **Method:** rule-based severity-weighted scoring, FAISS RAG over regulatory corpora, timer state-machine.

### 3.7 Admin API & Dashboard (`services/api`)
- **In:** admin actions, dashboard queries. **Out:** KPI charts (MTTR, severity, heatmap), user/role/tenant CRUD.
- **Method:** FastAPI + static frontend at `/dashboard`, Bearer-token auth with MFA challenge.

### 3.8 Integrity Module
- **In:** every write across services. **Out:** append-only audit row with `prev_hash`/`row_hash`.
- **Method:** SHA-256 chain over SQLite WAL; GPG-signed model artefacts verified at load.

---

## 4. Functional Requirements (FRs)

| ID | Requirement |
|---|---|
| FR-1 | The system shall authenticate users via SSO + MFA before granting any API access. |
| FR-2 | The system shall ingest telemetry from Wazuh, Suricata, Zeek, and EDR agents in near real-time (≤ 5 s end-to-end). |
| FR-3 | The AI engine shall return a risk score for any submitted event within 500 ms (p95). |
| FR-4 | Risk scores ≥ 75 shall automatically create a TheHive case; scores ≥ 90 shall additionally trigger a Shuffle playbook. |
| FR-5 | The GRC engine shall start DORA Art. 17 (72 h) and NIS2 Art. 21 timers when an ICT incident is registered. |
| FR-6 | The system shall expose REST endpoints for risk scoring, document upload, risk register, TPRM, audit log, and admin management. |
| FR-7 | Every action shall be written to the immutable hash-chained audit log. |
| FR-8 | The system shall generate DPIA, BCP, and incident reports as DOCX/PDF on demand. |

## 5. Non-Functional Requirements (NFRs)

| Category | Requirement |
|---|---|
| **Performance** | API gateway p95 latency ≤ 200 ms; AI inference p95 ≤ 500 ms; Kafka ingestion ≥ 10 k events/s per broker. |
| **Scalability** | Horizontal scaling via Kubernetes + ArgoCD; stateless microservices behind the API gateway; Kafka partitioning by tenant. |
| **Reliability** | DORA Art. 11 ICT-resilience target: 99.9 % availability; hybrid on-prem/cloud failover; backup retention 12 months. |
| **Security** | Zero-Trust per NIST SP 800-207; TLS 1.3 everywhere; PBKDF2-SHA256 secrets; GPG-signed ML models; least-privilege RBAC. |
| **Usability** | Analyst dashboard reachable in ≤ 3 clicks from login; OpenAPI docs at `/docs`; localisation-ready UI. |
| **Compliance** | Continuous mapping to ISO 27001 A.5/A.8, DORA Art. 6/9/11/17/28, NIS2 Art. 21, GDPR Art. 5/33/35, EU AI Act Art. 6/13/14. |
| **Maintainability** | Containerised microservices, Helm/Kustomize manifests, CI on every PR, SBOM per release. |
| **Auditability** | Hash-chained audit log with tamper detection on read; quarterly bias and drift review of all ML models. |

---

## 6. Design Trade-offs

The hybrid (cloud + on-prem + MSSP) topology was chosen over a pure-cloud SOC because Zeijlemaker et al. (2025) show feedback loops between local telemetry and cloud analytics improve detection of two-step and autonomous attack chains. SQLite-WAL keeps the dev footprint small while satisfying append-only audit needs; production swaps it for PostgreSQL behind the same SQLAlchemy interface. Mistral-7B is used only for commentary — never for autonomous enforcement — to remain within EU AI Act Art. 14.
