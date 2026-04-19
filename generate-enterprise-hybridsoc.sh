#!/bin/bash

PROJECT="hybridsoc-enterprise"

echo "Creating enterprise repo..."

mkdir -p $PROJECT/{helm,argo,ci,docker,services/{ai,grc,api},k8s/{base,overlays/dev,overlays/prod},scripts,docs,.github/workflows}

cd $PROJECT

################################
# README
################################
cat <<EOF > README.md
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
EOF

################################
# DOCKER BEST PRACTICE (NON ROOT)
################################
cat <<EOF > services/ai/Dockerfile
FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn scikit-learn
USER appuser
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
EOF

################################
# AI SERVICE
################################
cat <<EOF > services/ai/app.py
from fastapi import FastAPI
import numpy as np

app = FastAPI()

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/risk")
def risk():
    return {"risk_score": int(np.random.randint(1,100))}
EOF

################################
# GRC SERVICE
################################
cat <<EOF > services/grc/app.py
from fastapi import FastAPI

app = FastAPI()

@app.post("/compliance")
def compliance():
    return {"framework":"ISO27001","status":"mapped"}
EOF

################################
# API GATEWAY
################################
cat <<EOF > services/api/app.py
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/health")
def health():
    return {"api":"ok"}
EOF

################################
# K8S BASE DEPLOYMENT
################################
cat <<EOF > k8s/base/ai.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai
  template:
    metadata:
      labels:
        app: ai
    spec:
      containers:
      - name: ai
        image: hybridsoc/ai:latest
        securityContext:
          runAsNonRoot: true
          allowPrivilegeEscalation: false
        ports:
        - containerPort: 8000
EOF

################################
# NETWORK POLICY
################################
cat <<EOF > k8s/base/networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF

################################
# RBAC
################################
cat <<EOF > k8s/base/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ai-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get","list"]
EOF

################################
# KUSTOMIZE
################################
cat <<EOF > k8s/overlays/prod/kustomization.yaml
resources:
- ../../base
EOF

################################
# HELM CHART
################################
mkdir -p helm/hybridsoc/templates

cat <<EOF > helm/hybridsoc/Chart.yaml
apiVersion: v2
name: hybridsoc
version: 1.0.0
EOF

################################
# ARGOCD
################################
cat <<EOF > argo/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: hybridsoc
spec:
  source:
    repoURL: https://github.com/yourrepo/hybridsoc
    path: k8s/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: hybridsoc
EOF

################################
# CI/CD
################################
cat <<EOF > .github/workflows/ci.yml
name: CI

on:
  push:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker
        run: docker build -t hybridsoc/ai ./services/ai
EOF

################################
# DOCKER COMPOSE (DEV)
################################
cat <<EOF > docker/docker-compose.yml
version: "3.9"
services:
  ai:
    build: ../services/ai
    ports:
      - "8000:8000"
EOF

################################
# SCRIPTS
################################
cat <<EOF > scripts/deploy.sh
kubectl apply -k k8s/overlays/prod
EOF

chmod +x scripts/deploy.sh

################################
# ZIP
################################
cd ..
zip -r hybridsoc-enterprise.zip hybridsoc-enterprise

echo "✅ ENTERPRISE REPO READY: hybridsoc-enterprise.zip"