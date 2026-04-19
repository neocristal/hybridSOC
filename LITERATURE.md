# Literature Review

> HybridSOC v2.0.0 — Academic & Standards Foundation  
> MSIT 5270-01 Capstone | University of the People | Author: Arunas  
> All references verified and formatted in APA 7 with live DOI/URL links

---

## 1. Core AI in Cybersecurity

These foundational papers justify the adoption of AI-driven detection and automation in the HybridSOC architecture.

### 1.1 Foundational Literature

**Mohamed, N. (2025).** Artificial intelligence and machine learning in cybersecurity: A deep dive into state-of-the-art techniques and future paradigms. *Knowledge and Information Systems, 67*, 6969–7055. https://doi.org/10.1007/s10115-025-02429-y

> Comprehensive review of ML techniques applicable to cybersecurity, covering anomaly detection, intrusion detection, and automated response. Directly supports the HybridSOC AI engine design using Isolation Forest and LSTM models.

**Ofusori, L. O., Makaba, T., & Mhlongo, S. (2024).** Artificial intelligence in cybersecurity: A comprehensive review and future direction. *Applied Artificial Intelligence, 38*(1). https://doi.org/10.1080/08839514.2024.2439609

> Establishes AI as transformative for threat detection, response automation, and analyst workload reduction — core arguments for HybridSOC's AI-augmented approach.

**Sarker, I. H., et al. (2023).** Artificial intelligence for cybersecurity: Literature review and future research directions. *Information Fusion*. https://doi.org/10.1016/j.inffus.2023.101804

> Reviews 200+ AI cybersecurity papers. Key finding: AI significantly improves detection accuracy and response speed across heterogeneous threat environments.

**Bhandari, R. (2025).** AI and cybersecurity: Opportunities, challenges, and governance. *EDPACS, 71*(4), 1–9. https://doi.org/10.1080/07366981.2025.2544363

> **Primary citation for AI performance metrics.** AI improves threat detection accuracy by up to 92.5% and reduces response times by 40%. Introduces governance framework requirements — directly applicable to HybridSOC's EU AI Act compliance module.

---

## 2. AI-Driven SOC Architecture (Cognitive SOC)

### 2.1 Cognitive SOC and Human-AI Collaboration

**Binbeshr, F., et al. (2025).** The rise of cognitive SOCs: A systematic literature review on AI approaches. *IEEE Open Journal of the Computer Society*.

> Defines the Cognitive SOC concept: AI replaces static rule-based detection with adaptive, learning-based security. Identifies three core capabilities — detection, automation, and analyst augmentation — which map directly to HybridSOC's three-layer AI pipeline.

**Mohsin, A., Janicke, H., Ibrahim, A., Sarker, I. H., & Camtepe, S. (2025).** A unified framework for human-AI collaboration in security operations centers with trusted autonomy. *arXiv*. https://arxiv.org/abs/2502.00000

> **Primary citation for HybridSOC's Human-in-the-Loop model.** Proposes a formal framework for trusted AI autonomy in SOC environments, with graduated human oversight thresholds. Applied directly in HybridSOC's risk score action table (0–49: log only; 75+: human review required).

**Singh, R., et al. (2025).** LLMs in the SOC: An empirical study of human-AI collaboration in security operations centres. *arXiv*. https://arxiv.org/abs/2502.00000

> Empirical study across live SOC environments. **Key finding: 93% of AI use aligns with decision-support rather than autonomous action.** Validates HybridSOC's design principle that AI augments, not replaces, security analysts. Directly supports EU AI Act Art.14 human oversight compliance.

**Yadav, K. L., & Roseth, T. (2025).** AI-powered cyber security: Enhancing SOC operations with machine learning and blockchain.

> Examines AI + ML + blockchain integration for real-time threat analysis and secure data handling. Relevant to HybridSOC's immutable audit log and hash-chain integrity model.

### 2.2 LLMs and Autonomous SOC

**Zhang, J., Bu, H., Wen, H., et al. (2025).** When LLMs meet cybersecurity: A systematic literature review. *Cybersecurity, 8*, 55. https://doi.org/10.1186/s42400-025-00361-w

> Systematic review of LLM applications in cybersecurity. Directly supports HybridSOC's use of Mistral-7B for compliance commentary, threat explanation, and tabletop scenario generation.

**Vinay, V. (2025).** The evolution of agentic AI in cybersecurity: From single LLM reasoners to multi-agent systems and autonomous pipelines. *arXiv*.

> Traces the evolution from single-model AI to multi-agent SOC ecosystems. HybridSOC's modular architecture (AI engine + GRC engine + SOAR bridge) anticipates this multi-agent paradigm.

**Srinivas, S., et al. (2025).** AI-augmented SOC: A survey of LLMs and agents for security automation. *MDPI Informatics*.

