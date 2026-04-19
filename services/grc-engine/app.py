"""
HybridSOC GRC Engine v2.0.0
Governance, Risk & Compliance microservice.
Covers: ISO 27001:2022 | DORA | NIS2 | GDPR | EU AI Act
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

app = FastAPI(
    title="HybridSOC GRC Engine",
    version="2.0.0",
    description="Multi-framework GRC compliance engine for EU-regulated organizations.",
)

FRAMEWORKS = {
    "ISO27001": {"weight": 0.20, "articles": ["Cl.6.1", "A.5.x", "A.8.x"]},
    "DORA":     {"weight": 0.20, "articles": ["Art.6", "Art.9", "Art.11", "Art.13", "Art.17", "Art.28"]},
    "NIS2":     {"weight": 0.15, "articles": ["Art.21(2)(a)-(j)"]},
    "GDPR":     {"weight": 0.15, "articles": ["Art.5", "Art.6", "Art.33", "Art.35", "Art.37"]},
    "EUAI":     {"weight": 0.10, "articles": ["Art.5", "Art.6", "Art.9", "Art.13", "Art.14"]},
    "AML":      {"weight": 0.10, "articles": ["AMLD5/6", "CDD", "KYC"]},
    "MiCA":     {"weight": 0.10, "articles": ["Art.34", "Art.70", "Art.76", "Art.86"]},
}


class ComplianceRequest(BaseModel):
    framework: str
    document_id: Optional[int] = None
    context: Optional[str] = ""


class IncidentRequest(BaseModel):
    title: str
    severity: str
    type: str
    frameworks: list[str]


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "grc-engine", "version": "2.0.0"}


@app.post("/compliance", tags=["GRC"])
def compliance(req: ComplianceRequest):
    """Returns compliance mapping for the requested framework."""
    fw = req.framework.upper()
    meta = FRAMEWORKS.get(fw)
    if not meta:
        return {"error": f"Framework {fw} not supported", "supported": list(FRAMEWORKS.keys())}
    return {
        "framework": fw,
        "status": "mapped",
        "weight": meta["weight"],
        "key_articles": meta["articles"],
        "maturity_level": 3,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/incident/classify", tags=["GRC"])
def classify_incident(req: IncidentRequest):
    """
    Classifies an ICT incident and returns regulatory notification deadlines.
    DORA Art.17: major ICT incidents — initial notification within 4h, detailed report within 72h.
    NIS2 Art.21: significant incidents — early warning within 24h, notification within 72h.
    """
    now = datetime.now(timezone.utc)
    deadlines = {}

    if "DORA" in req.frameworks:
        deadlines["DORA_Art17_initial"] = (now + timedelta(hours=4)).isoformat()
        deadlines["DORA_Art17_detailed"] = (now + timedelta(hours=72)).isoformat()

    if "NIS2" in req.frameworks:
        deadlines["NIS2_Art21_early_warning"] = (now + timedelta(hours=24)).isoformat()
        deadlines["NIS2_Art21_notification"] = (now + timedelta(hours=72)).isoformat()

    if "GDPR" in req.frameworks:
        deadlines["GDPR_Art33_notification"] = (now + timedelta(hours=72)).isoformat()

    return {
        "incident_id": None,
        "title": req.title,
        "severity": req.severity,
        "type": req.type,
        "frameworks": req.frameworks,
        "notification_deadlines": deadlines,
        "status": "open",
        "created_at": now.isoformat(),
    }


@app.get("/frameworks", tags=["GRC"])
def list_frameworks():
    """Lists all supported compliance frameworks with weights."""
    return {"frameworks": FRAMEWORKS}
