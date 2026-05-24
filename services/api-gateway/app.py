"""
HybridSOC API Gateway v2.0.0
Central routing layer for all HybridSOC microservices.
"""

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os

app = FastAPI(
    title="HybridSOC API Gateway",
    version="2.0.0",
    description="Central API gateway routing requests to AI, GRC, and SOAR services.",
)

AI_ENGINE_URL  = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000")
GRC_ENGINE_URL = os.getenv("GRC_ENGINE_URL", "http://grc-engine:8001")
INTERNAL_SECRET = os.getenv("INTERNAL_AUTH_SECRET", "change-me-internal-secret")

security = HTTPBearer()

async def verify_token(auth: HTTPAuthorizationCredentials = Security(security)):
    """
    In production, this would validate the JWT or session token 
    against the Admin API or a Shared Session Store (Redis).
    """
    if not auth or not auth.credentials:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    # For now, we assume if a token is present, it's valid for proxying,
    # but internal services should still verify the INTERNAL_SECRET.
    return auth.credentials

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
async def proxy_risk(payload: dict, token: str = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {INTERNAL_SECRET}"}
        try:
            r = await client.post(f"{AI_ENGINE_URL}/risk", json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"AI Engine error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"AI Engine unreachable: {str(e)}")


@app.post("/api/compliance", tags=["Proxy — GRC"])
async def proxy_compliance(payload: dict, token: str = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {INTERNAL_SECRET}"}
        try:
            r = await client.post(f"{GRC_ENGINE_URL}/compliance", json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"GRC Engine error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"GRC Engine unreachable: {str(e)}")


@app.post("/api/incident", tags=["Proxy — GRC"])
async def proxy_incident(payload: dict, token: str = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {INTERNAL_SECRET}"}
        try:
            r = await client.post(f"{GRC_ENGINE_URL}/incident/classify", json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"GRC Engine error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"GRC Engine unreachable: {str(e)}")
