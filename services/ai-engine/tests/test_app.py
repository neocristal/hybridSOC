import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, compute_risk_score, RiskRequest

client = TestClient(app)

class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"
        assert data["eu_ai_act_compliance"] == "high-risk-art6"

class TestRiskScoringEndpoint:
    def test_risk_score_normal_activity(self):
        payload = {
            "user": "john.doe",
            "activity": "file_read",
            "ip": "192.168.1.100",
            "bytes_transferred": 1024,
            "timestamp": "2026-04-24T12:00:00Z",
            "source": "siem"
        }
        response = client.post("/risk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert 0 <= data["risk_score"] <= 100
        assert "severity" in data
        assert "explanation" in data
        assert data["human_review_required"] == False

    def test_risk_score_volume_spike(self):
        payload = {
            "user": "suspicious_user",
            "activity": "bulk_download",
            "ip": "192.168.1.100",
            "bytes_transferred": 104857601,  # > 100 MB
            "timestamp": "2026-04-24T12:00:00Z"
        }
        response = client.post("/risk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] >= 50
        assert "volume_spike" in data["features_triggered"]

    def test_risk_score_off_hours_activity(self):
        payload = {
            "user": "admin_user",
            "activity": "sudo_command",
            "ip": "10.0.0.1",
            "bytes_transferred": 0,
            "timestamp": "2026-04-24T03:00:00Z"  # Off-hours (3 AM UTC)
        }
        response = client.post("/risk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] >= 50
        assert data["severity"] in ["Medium", "High", "Critical"]

    def test_risk_score_privilege_escalation(self):
        payload = {
            "user": "regular_user",
            "activity": "privilege_escalation_attempt",
            "ip": "192.168.1.50",
            "bytes_transferred": 0
        }
        response = client.post("/risk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "privilege_escalation" in data["features_triggered"]
        assert data["human_review_required"] == True

class TestAnomalyEndpoint:
    def test_anomaly_returns_score(self):
        response = client.post("/anomaly")
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert 1 <= data["risk_score"] <= 100

class TestUEBAEndpoint:
    def test_ueba_normal_deviation(self):
        response = client.post("/ueba?user=john.doe&activity=file_read")
        assert response.status_code == 200
        data = response.json()
        assert data["user"] == "john.doe"
        assert data["activity"] == "file_read"
        assert "deviation_sigma" in data
        assert "baseline_exceeded" in data
        assert data["threshold_sigma"] == 2.5

class TestRiskComputationLogic:
    def test_compute_risk_score_baseline(self):
        req = RiskRequest(
            user="test_user",
            activity="normal",
            ip="192.168.1.1",
            bytes_transferred=1024
        )
        result = compute_risk_score(req)
        assert result["risk_score"] <= 100
        assert result["risk_score"] >= 0
        assert "explanation" in result

    def test_compute_risk_score_regulations(self):
        req = RiskRequest(
            user="test_user",
            activity="bulk_download",
            ip="192.168.1.1",
            bytes_transferred=104857601,
            timestamp="2026-04-24T03:00:00Z"
        )
        result = compute_risk_score(req)
        assert len(result["regulation"]) > 0
        assert any("GDPR" in reg or "ISO" in reg or "NIS2" in reg or "DORA" in reg 
                   for reg in result["regulation"])