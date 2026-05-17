# Discussion Forum: Embedding Ethics and Security into Capstone System Architecture

---

## Introduction

In the MSIT Capstone Project, ethics and security must be load-bearing elements of the architecture itself, not supplementary features added after the fact. This discussion identifies three concrete ethical and security risks relevant to a capstone system, analyzes how module-level design decisions mitigate each, and concludes with a worked example tied to recognized standards including OWASP Top 10, GDPR, and ISO 27001. The capstone system assumed here is a web-based data management platform that collects, processes, and displays user-submitted information—a scenario that surfaces the full range of ethical and security concerns described in the course materials.

---

## Risk 1: Unauthorized Access and Broken Authentication

The first and most pervasive risk in any web-based system is unauthorized access resulting from weak or improperly implemented authentication mechanisms. The OWASP Top 10—one of the most widely recognized frameworks for web application security—lists broken access control and identification/authentication failures consistently among the leading causes of security breaches (OWASP Foundation, 2021). From an architectural standpoint, this risk manifests at every point where the data flow crosses an authentication boundary: login endpoints, API calls, session management, and role-based access decisions.

Letaw (2024) is instructive here, noting that nonfunctional requirements include constraints "limiting how data can be handled" and that quality attributes such as integrity—defined as "how frequently the software loses data"—must be specified as testable thresholds (p. 36, 35). Treating authentication as a nonfunctional requirement rather than an implementation detail forces design teams to articulate explicit criteria: for example, "all API endpoints must require a valid JSON Web Token (JWT) validated against a centralized identity provider" or "session tokens must expire after 15 minutes of inactivity." These become acceptance criteria in the system's requirements specification (SRS), making them verifiable and auditable.

At the module design level, this risk is mitigated through a dedicated authentication and authorization service, implemented as a discrete component in a layered architecture. Walker (2022) describes how a layered architecture enforces separation of concerns, meaning the authentication layer cannot be bypassed by components in adjacent layers. Multi-factor authentication (MFA) is incorporated as a constraint-level nonfunctional requirement, and all password storage employs hashing algorithms aligned with NIST SP 800-63B guidelines. ISO 27001:2022 Annex A Control A.9 (Access Control) provides the formal governance framework that maps these technical decisions to organizational policy, ensuring that access rights are provisioned on the principle of least privilege and reviewed periodically (ISO/IEC, 2022).

---

## Risk 2: Inadequate Data Protection and Privacy Violations

The second major risk concerns the protection of personal data flowing through the system. A system that collects user-submitted information is subject to data minimization, storage limitation, and purpose limitation principles under the General Data Protection Regulation (GDPR), which applies not only to EU-resident users but to any system operated by or for organizations processing EU personal data (European Parliament, 2016). Failure to embed these principles architecturally—rather than relying on procedural controls alone—creates systemic exposure.

Summers (2020) frames this problem in terms of operational requirements: "What environments will the system be expected to operate in effective activities?" (p. 2). For a data-handling system, the legal and regulatory environment is itself a constraint that must be captured in the requirements. Letaw (2024) reinforces this by categorizing data-handling restrictions as a form of nonfunctional constraint that is "often externally mandated" (p. 36). GDPR's Article 5 requirements—lawfulness, fairness, transparency, data minimization, accuracy, storage limitation, integrity, and confidentiality—translate directly into a set of architectural constraints that must be reflected in the system's data flow design.

Concretely, these risks are mitigated through three design decisions. First, a data classification module enforces categorization of all ingested data at the point of entry, tagging records with sensitivity levels that govern downstream processing and retention. Second, encryption is applied at rest (AES-256) and in transit (TLS 1.3), satisfying ISO 27001:2022 Annex A Control A.10 (Cryptography). Third, a consent management component sits upstream of all data collection endpoints, presenting users with granular, revocable consent options. This directly addresses the ethical requirement of informed user consent: users are not assumed to consent by virtue of system usage but must affirmatively and specifically authorize each data processing purpose, consistent with GDPR Article 7 (European Parliament, 2016).

Red Hat (2021) further notes that as automation expands across an organization, "access control, automation orchestration, and trusted content are important to meet corporate security and compliance mandates" (p. 13). This principle applies equally to capstone systems: automated data pipelines must themselves be governed by the same access control and audit mechanisms as human-operated interfaces.

---

## Risk 3: Algorithmic Fairness and Bias in Data Processing

The third risk is more subtle but equally consequential: the potential for algorithmic bias in any component of the system that uses data to make or influence decisions. Even in systems not explicitly described as AI-powered, ranking algorithms, recommendation engines, filtering logic, and search result ordering can produce systematically unfair outcomes if the underlying data reflects historical inequities or if the algorithm's optimization objective is poorly specified.

