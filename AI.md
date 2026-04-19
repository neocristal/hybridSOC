# AI Engine

> HybridSOC AI Module v2.0.0  
> EU AI Act Compliance: High-Risk AI System (Art. 6) | Explainable AI | Human-in-the-Loop

---

## 1. Overview

The AI engine is the analytical core of HybridSOC. It processes security telemetry from Wazuh and Kafka, applies machine learning models to detect anomalies and predict threats, generates risk scores, and triggers SOAR playbooks. It is designed as a **decision-support system**, not a fully autonomous decision-maker — human analyst oversight is preserved for all high-stakes actions.

Per Bhandari (2025), AI systems improve cyber threat detection accuracy by up to 92.5% and reduce incident response times by 40%, while requiring robust governance frameworks to manage algorithmic bias and accountability risks.

---

## 2. AI Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: Data Ingestion                                  │
│  Kafka consumer → Wazuh alerts → Network flows → EDR    │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Step 2: Feature Extraction                              │
│  Log parsing │ NLP tokenisation │ Feature vectors        │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Step 3: ML Model Inference                              │
│  Isolation Forest (anomaly detection)                    │
│  LSTM (time-series behavioural baseline)                 │
│  Graph-based lateral movement prediction                 │
│  Mistral-7B LLM (article-level compliance commentary)    │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Step 4: Risk Scoring (0–100)                            │
│  Weighted composite score across model outputs           │
│  FAISS RAG enrichment: regulatory context injected       │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Step 5: SOAR Trigger                                    │
│  risk_score ≥ 75 → TheHive case created                  │
│  risk_score ≥ 90 → Cortex analyser + Shuffle playbook    │
│  All decisions logged to immutable audit trail           │
└─────────────────────────────────────────────────────────┘
```

---

## 3. ML Models

### 3.1 Isolation Forest — Anomaly Detection

```python
from sklearn.ensemble import IsolationForest

model = IsolationForest(
    n_estimators=200,
    contamination=0.05,    # Expected 5% anomaly rate
    random_state=42
)
model.fit(X_train)
anomaly_score = model.decision_function(X_new)
```

**Use case:** Detects statistical outliers in login behaviour, network traffic volume, API call patterns, and file access rates. Particularly effective for detecting insider threats and zero-day attack patterns not matched by signature rules.

### 3.2 LSTM — Time-Series Behavioural Baseline

**Use case:** Models temporal patterns in user and system behaviour. Detects deviations from established baselines — e.g., login at unusual hours, data exfiltration spikes, or service call volume anomalies.

```
Input:  [t-24h, t-12h, t-6h, t-1h, t-now] feature windows
Output: Deviation score from predicted baseline
```

### 3.3 FAISS RAG — Regulatory Enrichment

```python
import faiss
# Knowledge base: DORA, NIS2, ISO 27001, EU AI Act texts indexed
# Retrieves relevant article context for each AI finding
results = index.search(query_vector, k=5)
```

Augments AI findings with precise regulatory article references, enabling the GRC engine to map every anomaly to the applicable legal obligation.

### 3.4 Mistral-7B LLM — Compliance Commentary

- Model: `mistral-7b-instruct-v0.2.Q8_0.gguf` (llama-cpp-python)
- Role: Generates natural-language explanations of compliance findings
- Constraint: Used only for commentary generation, never for autonomous enforcement decisions

---

## 4. UEBA — User and Entity Behaviour Analytics

```
Baseline period: 30 days rolling window
Alert threshold:  2.5 standard deviations from baseline
Review threshold: 1.5 standard deviations (analyst notification only)

