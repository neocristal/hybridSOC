$root = "hybridsoc"

# Create folders
New-Item -ItemType Directory -Path $root -Force
New-Item -ItemType Directory -Path "$root\docker\wazuh" -Force
New-Item -ItemType Directory -Path "$root\k8s" -Force
New-Item -ItemType Directory -Path "$root\services\ai-engine" -Force
New-Item -ItemType Directory -Path "$root\services\grc-engine" -Force
New-Item -ItemType Directory -Path "$root\services\api-gateway" -Force
New-Item -ItemType Directory -Path "$root\scripts" -Force
New-Item -ItemType Directory -Path "$root\docs" -Force

# Create main files
@(
"README.md",
"SECURITY.md",
"ARCHITECTURE.md",
"AI.md",
"INTEGRITY.md",
"API.md"
) | ForEach-Object {
    New-Item -Path "$root\$_" -ItemType File -Force
}

# Docker compose
@"
version: "3.9"
services:
  wazuh-manager:
    image: wazuh/wazuh-manager:latest
    ports:
      - "1514:1514"
"@ | Set-Content "$root\docker\docker-compose.yml"

# K8s namespace
@"
apiVersion: v1
kind: Namespace
metadata:
  name: hybridsoc
"@ | Set-Content "$root\k8s\namespace.yaml"

# Script setup.sh
@"
#!/bin/bash
docker compose up -d
"@ | Set-Content "$root\scripts\setup.sh"

# Script deploy.sh
@"
#!/bin/bash
kubectl apply -f k8s/
"@ | Set-Content "$root\scripts\deploy.sh"

Write-Host "✅ HybridSOC project created"

$root = "hybridsoc"

mkdir $root -Force
mkdir "$root\k8s\base" -Force
mkdir "$root\k8s\overlays\prod" -Force
mkdir "$root\services\ai-engine" -Force
mkdir "$root\services\grc-engine" -Force
mkdir "$root\services\api-gateway" -Force

# AI service
@"
from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/risk")
def risk():
    return {"risk_score": random.randint(1,100)}
"@ | Set-Content "$root\services\ai-engine\app.py"

# Dockerfile (secure)
@"
FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn
USER appuser
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
"@ | Set-Content "$root\services\ai-engine\Dockerfile"

# K8s deployment with security
@"
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
"@ | Set-Content "$root\k8s\base\ai.yaml"

# Network policy (zero trust)
@"
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
"@ | Set-Content "$root\k8s\base\networkpolicy.yaml"

Write-Host "✅ Enterprise HybridSOC created"