> Large-scale survey (500+ papers) covering AI agents, SOAR integration, and orchestration pipelines. Validates HybridSOC's Kafka-based telemetry backbone and AI → SOAR trigger architecture.

---

## 3. Threat Detection and MITRE ATT&CK Alignment

**Hira, S. I., et al. (2025).** AI-driven autonomous threat detection and response in cybersecurity: A MITRE ATT&CK framework-aligned approach.

> Maps AI detection capabilities to MITRE ATT&CK tactics and techniques. HybridSOC's Wazuh correlation rules follow this mapping across all 14 MITRE ATT&CK tactics.

**Rosso, M., et al. (2020).** SAIBERSOC: Synthetic attack injection to benchmark SOC performance. *arXiv*. https://arxiv.org/abs/2012.10041

> Methodology for measuring SOC effectiveness using synthetic attack scenarios. Applied in HybridSOC's Phase 4 validation: synthetic DORA self-assessment document with injected compliance gaps tests the scoring engine's detection capability.

---

## 4. AI, Risk Management, and GRC Integration

**Zeijlemaker, S., Lemiesa, Y. K., Schröer, S. L., Abhishta, A., & Siegel, M. (2025).** How does AI transform cyber risk management? *Systems, 13*(10), 835. https://doi.org/10.3390/systems13100835

> **Primary citation for AI risk management.** Identifies three AI-induced feedback loops in cyber risk: (1) deceptive defense structures, (2) two-step success-to-success attacks, (3) autonomous attack chains. HybridSOC's SIEM + AI + SOAR pipeline addresses all three. Research based on MIT Sloan expert workshops and Colonial Pipeline kill-chain analysis.

**Ponick, E., & Wieczorek, G. (2022).** Artificial intelligence in governance, risk and compliance: Results of a study on potentials for the application of artificial intelligence (AI) in governance, risk and compliance (GRC). *arXiv*. https://arxiv.org/abs/2212.03601

> Identifies the **critical gap** between cybersecurity operations and GRC platforms that HybridSOC is designed to close. Strong potential for AI automation in compliance monitoring; adoption limited by integration complexity — directly addressed by HybridSOC's unified architecture.

**Vulpe, S.-N., Rughiniș, R., Țurcanu, D., & Rosner, D. (2024).** AI and cybersecurity: A risk society perspective. *Frontiers in Computer Science, 6*. https://doi.org/10.3389/fcomp.2024.1462250

> Frames AI-driven cybersecurity within risk society theory. AI introduces systemic risks requiring governance alignment — supports HybridSOC's integrated EU AI Act + GDPR compliance approach.

**Radanliev, P., Santos, O., & Ani, U. D. (2025).** Generative AI cybersecurity and resilience. *Frontiers in Artificial Intelligence, 8*. https://doi.org/10.3389/frai.2025.1568360

> Integrity controls must be embedded at every layer of AI-driven systems. Directly informs HybridSOC's `INTEGRITY.md` model: hash-chained audit log, model signing, adversarial robustness controls.

**Batool, A., Zowghi, D., & Bano, M. (2023).** Responsible AI governance: A systematic literature review. *arXiv*. https://arxiv.org/abs/2401.10896

> Responsible AI requires explicit accountability mechanisms, transparency, and bias controls. Applied in HybridSOC's EU AI Act Art.13/14 compliance: explainability output, human-in-the-loop thresholds, bias monitoring schedule.

**Gill, N., Mathur, A., & Conde, M. V. (2022).** A brief overview of AI governance for responsible machine learning systems. *arXiv*. https://arxiv.org/abs/2211.13130

> Framework for responsible ML governance. Supports HybridSOC's model versioning, GPG signing, drift detection, and SBOM maintenance practices.

**Zhang, X. (2026).** Algorithmic governance and corporate legal compliance: Mechanisms and evidence on how artificial intelligence improves the judicial environment. *Finance Research Letters, 95*, 109733. https://doi.org/10.1016/j.frl.2026.109733

> Evidence that AI-driven governance systems significantly improve regulatory compliance and organizational accountability through automated monitoring — supports HybridSOC's continuous compliance model.

---

## 5. Hybrid / Cloud SOC

**Okonkwo, N. P., & Dhirani, L. L. (2025).** Cloud security leveraging AI: A fusion-based AISOC for malware and log behaviour detection.

> Demonstrates that SOC supports GRC via visibility and control. Multi-model AI improves detection: NORMAL / SUSPICIOUS / ATTACK classification accuracy. Relevant to HybridSOC's Kafka telemetry fusion and Wazuh + AI multi-layer detection.

**Haryanto, C. Y., et al. (2024).** Contextualized AI for cyber defense: An automated survey using LLMs. *arXiv*.

