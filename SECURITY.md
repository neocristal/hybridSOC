# Security Policy

> HybridSOC v2.0.0 | EU-Regulated Deployment | Jurisdiction: European Union

---

## Supported Versions

| Version | Supported | Notes |
|---|---|---|
| 2.0.x | ✅ Active | Current production release |
| 1.0.x | ⚠️ Maintenance | Security patches only |
| < 1.0 | ❌ EOL | No longer supported |

---

## Reporting Vulnerabilities

**Responsible disclosure:** security@hybridsoc.ai

- Response SLA: **72 hours** (critical), **5 business days** (non-critical)
- Coordinated disclosure period: **90 days**
- CVE assignment requested for confirmed vulnerabilities

---

## Security Architecture

### 1. Zero Trust Model

Implementation follows **NIST SP 800-207 Zero Trust Architecture**:

```
never trust, always verify
continuous authentication and authorisation
microsegmentation of all services
identity-centric access control
least-privilege enforcement
```

Per Rose et al. (2020), Zero Trust eliminates implicit trust based on network location, requiring explicit verification of every request regardless of origin.

### 2. Identity & Access Management (IAM)

| Control | Implementation |
|---|---|
| SSO | Keycloak (OIDC / SAML 2.0) |
| MFA | TOTP (RFC 6238) + Email OTP fallback |
| PAM | HashiCorp Vault (dynamic secrets, lease-based) |
| Session tokens | Cryptographically random, server-side, SQLite-stored |
| Password hashing | PBKDF2-SHA256, 260,000 iterations, per-user salt + global PEPPER |
| Account lockout | Progressive delay after failed attempts |
| CAPTCHA | Cloudflare Turnstile (production) |

### 3. Container Security

All containers follow **CIS Docker Benchmark** and **OWASP Container Security**:

```yaml
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

- **No privileged containers**
- **Non-root execution** (dedicated `appuser`)
- **Minimal base images** (python:3.11-slim)
- **No secrets in environment variables** — all via HashiCorp Vault or Kubernetes Secrets

Kubernetes security best practices (CNCF, 2024) mandate RBAC, Pod Security Standards, and network isolation to minimise the attack surface in containerised SOC environments.

### 4. Kubernetes Security Controls

| Control | Configuration |
|---|---|
| RBAC | Role-based, least-privilege per service |
| Network Policies | Default-deny-all; explicit allow rules only |
| Pod Security Standards | `restricted` profile enforced |
| Secrets management | Kubernetes Secrets + Vault Agent Injector |
| Namespace isolation | `hybridsoc` namespace; no cross-namespace access |
| Ingress TLS | TLS 1.3 minimum; certificate via cert-manager |

### 5. SOC Security Controls

| Control | Tool |
|---|---|
| SIEM correlation rules | Wazuh rule engine (MITRE ATT&CK mapped) |
| Network IDS/IPS | Suricata + Zeek (real-time packet inspection) |
| Endpoint protection | Velociraptor + osquery |
| Threat intelligence | MISP + OpenCTI (automated IOC enrichment) |
| Immutable audit log | Append-only SQLite WAL; hash-chained entries |

### 6. Encryption Standards

| Layer | Standard |
|---|---|
| Transport | TLS 1.3 (all internal and external endpoints) |
| Secrets at rest | AES-256-GCM (HashiCorp Vault) |
| Database | SQLite WAL encryption (SQLCipher) |
| Credentials | Never stored in plaintext; no hardcoded secrets |
| API tokens | Bearer tokens, 256-bit random, server-side sessions |

### 7. EU AI Act Compliance (Art. 13 & 14)

The AI engine is classified as **high-risk AI** under EU AI Act Article 6. Controls implemented:

- **Explainability**: every AI finding includes article-level justification
- **Human-in-the-loop**: AI risk scores trigger analyst review, not automated blocking, for scores above threshold
- **Bias monitoring**: model outputs logged and reviewed quarterly
- **Model versioning**: all models signed and version-controlled

### 8. GDPR Controls (Art. 5, 33, 35)

- Data minimisation: only necessary log fields retained
- Retention limits: documents 1 year; statistics 2 years; auto-purge enforced
- Data breach notification: automated DORA Art. 17 / GDPR Art. 33 timer (72-hour threshold)
- DPIA: completed for AI-assisted processing activities
- DPO contact: dpo@hybridsoc.ai

---

## Hardening Checklist

- [ ] Change all default credentials before production deployment
- [ ] Enable TLS on all endpoints (no HTTP in production)
- [ ] Rotate secrets on a 90-day schedule (HashiCorp Vault lease enforcement)
- [ ] Disable unused services and ports
- [ ] Enable Kubernetes Pod Security Standards (`restricted`)
- [ ] Configure Wazuh active response rules
- [ ] Enable Cloudflare Turnstile CAPTCHA
- [ ] Enable audit log forwarding to external SIEM
- [ ] Configure DORA Art. 17 incident notification timers
- [ ] Complete DPIA before production go-live

---

## References

Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). *Zero Trust Architecture* (NIST SP 800-207). NIST. https://doi.org/10.6028/NIST.SP.800-207

European Parliament & Council of the EU. (2024). *Regulation (EU) 2024/1689 — EU AI Act* (Art. 13, 14). https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689

European Parliament & Council of the EU. (2022). *Regulation (EU) 2022/2554 — DORA* (Art. 17). https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R2554

NIST. (2024). *Cybersecurity Framework (CSF) 2.0*. https://doi.org/10.6028/NIST.CSWP.29

Bhandari, R. (2025). AI and cybersecurity: Opportunities, challenges, and governance. *EDPACS, 71*(4), 1–9. https://doi.org/10.1080/07366981.2025.2544363
