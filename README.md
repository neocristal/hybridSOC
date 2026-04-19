# HybridSOC Enterprise

AI-Driven HybridSOC with GRC integration.

## Stack

- SIEM: Wazuh
- SOAR: TheHive + Cortex
- AI Engine: FastAPI + ML
- GRC Engine
- API Gateway
- GitOps: ArgoCD
- Orchestration: Kubernetes

## Deploy

kubectl apply -k k8s/overlays/prod

## Architecture

Users → IAM → Zero Trust → SIEM → AI → SOAR → GRC