Letaw (2024) raises this concern directly in the context of requirements elicitation, warning that "stakeholders might want what's bad for them or others" and that developers bear a professional obligation to exercise judgment rather than merely satisfy stated demands (p. 34). The ethical dimension of algorithmic processing is thus not separable from the requirements engineering process—it must be addressed at the specification stage before a single line of code is written.

Mitigating this risk requires embedding fairness as a quality attribute in the system's nonfunctional requirements. Letaw (2024) lists "flexibility" and "interoperability" among quality attributes (p. 35), but fairness and non-discrimination can be added as domain-specific quality attributes with measurable thresholds. For example: "The system's recommendation component must produce outputs that, when evaluated across demographic groups present in the test dataset, show no statistically significant disparity in favorable outcomes exceeding 5 percentage points." This is a verifiable, traceable requirement in the spirit of Summers's (2020) instruction that each requirement "should be stated in such a way that an objective verification and validation can be defined for it" (p. 10).

At the module level, bias risk is mitigated by separating the data ingestion, processing, and output layers so that fairness audits can be applied at each stage without requiring a full system re-test. A dedicated bias evaluation pipeline is incorporated into the CI/CD workflow, running fairness metrics automatically on each build. This approach aligns with the automation governance principles described by Red Hat (2021), which emphasize auditability, accountability, and the ability to "establish clear lines of accountability" within automated processes (p. 14).

---

## Concrete Example: Layered Architecture Supporting Both Ethical Integrity and Secure Operation

To make these principles concrete, consider the system's user registration and consent flow. When a new user submits their registration information, the request passes through the following architectural layers, each implementing specific ethical and security controls:

**Layer 1 – API Gateway (Security):** All incoming requests are validated against rate-limiting rules (OWASP Top 10: A04 Insecure Design) and require a valid CSRF token. TLS 1.3 is enforced at this layer.

**Layer 2 – Authentication Service (Security + Ethics):** The user's credentials are verified against a hashed credential store. MFA is triggered for accounts accessing sensitive data categories. This satisfies ISO 27001:2022 A.9.4 (System and application access control).

**Layer 3 – Consent Management Module (Ethics):** Before any personal data is persisted, the consent module presents the user with a structured consent form specifying each data processing purpose, aligned with GDPR Article 7. Consent records are stored with timestamps and version identifiers, creating an auditable trail.

**Layer 4 – Data Classification Service (Security + Ethics):** Submitted data is tagged with sensitivity classifications. Records containing special-category data under GDPR Article 9 (health, ethnicity, biometrics) are automatically routed to a restricted storage zone with additional encryption and access controls.

**Layer 5 – Audit Log (Governance):** Every action across all layers is logged to an immutable audit trail, satisfying both ISO 27001:2022 A.12.4 (Logging and monitoring) and the GDPR accountability principle of Article 5(2).

This architecture demonstrates how Walker's (2022) layered pattern, when combined with explicit ethical and security requirements, produces a system where each layer has both a functional and a compliance role. The requirements that drove these decisions are traceable—per Summers (2020)—back to specific regulatory obligations and ethical commitments, ensuring that any future audit can verify that the design intent was operationalized correctly (p. 10).

---

## Conclusion

Embedding ethics and security into a capstone system's architecture is not a constraint on good design—it is what good design means in the context of systems that handle real user data. By treating authentication, data protection, and algorithmic fairness as first-class requirements with measurable criteria, and by choosing architectural patterns that enforce these requirements structurally, the capstone system becomes not only functional and scalable but trustworthy. The frameworks discussed—OWASP Top 10, GDPR, and ISO 27001—are not bureaucratic overhead; they are the codified lessons of decades of security failures and ethical missteps that well-designed systems exist to prevent.

---

## References

European Parliament. (2016). *Regulation (EU) 2016/679 of the European Parliament and of the Council of 27 April 2016 (General Data Protection Regulation)*. Official Journal of the European Union. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679

ISO/IEC. (2022). *ISO/IEC 27001:2022 – Information security, cybersecurity and privacy protection*. International Organization for Standardization. https://www.iso.org/standard/27001

Letaw, L. (2024). *Handbook of software engineering methods* [Open textbook]. Oregon State University. https://open.oregonstate.education/setextbook/

OWASP Foundation. (2021). *OWASP Top 10 – 2021*. https://owasp.org/www-project-top-ten/

Red Hat. (2021). *The automation architect's handbook: A guide to leading your company's end-to-end automation journey*. https://www.redhat.com/en/engage/automation-architect-handbook-20210309

Summers, B. L. (2020). *Effective methods for software engineering*. Auerbach Publishers, Incorporated. http://ebookcentral.proquest.com/lib/univ-people-ebooks/detail.action?docID=6267381

Walker, V. (2022, March 16). 14 software architecture design patterns to know. *Red Hat*. https://www.redhat.com/en/blog/14-software-architecture-patterns
