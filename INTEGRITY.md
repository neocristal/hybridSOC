# Integrity & Trust Model

> HybridSOC v2.0.0 | EU-Regulated | GDPR Art. 5 | ISO 27001 A.8 | DORA Art. 9

---

## 1. Overview

The HybridSOC integrity model ensures that all data processed, stored, and transmitted by the platform is authentic, tamper-evident, and fully auditable. Integrity is enforced across three dimensions: **data integrity**, **model integrity**, and **process integrity**.

Per Radanliev et al. (2025), generative AI systems in cybersecurity must embed integrity controls at every layer — not merely at the perimeter — because AI-driven decisions are only as trustworthy as the data and models underpinning them.

---

## 2. Data Integrity

### 2.1 Log Immutability

All security events written to the audit log are **append-only** with no update or delete operations permitted at the database level.

```sql
-- SQLite WAL mode: no DELETE or UPDATE on audit_log
-- Hash chain: each entry includes SHA-256 hash of previous entry
CREATE TABLE audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    action      TEXT NOT NULL,
    details     TEXT,
    ip_address  TEXT,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    prev_hash   TEXT NOT NULL,    -- SHA-256 of previous row
    row_hash    TEXT NOT NULL     -- SHA-256 of this row's content
);
```

Any tampering with a row invalidates the hash chain, which is verified on every audit log access.

### 2.2 Document Hash Validation

All uploaded documents (PDF, DOCX, TXT) are hashed on ingestion:

```python
import hashlib

def hash_document(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

# Stored in documents.content_hash
# Re-verified before every analysis run
```

Duplicate submissions and post-upload modifications are detected automatically.

### 2.3 GDPR Data Minimisation (Art. 5(1)(c))

Only fields strictly necessary for each processing purpose are retained:

| Data Type | Retention | Justification |
|---|---|---|
| Security event logs | 12 months | ISO 27001 A.8.15 / NIS2 Art. 21 |
| Compliance documents | 12 months | DORA Art. 9 |
| User session tokens | Until expiry (max 8h) | GDPR Art. 5(1)(e) |
| AI risk scores | 24 months | GRC audit trail |
| Personal identifiers | Pseudonymised after 90 days | GDPR Art. 5(1)(e) |

Automated purge jobs enforced via scheduled SQLite maintenance tasks.

---

## 3. Model Integrity

### 3.1 Model Versioning and Signing

All ML models are:
- Version-controlled via Git LFS (Large File Storage)
- Tagged with semantic version (e.g., `isolation-forest-v2.1.0`)
- Cryptographically signed using GPG before deployment
- Verified at runtime: signature checked before model load

```bash
# Sign model artifact
gpg --detach-sign --armor isolation_forest_v2.1.0.pkl

# Verify at runtime (ai-engine startup)
gpg --verify isolation_forest_v2.1.0.pkl.asc isolation_forest_v2.1.0.pkl
```

### 3.2 Model Drift Detection

```python
# F1-score monitoring — retraining triggered if drops below threshold
RETRAIN_THRESHOLD = 0.85

current_f1 = evaluate_model(model, validation_set)
if current_f1 < RETRAIN_THRESHOLD:
    trigger_retraining_pipeline()
    notify_team("Model drift detected — retraining initiated")
```

### 3.3 Adversarial Robustness

Per Bhandari (2025), AI systems in cybersecurity are vulnerable to adversarial inputs designed to evade detection. Controls implemented:

- **Input sanitisation**: all log data normalised before feature extraction
- **Outlier rejection**: inputs with feature values > 6σ from training distribution rejected and flagged
- **Ensemble validation**: anomaly flagged only if two or more models agree
- **Canary tokens**: synthetic known-bad events injected monthly to validate detection capability

---

## 4. Process Integrity

### 4.1 Immutable Audit Trail

Every action in the platform — user login, document upload, AI analysis, compliance finding, SOAR playbook execution — is logged to the immutable audit trail with:

- User ID and role
- Action type and parameters
- Source IP address and geolocation
- Timestamp (UTC, millisecond precision)
- Previous row hash (chain validation)
- Row hash (tamper detection)

### 4.2 SOAR Decision Traceability

Every automated SOAR action is linked to:
- The triggering AI risk score
- The specific features that exceeded thresholds
- The analyst who reviewed and approved (for score ≥ 75)
- The regulatory obligation that mandated the action

### 4.3 Separation of Duties

| Role | Permissions |
|---|---|
| `analyst` | View alerts, create cases, run playbooks |
| `manager` | All analyst permissions + close incidents + approve responses |
| `compliance` | View GRC reports, download documents, run questionnaires |
| `admin` | User management, platform configuration, no data access |
| `superadmin` | Full platform access (restricted to 2 accounts max) |

No single role has both administrative and analytical access. This satisfies ISO 27001 A.5.3 (Segregation of duties).

---

## 5. GRC Integrity Controls

### 5.1 Compliance Score Integrity

Compliance scores are calculated deterministically from rule-based checks:

```
Overall Score = Σ(framework_score × framework_weight)
              − Σ(severity_penalty)

Severity penalties:
  Critical  → −4.0 points
  High      → −2.5 points
  Medium    → −1.5 points
  Low       → −0.5 points
```

Scores are recalculated on every document version upload; previous versions retained for diff analysis.

### 5.2 DORA Art. 9 — ICT Risk Management

The platform implements ICT risk management controls required by DORA Art. 9:

- Risk register with quantified likelihood × impact matrices
- Third-party vendor risk assessments (TPRM module)
- Concentration risk monitoring (single-vendor dependency detection)
- Business Continuity Plan (BCP) document generation

---

## 6. Zero Trust Integrity Enforcement

Following NIST SP 800-207, every API request is verified against:

1. **Identity**: valid session token (PBKDF2-SHA256, 256-bit random)
2. **Authorisation**: role-based permission check
3. **Integrity**: request body hash verified against `X-Content-Hash` header
4. **Audit**: request logged before processing begins

No request proceeds without passing all four checks. This satisfies the Zero Trust principle of continuous verification (Rose et al., 2020).

---

## References

Radanliev, P., Santos, O., & Ani, U. D. (2025). Generative AI cybersecurity and resilience. *Frontiers in Artificial Intelligence, 8*. https://doi.org/10.3389/frai.2025.1568360

Bhandari, R. (2025). AI and cybersecurity: Opportunities, challenges, and governance. *EDPACS, 71*(4), 1–9. https://doi.org/10.1080/07366981.2025.2544363

Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero Trust Architecture* (NIST SP 800-207). NIST. https://doi.org/10.6028/NIST.SP.800-207

European Parliament & Council of the EU. (2022). *Regulation (EU) 2022/2554 — DORA* (Art. 9). https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R2554

ISO. (2022). *ISO/IEC 27001: Information security management systems* (A.5.3, A.8.15). https://www.iso.org/standard/27001

Batool, A., Zowghi, D., & Bano, M. (2023). Responsible AI governance: A systematic literature review. *arXiv*. https://arxiv.org/abs/2401.10896