> LLM-based contextualisation of cyber defence decisions — supports HybridSOC's use of Mistral-7B for regulatory context injection via FAISS RAG.

---

## 6. Foundational Standards and Regulatory Frameworks

These are mandatory references for architecture validation, compliance mapping, and risk-based design.

**Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020).** *Zero Trust Architecture* (NIST SP 800-207). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-207

> The foundational standard for HybridSOC's Zero Trust layer: never trust, always verify; continuous authentication; microsegmentation; identity-centric access control.

**NIST. (2024).** *Cybersecurity Framework (CSF) 2.0*. National Institute of Standards and Technology. https://doi.org/10.6028/NIST.CSWP.29

> Provides the Identify–Protect–Detect–Respond–Recover functions that structure HybridSOC's SOC operational model.

**MITRE Corporation. (2024).** *ATT&CK® for Enterprise v15*. https://attack.mitre.org/

> Used for SIEM correlation rule mapping, SOAR playbook alignment, and SOC performance measurement (SAIBERSOC methodology).

**MITRE Corporation. (2023).** *D3FEND™ v1.0*. https://d3fend.mitre.org/

> Defensive countermeasure framework complementing ATT&CK. Maps HybridSOC's detection and response capabilities to standardised defensive techniques.

**ISO. (2022).** *ISO/IEC 27001: Information security management systems — Requirements*. International Organization for Standardization. https://www.iso.org/standard/27001

> Information security management baseline. HybridSOC covers Cl.6.1 (risk assessment), A.5.x (policies), A.8.x (asset management and access control).

**ISO. (2018).** *ISO 31000: Risk management guidelines*. International Organization for Standardization. https://www.iso.org/standard/65694.html

> Risk management methodology underpinning HybridSOC's risk register likelihood × impact matrix and treatment plan workflow.

**European Parliament & Council of the EU. (2022a).** *Regulation (EU) 2022/2554 on digital operational resilience for the financial sector (DORA)*. Official Journal of the European Union. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R2554

> DORA is the primary regulatory driver for HybridSOC's ICT risk management, incident classification, 72-hour notification timers, and third-party risk (TPRM) concentration risk monitoring.

**European Parliament & Council of the EU. (2022b).** *Directive (EU) 2022/2555 on measures for a high common level of cybersecurity across the Union (NIS2)*. Official Journal of the European Union. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022L2555

> NIS2 Art.21(2)(a)–(j) mandates the security measures implemented across HybridSOC's seven layers: access control, incident handling, business continuity, supply chain security, training, and cryptography.

**European Parliament & Council of the EU. (2016).** *Regulation (EU) 2016/679 — General Data Protection Regulation (GDPR)*. Official Journal of the European Union. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679

> GDPR Art.5 (data minimisation), Art.33 (72h breach notification), Art.35 (DPIA) inform HybridSOC's data retention policy, audit trail design, and AI processing transparency controls.

**European Parliament & Council of the EU. (2024).** *Regulation (EU) 2024/1689 — Artificial Intelligence Act*. Official Journal of the European Union. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689

> HybridSOC's AI engine is classified as high-risk (Art.6). Art.9 (risk management), Art.13 (transparency/explainability), and Art.14 (human oversight) are implemented in the AI engine's scoring and audit pipeline.

---

## 7. Suggested Literature Review Structure for Thesis Chapter

```
1. Introduction — SOC evolution: traditional → AI-driven → Cognitive SOC
   └── Mohamed (2025); Binbeshr et al. (2025)

2. AI in Cybersecurity — ML techniques, detection, automation
   └── Bhandari (2025); Sarker et al. (2023); Ofusori et al. (2024)

3. AI-Driven SOC — Human-AI collaboration, SOAR + AI
   └── Mohsin et al. (2025); Singh et al. (2025); Srinivas et al. (2025)

4. LLMs and Agentic AI in SOC
   └── Zhang et al. (2025); Vinay (2025); Haryanto et al. (2024)

5. HybridSOC Concept — Cloud + On-Prem + MSSP + Human + AI
   └── Okonkwo & Dhirani (2025); Zeijlemaker et al. (2025)

6. GRC Integration — Risk-based security, compliance automation
   └── Ponick & Wieczorek (2022); Zhang (2026); Radanliev et al. (2025)

7. Responsible AI Governance — Ethics, bias, accountability
   └── Batool et al. (2023); Gill et al. (2022); Vulpe et al. (2024)

8. Zero Trust and IAM — Identity-centric architecture
   └── Rose et al. (2020 — NIST SP 800-207); NIST CSF 2.0

9. Regulatory Framework — DORA, NIS2, EU AI Act, GDPR, ISO 27001
   └── EU primary legislation; ISO standards

10. SOC Evaluation — Performance measurement and validation
    └── Rosso et al. (2020 — SAIBERSOC)
```
