"""
HybridSOC API Gateway v2.0.0
Central routing layer for all HybridSOC microservices.
"""

from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI(
    title="HybridSOC API Gateway",
    version="2.0.0",
    description="Central API gateway routing requests to AI, GRC, and SOAR services.",
)

AI_ENGINE_URL  = "http://ai-engine:8000"
GRC_ENGINE_URL = "http://grc-engine:8001"


@app.get("/health", tags=["System"])
async def health():
    statuses = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in [("ai_engine", AI_ENGINE_URL), ("grc_engine", GRC_ENGINE_URL)]:
            try:
                r = await client.get(f"{url}/health")
                statuses[name] = "ok" if r.status_code == 200 else "degraded"
            except Exception:
                statuses[name] = "unreachable"
    return {"gateway": "ok", "version": "2.0.0", "services": statuses}


@app.post("/api/risk", tags=["Proxy — AI"])
async def proxy_risk(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{AI_ENGINE_URL}/risk", json=payload)
    return r.json()


@app.post("/api/compliance", tags=["Proxy — GRC"])
async def proxy_compliance(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{GRC_ENGINE_URL}/compliance", json=payload)
    return r.json()


@app.post("/api/incident", tags=["Proxy — GRC"])
async def proxy_incident(payload: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{GRC_ENGINE_URL}/incident/classify", json=payload)
    return r.json()
