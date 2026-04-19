# API Reference

> HybridSOC REST API v2.0.0  
> Base URL: `http://localhost:8080/api`  
> Auth: Bearer token (`X-Auth-Token` header)  
> Format: JSON | OpenAPI 3.0 spec at `/api/docs`

---

## Authentication

All endpoints require a valid session token:

```http
X-Auth-Token: <token>
```

Tokens are obtained via `/api/auth/login`. Tokens expire after 8 hours. All unauthenticated requests return `401 Unauthorized` and are logged to the immutable audit trail.

---

## Endpoints

### Health & Status

#### `GET /health`

Returns platform and service health.

```http
GET /health

Response 200:
{
  "status": "ok",
  "version": "2.0.0",
  "services": {
    "wazuh": "connected",
    "elasticsearch": "connected",
    "kafka": "connected",
    "ai_engine": "loaded",
    "llm": "loaded",
    "thehive": "connected"
  },
  "timestamp": "2026-04-19T08:00:00Z"
}
```

#### `GET /api/status`

Returns system status including LLM model state and active language settings.

---

### Authentication

#### `POST /api/auth/register`

Register a new user.

```json
{
  "email": "analyst@company.eu",
  "username": "analyst01",
  "password": "SecureP@ss1!",
  "company_id": 1
}
```

#### `POST /api/auth/login`

Authenticate and obtain session token.

```json
Request:
{
  "email": "analyst@company.eu",
  "password": "SecureP@ss1!",
  "totp_code": "123456"
}

Response 200:
{
  "token": "eyJh...",
  "expires_at": "2026-04-19T16:00:00Z",
  "user": {
    "id": 42,
    "username": "analyst01",
    "role": "analyst"
  }
}
```

---

### AI Risk Engine

#### `POST /risk`

Submit an event for AI risk scoring.

```json
Request:
{
  "user": "analyst01",
  "activity": "bulk_file_download",
  "ip": "192.168.10.45",
  "bytes_transferred": 524288000,
  "timestamp": "2026-04-19T02:15:00Z"
}

Response 200:
{
  "risk_score": 87,
  "anomaly_detected": true,
  "severity": "High",
  "features_triggered": ["volume_spike", "off_hours_activity", "unusual_source"],
  "regulation": ["GDPR Art.5(1)(f)", "ISO 27001 A.8.2", "NIS2 Art.21(2)(h)"],
  "explanation": "Bulk file transfer of 500MB at 02:15 local time is 4.2σ above user baseline. Source IP has not been seen previously.",
  "action_recommended": "create_case",
  "human_review_required": true,
  "model_version": "isolation-forest-v2.1.0"
}
```

#### `POST /anomaly`

Lightweight anomaly check (returns score only).

```json
Response: { "risk_score": 42 }
```

---

### Document Compliance Analysis

#### `POST /api/documents/upload`

Upload a document for asynchronous compliance analysis.

```http
Content-Type: multipart/form-data

file: <PDF|DOCX|TXT>
frameworks: ["ISO27001","DORA","NIS2","GDPR","EUAI"]
```

```json
Response 202:
{
  "document_id": 101,
  "status": "queued",
  "estimated_completion_seconds": 45
}
```

#### `GET /api/documents`

List all documents with scores.

#### `GET /api/documents/{id}`

Full analysis result including all issues.

```json
Response 200:
{
  "document_id": 101,
  "filename": "DORA_selfassessment_2026.docx",
  "overall_score": 62.4,
  "maturity_level": 3,
  "framework_scores": {
    "ISO27001": 71.0,
    "DORA": 54.2,
    "NIS2": 68.5,
    "GDPR": 65.0,
    "EUAI": 55.8
  },
  "issues": [
    {
      "framework": "DORA",
      "article": "Art. 17",
      "severity": "Critical",
      "title": "ICT incident classification procedure missing",
      "description": "No documented procedure for classifying ICT-related incidents per DORA Art.17 thresholds."
    }
  ],
  "llm_summary": "The document demonstrates partial DORA compliance. Critical gaps exist in incident response (Art.17) and third-party risk management (Art.28)..."
}
```

#### `GET /api/documents/{id}/diff/{v1}/{v2}`

Side-by-side diff between two document versions.

---

### Risk Register

#### `GET /api/risks`

List all risk register entries.

#### `POST /api/risks`

Create a new risk entry.

```json
{
  "title": "Single cloud provider dependency",
  "likelihood": 3,
  "impact": 5,
  "framework": "DORA",
  "article": "Art.28",
  "treatment": "Implement multi-cloud redundancy within Q3 2026"
}
```

---

### Crisis Management

#### `GET /api/cm/incidents`

List all incidents.

#### `POST /api/cm/incidents`

Create a new incident (starts DORA Art.17 / NIS2 Art.21 notification timers).

```json
{
  "title": "Ransomware detected on endpoint WKSTN-044",
  "severity": "Critical",
  "type": "ICT_INCIDENT",
  "frameworks": ["DORA", "NIS2"],
  "affected_systems": ["WKSTN-044", "file-server-01"]
}

Response 201:
{
  "incident_id": 55,
  "dora_notification_deadline": "2026-04-21T08:00:00Z",
  "nis2_notification_deadline": "2026-04-20T08:00:00Z",
  "status": "open"
}
```

---

### Third-Party Risk Management (TPRM)

#### `GET /api/tprm/vendors`

List vendor registry.

#### `POST /api/tprm/vendors`

Register a new vendor.

```json
{
  "name": "CloudProvider EU GmbH",
  "criticality": "Critical",
  "dora_art28_applicable": true,
  "services": ["cloud_storage", "compute"]
}
```

---

### GRC Knowledge Base & Chat

#### `POST /api/kb/upload`

Upload regulatory text to knowledge base (indexed via FAISS).

#### `POST /api/chat`

Ask a compliance question grounded in the knowledge base.

```json
Request:  { "question": "What are DORA Art.17 notification deadlines?" }
Response: { "answer": "DORA Art.17 requires initial notification of major ICT incidents to the competent authority within 4 hours of classification, with a detailed report within 72 hours...", "sources": ["DORA_Art17.pdf"] }
```

---

### Administration

#### `GET /api/admin/companies`

List all companies (superadmin only).

#### `GET /api/admin/users`

List all users (admin only).

#### `GET /api/audit`

Full immutable audit log (admin only).

```json
[
  {
    "id": 1001,
    "user_id": 42,
    "action": "document_upload",
    "details": "filename: DORA_assessment.docx, size: 204800",
    "ip_address": "195.44.x.x",
    "timestamp": "2026-04-19T08:15:00Z",
    "prev_hash": "a3f8...",
    "row_hash": "b7c2..."
  }
]
```

---

## Error Codes

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 202 | Accepted (async processing) |
| 400 | Bad Request — validation error |
| 401 | Unauthorized — invalid or expired token |
| 403 | Forbidden — insufficient role |
| 404 | Not Found |
| 429 | Too Many Requests — rate limit exceeded |
| 500 | Internal Server Error |

---

## Rate Limits

| Role | Requests / minute |
|---|---|
| `analyst` | 60 |
| `manager` | 120 |
| `admin` | 300 |
| `superadmin` | Unlimited |

All rate limit violations are logged to the audit trail and trigger an automated alert if frequency exceeds 3 violations in 5 minutes.

---

## OpenAPI / Swagger

Full OpenAPI 3.0 specification available at runtime:

```
http://localhost:8000/docs    ← AI Engine (Swagger UI)
http://localhost:8001/docs    ← GRC Engine (Swagger UI)
http://localhost:8080/api/redoc ← API Gateway (ReDoc)
```
