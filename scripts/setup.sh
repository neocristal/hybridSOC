#!/bin/bash
# HybridSOC Setup Script
# Usage: ./scripts/setup.sh

set -euo pipefail

echo "╔══════════════════════════════════════════════════════╗"
echo "║   HybridSOC Enterprise Setup v2.0.0                 ║"
echo "║   AI-Driven SOC + GRC | EU-Regulated                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Preflight checks ─────────────────────────────────────────────
echo "[1/5] Checking prerequisites..."
command -v docker   >/dev/null 2>&1 || { echo "ERROR: docker not found"; exit 1; }
command -v docker   >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 || { echo "ERROR: docker compose not found"; exit 1; }
echo "      ✅ Docker OK"

# ── Environment file ─────────────────────────────────────────────
echo "[2/5] Checking environment configuration..."
if [ ! -f "docker/.env" ]; then
    cp docker/.env.example docker/.env
    echo "      ⚠️  Created docker/.env from .env.example"
    echo "      ⚠️  IMPORTANT: Edit docker/.env and set all passwords before continuing"
    read -p "      Press ENTER after editing .env to continue..." _
fi
echo "      ✅ Environment file OK"

# ── Build images ─────────────────────────────────────────────────
echo "[3/5] Building HybridSOC service images..."
docker build -t hybridsoc/ai-engine:2.0.0  services/ai-engine/
docker build -t hybridsoc/grc-engine:2.0.0 services/grc-engine/
docker build -t hybridsoc/api-gateway:2.0.0 services/api-gateway/
echo "      ✅ Images built"

# ── Start stack ───────────────────────────────────────────────────
echo "[4/5] Starting HybridSOC stack..."
cd docker
docker compose up -d
cd ..
echo "      ✅ Stack started"

# ── Health check ─────────────────────────────────────────────────
echo "[5/5] Waiting for services to become healthy..."
sleep 15
AI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
GRC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   HybridSOC Service Status                          ║"
echo "╠══════════════════════════════════════════════════════╣"
printf "║  %-30s %s\n"  "AI Engine   (port 8000):" "HTTP $AI_STATUS  ║"
printf "║  %-30s %s\n"  "GRC Engine  (port 8001):" "HTTP $GRC_STATUS  ║"
echo "║  Wazuh Dashboard  (port 5601): https://localhost:5601 ║"
echo "║  TheHive SOAR     (port 9000): http://localhost:9000  ║"
echo "║  Cortex           (port 9001): http://localhost:9001  ║"
echo "║  Keycloak IAM     (port 8180): http://localhost:8180  ║"
echo "║  API Gateway      (port 8080): http://localhost:8080  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "API Docs:  http://localhost:8000/docs  (AI Engine)"
echo "           http://localhost:8001/docs  (GRC Engine)"
echo "           http://localhost:8080/api/redoc (Gateway)"
echo ""
echo "✅ HybridSOC setup complete."
