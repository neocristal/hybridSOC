# Architecture

> HybridSOC v2.0.0 — AI-Driven Security Operations Center with Integrated GRC  
> Aligned with: NIST SP 800-207 | MITRE ATT&CK | ISO/IEC 27001:2022 | DORA | NIS2 | EU AI Act

---

## 1. Design Principles

HybridSOC is designed on five foundational principles derived from current academic consensus:

1. **Zero Trust** — Never trust, always verify. Every request authenticated regardless of network location (Rose et al., 2020; NIST SP 800-207).
2. **AI Augmentation** — AI enhances analyst capability; human-in-the-loop preserved for all automated decisions above threshold (Mohsin et al., 2025).
3. **Continuous Compliance** — GRC monitoring is real-time, not periodic. Compliance posture updated on every event.
4. **Telemetry Fusion** — Logs, network, endpoint, and cloud signals unified in a single analytics pipeline.
5. **Resilience by Design** — DORA Art. 11 ICT resilience requirements embedded in architecture.

---

## 2. Seven-Layer Security Model

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Users / Devices / Endpoints                   │
│  Velociraptor agents │ osquery │ Bitdefender             │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Layer 2: Identity (IAM / SSO / MFA / PAM)              │
│  Keycloak │ HashiCorp Vault │ TOTP MFA │ Entra ID        │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Layer 3: Zero Trust Access Control                      │
│  Cloudflare Zero Trust │ Zscaler │ ZTNA policies         │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Layer 4: Network Security                               │
│  OPNsense / pfSense │ Suricata IDS/IPS │ Zeek NSM        │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Layer 5: Telemetry & Streaming                          │
│  Kafka (streaming backbone) │ Elastic Beats │ Wazuh agents│
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Layer 6: SOC Analytics                                  │
│  SIEM: Wazuh + Elastic │ Threat Intel: MISP + OpenCTI   │
│  AI Engine: FastAPI + ML (Isolation Forest / LSTM)       │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Layer 7: Automation, Response & GRC                     │
│  SOAR: TheHive + Cortex + Shuffle                        │
│  GRC: ISO 27001 / DORA / NIS2 / EU AI Act mapping        │
│  DocGen: DPIA / BCP / Incident Reports                   │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow

```
1. Endpoint / Network event occurs
        │
2. Wazuh agent / Zeek / Suricata captures telemetry
        │
3. Kafka ingests event stream (real-time)
        │
4. Elasticsearch indexes raw log data
        │
5. Wazuh SIEM applies 50+ MITRE ATT&CK-mapped correlation rules
        │
6. AI Engine (FastAPI) performs:
   - Anomaly detection (Isolation Forest)
   - Time-series analysis (LSTM)
   - Risk scoring (0–100)
   - FAISS RAG: enriches with regulatory context
        │
7. If risk_score > threshold:
   - TheHive case created
   - Cortex analyser triggered (IOC enrichment, malware analysis)
   - Shuffle playbook executed (IP block / user quarantine / alert)
        │
8. GRC Engine maps event to compliance framework:
   - DORA Art. 17 → 72h notification timer starts if ICT incident
   - NIS2 Art. 21 → significant incident classification
   - ISO 27001 → control gap logged
        │
9. Incident report generated (DOCX / PDF)
10. Audit log entry written (immutable, hash-chained)
```

---

## 4. Hybrid Deployment Model

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   ON-PREMISES    │    │      CLOUD       │    │      MSSP        │
│                  │    │                  │    │                  │
│ Wazuh Manager    │◄──►│ Elastic Cloud    │◄──►│ Threat Intel     │
│ Keycloak IAM     │    │ Kafka Streams    │    │ MISP / OpenCTI   │
│ OPNsense FW      │    │ K8s (EKS/AKS)   │    │ Shared SOC       │
│ Velociraptor EDR │    │ AI Engine        │    │ Incident Sharing │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

**Rationale:** Zeijlemaker et al. (2025) demonstrate that hybrid architectures integrating cloud and on-premises components create feedback loops that improve both deceptive defense capability and real-time risk management.

---

## 5. Microservices Architecture

```
                    ┌─────────────┐
                    │ API Gateway │  :8080
                    │  (FastAPI)  │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼───────┐
    │  AI Engine  │ │ GRC Engine  │ │ SOAR Bridge │
    │  :8000      │ │  :8001      │ │  :8002      │
    │ FastAPI+ML  │ │ Compliance  │ │ TheHive API │
    └──────┬──────┘ └──────┬──────┘ └─────┬───────┘
           │               │               │
    ┌──────▼───────────────▼───────────────▼───────┐
    │                  SQLite WAL / Elasticsearch   │
    └───────────────────────────────────────────────┘
```

---

## 6. Kafka Streaming Backbone

```
[Wazuh agents] ──► [Kafka: soc-alerts]    ──► [AI Engine]
[Suricata]     ──► [Kafka: network-events] ──► [SIEM]
[Zeek]         ──► [Kafka: network-flows]  ──► [Threat Intel]
[API Gateway]  ──► [Kafka: api-logs]       ──► [GRC Engine]
```

Kafka provides the real-time event backbone ensuring no telemetry loss during high-volume security events (Binbeshr et al., 2025).

---

## 7. GRC Integration Model

| Trigger Event | GRC Action | Regulation |
|---|---|---|
| ICT incident detected | 72h notification timer starts | DORA Art. 17 |
| Third-party vendor anomaly | TPRM concentration risk flagged | DORA Art. 28 |
| Significant cybersecurity incident | NIS2 classification + CSIRT notification | NIS2 Art. 21 |
| AI decision made | Explainability log written | EU AI Act Art. 13 |
| Personal data involved | GDPR Art. 33 breach assessment triggered | GDPR Art. 33 |
| New risk identified | Risk register entry created | ISO 27001 Cl. 6.1 |

---

## 8. MITRE ATT&CK Alignment

Wazuh correlation rules are mapped to MITRE ATT&CK tactics:

| Tactic | Detection Method |
|---|---|
| Initial Access | Suricata signatures + Zeek conn logs |
| Execution | osquery process monitoring |
| Persistence | Wazuh FIM (file integrity monitoring) |
| Privilege Escalation | Velociraptor + audit log analysis |
| Lateral Movement | Network flow analysis (Zeek) |
| Exfiltration | AI anomaly detection (data volume spike) |
| Impact | SOAR automated isolation + GRC impact assessment |

---

## References

Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero Trust Architecture* (NIST SP 800-207). NIST. https://doi.org/10.6028/NIST.SP.800-207

Zeijlemaker, S., Lemiesa, Y. K., Schröer, S. L., Abhishta, A., & Siegel, M. (2025). How does AI transform cyber risk management? *Systems, 13*(10), 835. https://doi.org/10.3390/systems13100835

Mohsin, A., Janicke, H., Ibrahim, A., Sarker, I. H., & Camtepe, S. (2025). A unified framework for human-AI collaboration in security operations centers with trusted autonomy. *arXiv*. https://arxiv.org/abs/2502.00000

Binbeshr, F., et al. (2025). The rise of cognitive SOCs: A systematic literature review on AI approaches. *IEEE Open Journal of the Computer Society*.

MITRE Corporation. (2024). *ATT&CK® for Enterprise v15*. https://attack.mitre.org/

ISO. (2022). *ISO/IEC 27001: Information security management systems — Requirements*. https://www.iso.org/standard/27001

European Parliament & Council of the EU. (2022). *Regulation (EU) 2022/2554 — DORA*. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R2554

European Parliament & Council of the EU. (2022). *Directive (EU) 2022/2555 — NIS2*. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022L2555