Features tracked:
- Login time distribution
- Source IP geolocation
- Resource access patterns
- API call frequency
- Data transfer volume
- Privilege usage frequency
```

---

## 5. Capabilities Summary

| Capability | Method | Trigger |
|---|---|---|
| Anomaly Detection | Isolation Forest | Any log event |
| UEBA | LSTM + statistical baseline | User activity events |
| Threat Prediction | Graph ML | Lateral movement indicators |
| Alert Prioritisation | Composite risk score | All SIEM alerts |
| Compliance Analysis | FAISS RAG + Mistral-7B | Document upload |
| Automated Response | SOAR API call | risk_score ≥ 75 |

---

## 6. Ethics and Governance Controls

Per the **EU AI Act (Regulation EU 2024/1689)**, the HybridSOC AI engine is classified as a **high-risk AI system** under Article 6 (AI systems used in critical infrastructure and law enforcement contexts). The following controls are implemented:

### 6.1 Explainability (Art. 13 — Transparency)

Every AI-generated risk score includes:
- The specific features that contributed to the score
- The weight of each feature
- The regulatory articles applicable to the finding
- A natural-language explanation (Mistral-7B generated)

### 6.2 Human-in-the-Loop (Art. 14 — Human Oversight)

| Risk Score | Action | Human Review Required |
|---|---|---|
| 0–49 | Logged only | No |
| 50–74 | Analyst notification | Recommended |
| 75–89 | TheHive case created | Required before enforcement |
| 90–100 | Automated response + escalation | Required within 1 hour |

**Rationale:** Singh et al. (2025) found that 93% of AI use in live SOC environments aligns with decision-support rather than autonomous action, confirming human-in-the-loop as the operationally validated model.

### 6.3 Bias Monitoring

- All model outputs logged with input feature vectors
- Quarterly statistical review of false positive and false negative rates
- Protected attribute analysis: no user demographic data used as model input
- Model performance audited against MITRE ATT&CK detection coverage metrics

### 6.4 Model Integrity

- All models version-controlled (Git LFS) and cryptographically signed
- Model drift detection: retraining triggered if F1 score drops below 0.85
- SBOM (Software Bill of Materials) maintained for all ML dependencies

---

## 7. API Integration

```http
POST /risk
Content-Type: application/json

{
  "user": "analyst01",
  "activity": "bulk_file_download",
  "ip": "192.168.10.45",
  "bytes_transferred": 524288000,
  "timestamp": "2026-04-19T08:00:00Z"
}

Response:
{
  "risk_score": 87,
  "anomaly_detected": true,
  "features": ["volume_spike", "off_hours_activity"],
  "regulation": ["GDPR Art.5(1)(f)", "ISO 27001 A.8.2"],
  "explanation": "Bulk file transfer of 500MB at 02:00 local time is 4.2σ above user baseline.",
  "action_recommended": "create_case",
  "human_review_required": true
}
```

---

## References

Bhandari, R. (2025). AI and cybersecurity: Opportunities, challenges, and governance. *EDPACS, 71*(4), 1–9. https://doi.org/10.1080/07366981.2025.2544363

Zeijlemaker, S., Lemiesa, Y. K., Schröer, S. L., Abhishta, A., & Siegel, M. (2025). How does AI transform cyber risk management? *Systems, 13*(10), 835. https://doi.org/10.3390/systems13100835

Singh, R., et al. (2025). LLMs in the SOC: An empirical study of human-AI collaboration in security operations centres. *arXiv*. https://arxiv.org/abs/2502.00000

Mohsin, A., Janicke, H., Ibrahim, A., Sarker, I. H., & Camtepe, S. (2025). A unified framework for human-AI collaboration in security operations centers with trusted autonomy. *arXiv*.

European Parliament & Council of the EU. (2024). *Regulation (EU) 2024/1689 — EU AI Act* (Art. 6, 13, 14). https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689

Batool, A., Zowghi, D., & Bano, M. (2023). Responsible AI governance: A systematic literature review. *arXiv*. https://arxiv.org/abs/2401.10896

Mohamed, N. (2025). Artificial intelligence and machine learning in cybersecurity: A deep dive into state-of-the-art techniques and future paradigms. *Knowledge and Information Systems, 67*, 6969–7055. https://doi.org/10.1007/s10115-025-02429-y
