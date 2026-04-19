#!/bin/bash
# HybridSOC Kubernetes Deploy Script
# Usage: ./scripts/deploy.sh [dev|prod]

set -euo pipefail

ENV=${1:-prod}

echo "╔══════════════════════════════════════════════════════╗"
echo "║   HybridSOC Kubernetes Deployment v2.0.0            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl not found"; exit 1; }

echo "Deploying to environment: $ENV"
echo ""

kubectl apply -k k8s/overlays/$ENV

echo ""
echo "Waiting for rollout..."
kubectl rollout status deployment/ai-engine  -n hybridsoc --timeout=120s
kubectl rollout status deployment/grc-engine -n hybridsoc --timeout=120s
kubectl rollout status deployment/api-gateway -n hybridsoc --timeout=120s

echo ""
echo "✅ HybridSOC deployed to Kubernetes ($ENV)"
echo ""
kubectl get pods -n hybridsoc
