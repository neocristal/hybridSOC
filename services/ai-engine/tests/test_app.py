import pytest
from fastapi.testclient import TestClient
from services.ai_engine.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_risk_scoring():
    response = client.post("/risk-score", json={"data": {"key": "value"}})
    assert response.status_code == 200
    assert "score" in response.json()