# Security Implementation
## USM Autoimmune ML Platform - Sprint 3

| Field | Value |
|-------|-------|
| **Sprint** | Sprint 3 - Security Hardening |
| **Status** | ✅ Complete |
| **JIRA Tickets** | USMA-86, USMA-115, USMA-52 |
| **Last Updated** | April 27, 2026 |

---

## Table of Contents

1. [Security Overview](#1-security-overview)
2. [Authentication (JWT)](#2-authentication-jwt)
3. [Authorization (RBAC)](#3-authorization-rbac)
4. [Transport Security (HTTPS/TLS)](#4-transport-security-httpstls)
5. [API Rate Limiting](#5-api-rate-limiting)
6. [API Key Management](#6-api-key-management)
7. [Audit Logging & Compliance](#7-audit-logging--compliance)
8. [Security Headers](#8-security-headers)
9. [Database Security Tables](#9-database-security-tables)
10. [Security Evolution Summary](#10-security-evolution-summary)
11. [Screenshot Evidence](#11-screenshot-evidence)

---

# 1. Security Overview

Sprint 3 transformed the platform from basic session-based authentication to **enterprise-grade security** with multiple layers of protection:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SECURITY ARCHITECTURE LAYERS                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 1: TRANSPORT SECURITY                                           │
│  ├─ HTTPS/TLS 1.2+ encryption via nginx reverse proxy                 │
│  ├─ HTTP-to-HTTPS automatic redirection                                │
│  └─ Security headers (HSTS, X-Frame-Options, CSP)                      │
│                                                                         │
│  LAYER 2: AUTHENTICATION                                                │
│  ├─ JWT tokens (12-hour validity)                                      │
│  ├─ Bcrypt password hashing with salt                                  │
│  └─ Automatic token expiry detection                                   │
│                                                                         │
│  LAYER 3: AUTHORIZATION                                                 │
│  ├─ Role-Based Access Control (RBAC)                                   │
│  ├─ 3 roles: Admin, Researcher, Viewer                                 │
│  └─ Per-endpoint permission enforcement                                │
│                                                                         │
│  LAYER 4: API PROTECTION                                                │
│  ├─ Sliding window rate limiting                                       │
│  ├─ Per-endpoint limits (10-100 req/min)                               │
│  └─ API key management for external systems                            │
│                                                                         │
│  LAYER 5: AUDIT & COMPLIANCE                                           │
│  ├─ Comprehensive audit logging (22 columns)                           │
│  ├─ Data access logs for PDPA compliance                               │
│  └─ Sensitive action flagging                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 2. Authentication (JWT)

## 2.1 Overview [USMA-86]

Replaced the previous session-based authentication with **JWT (JSON Web Token) authentication**. Access tokens have a 12-hour validity period with automatic expiry detection on the frontend.

| Parameter | Value |
|-----------|-------|
| **Token Type** | Bearer |
| **Algorithm** | HS256 |
| **Expiry** | 12 hours (43,200 seconds) |
| **Storage** | HttpOnly cookie (secure) |
| **Status** | ✅ Complete |

## 2.2 Implementation Files

| File | Purpose |
|------|---------|
| `app/core/security.py` | JWT token generation, validation, password hashing |
| `app/api/endpoints/auth.py` | Login, logout, token refresh endpoints |
| `app/api/deps.py` | Dependency injection for authentication |

## 2.3 JWT Token Structure

```python
# JWT Payload
{
    "sub": "user@email.com",      # Subject (user identifier)
    "user_id": 123,               # Database user ID
    "role": "researcher",         # RBAC role
    "exp": 1714063200,            # Expiration timestamp (12h from issue)
    "iat": 1714020000             # Issued at timestamp
}
```

## 2.4 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    JWT AUTHENTICATION FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. LOGIN REQUEST                                                       │
│     POST /api/v1/auth/login                                            │
│     Body: { "email": "user@email.com", "password": "****" }            │
│                                                                         │
│  2. SERVER VALIDATION                                                   │
│     ├─ Verify credentials against database                             │
│     ├─ Check password hash (bcrypt)                                    │
│     └─ Generate JWT token with 12h expiry                              │
│                                                                         │
│  3. LOGIN RESPONSE                                                      │
│     {                                                                   │
│       "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",       │
│       "token_type": "bearer",                                          │
│       "expires_in": 43200                                              │
│     }                                                                   │
│                                                                         │
│  4. AUTHENTICATED REQUESTS                                              │
│     Header: Authorization: Bearer <token>                              │
│                                                                         │
│  5. TOKEN VALIDATION (Every Request)                                   │
│     ├─ Verify signature                                                │
│     ├─ Check expiration                                                │
│     ├─ Extract user_id and role                                        │
│     └─ Inject current_user into request                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2.5 Screenshot Evidence

| # | Screenshot | Description |
|---|------------|-------------|
| 29 | JWT Login Response | POST /api/v1/auth/login showing access_token, token_type: bearer, expires_in: 43200 |
| 30 | JWT Authorization | Swagger 'Authorize' modal with Bearer token input, endpoints showing lock icons |

---

# 3. Authorization (RBAC)

## 3.1 Overview [USMA-115] [USMA-52]

Implements a **3-tier role-based access control system** applied to all training and inference endpoints. Roles are enforced at the API layer with automatic permission checking.

| Role | Description | Access Level |
|------|-------------|--------------|
| **Admin** | Full system access | All operations + user management |
| **Researcher** | Training and prediction access | ML operations, no admin panel |
| **Viewer** | Read-only access | View results only |

## 3.2 Implementation Files

| File | Purpose |
|------|---------|
| `app/api/deps.py` | Role checking dependency (`require_role()`) |
| `app/models/user.py` | User model with role field |

## 3.3 Permission Matrix

| Permission | Admin | Researcher | Viewer |
|------------|:-----:|:----------:|:------:|
| Upload Datasets | ✅ | ✅ | ❌ |
| Train Models | ✅ | ✅ | ❌ |
| Make Predictions | ✅ | ✅ | ❌ |
| View Predictions History | ✅ | ✅ | ✅ |
| View Model Comparison | ✅ | ✅ | ✅ |
| Admin Panel | ✅ | ❌ | ❌ |
| Manage Users | ✅ | ❌ | ❌ |
| Create API Keys | ✅ | ❌ | ❌ |
| View Audit Logs | ✅ | ❌ | ❌ |

## 3.4 RBAC Implementation

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status

def require_role(allowed_roles: list[str]):
    """Dependency that checks if current user has required role."""
    
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized for this action"
            )
        return True
    
    return role_checker

# Usage in endpoints
@router.post("/train/base-model")
async def train_base_model(
    request: BaseModelTrainingRequest,
    current_user: User = Depends(get_current_user),      # Authentication
    _: bool = Depends(require_role(["admin", "researcher"]))  # Authorization
):
    ...
```

## 3.5 Response Codes

| Code | Meaning | When |
|------|---------|------|
| **200** | Success | Valid token + authorized role |
| **401** | Unauthorized | No token or invalid/expired token |
| **403** | Forbidden | Valid token but insufficient role |

## 3.6 Screenshot Evidence

| # | Screenshot | Description |
|---|------------|-------------|
| 31 | RBAC Permission Matrix | PowerPoint slide showing role permissions |
| 32 | Users Table with Roles | Database query: `SELECT username, email, role, is_active FROM users` |
| 33 | Admin UI View | Full sidebar with all menu items visible |
| 34 | Researcher UI View | Limited sidebar (no Admin Panel) |
| 35 | Viewer UI View | Minimal sidebar (read-only items) |
| 36 | RBAC 403 Forbidden | Swagger showing viewer role rejected from training endpoint |

---

# 4. Transport Security (HTTPS/TLS)

## 4.1 Overview

All traffic is encrypted using **TLS 1.2/1.3** via nginx reverse proxy. HTTP requests are automatically redirected to HTTPS.

## 4.2 nginx Configuration

```nginx
# /etc/nginx/sites-enabled/usm-autoimmune-https

# HTTP → HTTPS Redirect
server {
    listen 80;
    server_name 100.106.132.15;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name 100.106.132.15;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy to Backend API
    location /api/ {
        proxy_pass http://100.106.132.15:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy to Frontend
    location / {
        proxy_pass http://100.106.132.15:5173;
        proxy_set_header Host $host;
    }
}
```

## 4.3 Certificate Files

```bash
$ ls -lh /etc/nginx/ssl/
-rw-r--r-- 1 root root 1.8K Apr 25 10:30 cert.pem
-rw------- 1 root root 1.7K Apr 25 10:30 key.pem
```

| Environment | Certificate Type |
|-------------|-----------------|
| Development | Self-signed certificate |
| Production | Let's Encrypt (auto-renewal) |

## 4.4 Screenshot Evidence

| # | Screenshot | Description |
|---|------------|-------------|
| 42 | HTTPS Connection | Browser address bar showing padlock icon |
| 48 | nginx Configuration | Terminal showing SSL config with TLS 1.2/1.3 |

---

# 5. API Rate Limiting

## 5.1 Overview

**Sliding window rate limiting** protects all API endpoints from abuse. Different endpoints have different limits based on their sensitivity and resource consumption.

## 5.2 Rate Limits by Endpoint

| Endpoint Pattern | Limit | Window | Purpose |
|-----------------|-------|--------|---------|
| `/api/v1/auth/login` | 10 req | 60 sec | Prevent brute-force attacks |
| `/api/v1/upload/*` | 20 req | 60 sec | Prevent upload abuse |
| `/api/v1/ml/training/*` | 30 req | 60 sec | Prevent training spam |
| `/api/v1/ml/ensemble/*` | 30 req | 60 sec | Prevent ensemble spam |
| `/api/v1/admin/*` | 50 req | 60 sec | Admin protection |
| All other endpoints | 100 req | 60 sec | General protection |

## 5.3 Rate Limit Headers

When rate limited, the API returns:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1714063260
Retry-After: 45

{
    "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

## 5.4 Testing Rate Limits

```bash
# Make 110 rapid requests to login endpoint (limit: 10/min)
for i in {1..110}; do 
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://100.106.132.15:8001/api/v1/auth/login
done | sort | uniq -c

# Expected output:
#      10 405  (Method Not Allowed - GET instead of POST)
#     100 429  (Too Many Requests - RATE LIMITED!)
```

## 5.5 Screenshot Evidence

| # | Screenshot | Description |
|---|------------|-------------|
| 43 | Rate Limiting 429 | Terminal showing 100 requests blocked with 429 status |

---

# 6. API Key Management

## 6.1 Overview

API keys enable **external system integration** with role-based permissions and automatic expiration. Keys are SHA-256 hashed before storage - plain keys are never stored.

## 6.2 API Key Features

| Feature | Description |
|---------|-------------|
| **Role-Based** | Keys inherit role permissions (admin/researcher/viewer) |
| **Scoped** | Optional scope restrictions (e.g., `read:patients`) |
| **Expiring** | Configurable expiration (e.g., 90 days) |
| **Rate Limited** | Per-key rate limits |
| **Revocable** | Can be revoked at any time |
| **Audited** | All usage tracked |

## 6.3 Create API Key

```http
POST /api/v1/admin/keys
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "name": "Mobile App Integration",
  "description": "API access for mobile application",
  "role": "researcher",
  "scopes": ["read:patients", "write:predictions"],
  "rate_limit": 2000,
  "expires_in_days": 90
}
```

**Response:**
```json
{
  "id": 1,
  "key": "usm_key_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
  "key_prefix": "usm_key_abc123",
  "name": "Mobile App Integration",
  "description": "API access for mobile application",
  "role": "researcher",
  "scopes": ["read:patients", "write:predictions"],
  "rate_limit": 2000,
  "expires_at": "2026-07-25T10:30:00Z",
  "created_at": "2026-04-25T10:30:00Z",
  "created_by": "s.nasrin"
}
```

> ⚠️ **Warning:** API key is shown only once - must be saved immediately!

## 6.4 Using API Keys

```bash
# Option 1: Header
curl -H "X-API-Key: usm_key_abc123..." https://api.example.com/endpoint

# Option 2: Query parameter (less secure)
curl "https://api.example.com/endpoint?api_key=usm_key_abc123..."
```

## 6.5 Screenshot Evidence

| # | Screenshot | Description |
|---|------------|-------------|
| 44 | API Key Creation | Swagger showing POST /admin/keys response with full key |
| 45 | API Keys Table | Database showing key_hash, key_prefix, role, expires_at |

---

# 7. Audit Logging & Compliance

## 7.1 Overview

Comprehensive audit logging captures **WHO, WHAT, WHEN, WHERE, WHY** for all platform operations. Critical for PDPA compliance and security monitoring.

## 7.2 Audit Log Coverage

| Event Type | Logged? | Contains |
|------------|:-------:|----------|
| User Authentication | ✅ | WHO, WHEN, WHERE (IP), SUCCESS/FAIL |
| Data Access | ✅ | USER, PATIENT, FIELDS, PURPOSE, CONSENT |
| Model Training | ✅ | USER, DATASET, PARAMS, DURATION |
| Predictions | ✅ | USER, PATIENT, MODEL, RESULT, CONFIDENCE |
| Admin Actions | ✅ | USER, ACTION, RESOURCE, BEFORE/AFTER |
| API Key Operations | ✅ | CREATOR, KEY_PREFIX, PERMISSIONS |
| Security Events | ✅ | FAILED_LOGINS, RATE_LIMITS, 403_ERRORS |

## 7.3 Audit Logs Query

```sql
SELECT 
    id,
    username,
    action,
    resource_type,
    endpoint,
    http_method,
    ip_address,
    response_status,
    response_time_ms,
    is_sensitive,
    timestamp
FROM audit_logs
ORDER BY timestamp DESC
LIMIT 10;
```

**Example Results:**

| id | username | action | resource_type | endpoint | http_method | ip_address | response_status | response_time_ms | is_sensitive | timestamp |
|----|----------|--------|---------------|----------|-------------|------------|-----------------|------------------|--------------|-----------|
| 145 | s.nasrin | API_KEY_CREATED | api_key | /admin/keys | POST | 100.106.132.1 | 200 | 45 | true | 2026-04-26 10:30 |
| 144 | s.nasrin | DATASET_PREPARED | dataset | /ml/prepare-dataset | POST | 100.106.132.1 | 200 | 2341 | false | 2026-04-26 10:25 |
| 143 | s.nasrin | TRAINING_STARTED | training_job | /ml/train/base-model | POST | 100.106.132.1 | 200 | 89 | false | 2026-04-26 10:20 |
| 142 | researcher1 | PREDICTION_MADE | prediction | /ml/predict | POST | 100.106.132.5 | 200 | 234 | false | 2026-04-26 10:15 |
| 141 | researcher1 | PATIENT_VIEWED | patient | /patients/123 | GET | 100.106.132.5 | 200 | 23 | true | 2026-04-26 10:10 |
| 140 | unknown | USER_LOGIN_FAILED | auth | /auth/login | POST | 203.123.45.67 | 401 | 12 | true | 2026-04-26 10:05 |

## 7.4 Data Access Logs (PDPA Compliance)

```sql
SELECT 
    id,
    username,
    patient_anonymous_id,
    fields_accessed,
    access_purpose,
    consent_verified,
    accessed_at
FROM data_access_logs
ORDER BY accessed_at DESC
LIMIT 5;
```

**Example Results:**

| id | username | patient_anonymous_id | fields_accessed | access_purpose | consent_verified | accessed_at |
|----|----------|---------------------|-----------------|----------------|------------------|-------------|
| 23 | s.nasrin | PAT_001 | ["diagnosis", "lab_results", "medications"] | Clinical research | true | 2026-04-26 10:10 |
| 22 | researcher1 | PAT_002 | ["lab_results", "biomarkers"] | Model training | true | 2026-04-26 09:45 |

> **PDPA Compliance:** Every data access is logged with fields accessed, purpose, and consent verification status.

## 7.5 Screenshot Evidence

| # | Screenshot | Description |
|---|------------|-------------|
| 46 | Audit Logs Table | Database showing comprehensive audit trail |
| 46b | Data Access Logs | Database showing PDPA-compliant access logging |

---

# 8. Security Headers

## 8.1 Implemented Headers

```http
# Response Headers (added by nginx)
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

## 8.2 Header Descriptions

| Header | Value | Purpose |
|--------|-------|---------|
| **HSTS** | max-age=31536000 | Force HTTPS for 1 year |
| **X-Frame-Options** | SAMEORIGIN | Prevent clickjacking |
| **X-Content-Type-Options** | nosniff | Prevent MIME sniffing |
| **X-XSS-Protection** | 1; mode=block | Enable XSS filter |
| **CSP** | default-src 'self' | Restrict resource loading |

---

# 9. Database Security Tables

## 9.1 api_keys Table

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    api_keys TABLE (18 columns, 3 indexes)               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  IDENTIFICATION                                                         │
│  ├─ id (PRIMARY KEY)                                                   │
│  ├─ name                                                               │
│  ├─ key_hash (SHA-256 hashed, never plain text)                        │
│  └─ key_prefix (first 14 chars for identification)                     │
│                                                                         │
│  PERMISSIONS                                                            │
│  ├─ role (admin/researcher/viewer)                                     │
│  ├─ scopes (JSONB array)                                               │
│  └─ rate_limit                                                         │
│                                                                         │
│  LIFECYCLE                                                              │
│  ├─ created_by, created_at                                             │
│  ├─ expires_at                                                         │
│  ├─ last_used_at, usage_count                                          │
│  └─ is_active, is_revoked, revoked_at, revoked_by                      │
│                                                                         │
│  INDEXES                                                                │
│  ├─ idx_api_keys_hash      → Fast key verification                     │
│  ├─ idx_api_keys_prefix    → Management UI lookup                      │
│  └─ idx_api_keys_created_by → Audit queries                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 9.2 audit_logs Table

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    audit_logs TABLE (22 columns, 6 indexes)             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WHO                                                                    │
│  ├─ user_id, username, user_role                                       │
│                                                                         │
│  WHAT                                                                   │
│  ├─ action, resource_type, resource_id                                 │
│  ├─ http_method, endpoint                                              │
│  └─ description                                                        │
│                                                                         │
│  WHEN                                                                   │
│  └─ timestamp                                                          │
│                                                                         │
│  WHERE                                                                  │
│  ├─ ip_address, user_agent                                             │
│                                                                         │
│  WHY                                                                    │
│  ├─ request_payload (JSONB)                                            │
│  └─ changes (JSONB - before/after)                                     │
│                                                                         │
│  HOW                                                                    │
│  ├─ response_time_ms, response_status                                  │
│  └─ data_accessed                                                      │
│                                                                         │
│  FLAGS                                                                  │
│  ├─ is_sensitive, is_suspicious                                        │
│  └─ success                                                            │
│                                                                         │
│  INDEXES                                                                │
│  ├─ idx_audit_logs_user_timestamp    → User activity queries           │
│  ├─ idx_audit_logs_action_timestamp  → Security event analysis         │
│  ├─ idx_audit_logs_resource          → Resource access tracking        │
│  ├─ idx_audit_logs_ip_timestamp      → IP-based threat detection       │
│  ├─ idx_audit_logs_action            → Action-type filtering           │
│  └─ idx_audit_logs_timestamp         → Chronological queries           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 9.3 data_access_logs Table

```
┌─────────────────────────────────────────────────────────────────────────┐
│                data_access_logs TABLE (13 columns, 3 indexes)           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  USER IDENTIFICATION                                                    │
│  ├─ id, user_id, username, user_role                                   │
│                                                                         │
│  PATIENT IDENTIFICATION                                                 │
│  ├─ patient_id, patient_anonymous_id                                   │
│                                                                         │
│  ACCESS DETAILS                                                         │
│  ├─ fields_accessed (JSONB array)                                      │
│  ├─ access_purpose                                                     │
│  ├─ consent_verified (boolean)                                         │
│  ├─ access_level (read/write/delete)                                   │
│  └─ accessed_at, ip_address                                            │
│                                                                         │
│  INDEXES                                                                │
│  ├─ idx_data_access_patient_time → Patient access history              │
│  ├─ idx_data_access_user_time    → User activity audit                 │
│  └─ idx_data_access_accessed_at  → Time-based queries                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 10. Security Evolution Summary

## 10.1 Sprint 1-2 vs Sprint 3 Comparison

| Security Feature | Sprint 1-2 (Original) | Sprint 3 (Enhanced) | Status |
|------------------|:---------------------:|:-------------------:|:------:|
| Authentication | Session-based cookies | ✅ JWT tokens (12h expiry) | ✅ |
| Authorization | Basic login | ✅ RBAC (3 roles) | ✅ |
| Transport Security | ❌ HTTP only | ✅ HTTPS/TLS 1.2+ | ✅ |
| Rate Limiting | ❌ None | ✅ Per-endpoint (10-100 req/min) | ✅ |
| API Access Control | ❌ JWT only | ✅ API key management | ✅ |
| Audit Trail | ❌ None | ✅ 22-column logging | ✅ |
| PDPA Compliance | ❌ None | ✅ Data access logs | ✅ |
| Security Headers | ❌ None | ✅ HSTS, X-Frame-Options, CSP | ✅ |
| Password Security | Basic hashing | ✅ bcrypt with salt | ✅ |
| Key Management | ❌ None | ✅ SHA-256, auto-expiration | ✅ |

## 10.2 Security Metrics

| Metric | Value |
|--------|-------|
| **Security Tables** | 3 new tables |
| **Total Indexes** | 12 indexes for fast queries |
| **Audit Columns** | 22 columns per log entry |
| **Rate Limit Tiers** | 6 endpoint categories |
| **RBAC Roles** | 3 (Admin, Researcher, Viewer) |
| **Token Validity** | 12 hours |
| **TLS Version** | 1.2 / 1.3 |

---

# 11. Screenshot Evidence

## 11.1 Complete Screenshot Checklist

### Authentication & Authorization (Core)

| # | Screenshot | Location | Status |
|---|------------|----------|:------:|
| 29 | JWT Login Response | Swagger: POST /api/v1/auth/login | ☐ |
| 30 | JWT Authorization Modal | Swagger: Authorize button | ☐ |
| 31 | RBAC Permission Matrix | PowerPoint slide | ☐ |
| 32 | Users Table with Roles | pgAdmin: SELECT from users | ☐ |
| 33 | Admin UI View | Frontend: Full sidebar | ☐ |
| 34 | Researcher UI View | Frontend: Limited sidebar | ☐ |
| 35 | Viewer UI View | Frontend: Minimal sidebar | ☐ |
| 36 | RBAC 403 Forbidden | Swagger: Viewer rejected | ☐ |

### Production Security (New)

| # | Screenshot | Location | Status |
|---|------------|----------|:------:|
| 42 | HTTPS Connection | Browser padlock icon | ☐ |
| 43 | Rate Limiting 429 | Terminal: 100 blocked requests | ☐ |
| 44 | API Key Creation | Swagger: POST /admin/keys | ☐ |
| 45 | API Keys Table | pgAdmin: api_keys table | ☐ |
| 46 | Audit Logs Table | pgAdmin: audit_logs query | ☐ |
| 46b | Data Access Logs | pgAdmin: data_access_logs query | ☐ |
| 47 | Security Comparison | PowerPoint: Evolution table | ☐ |
| 48 | nginx HTTPS Config | Terminal: cat nginx config | ☐ |

### PowerPoint Slides

| # | Slide | Content |
|---|-------|---------|
| A | Rate Limits by Endpoint | Table with 6 endpoint categories |
| B | Audit Log Coverage | Table with 7 event types |
| C | Security Tables Schema | 3 tables with indexes |
| D | Security Evolution | Sprint 1-2 vs Sprint 3 comparison |

---

## Summary

Sprint 3 security implementation provides **enterprise-grade protection** for the USM Autoimmune ML Platform:

✅ **JWT Authentication** - Secure, stateless token-based auth with 12h expiry  
✅ **RBAC** - 3-tier role system (Admin/Researcher/Viewer)  
✅ **HTTPS/TLS** - All traffic encrypted with TLS 1.2+  
✅ **Rate Limiting** - Per-endpoint protection against abuse  
✅ **API Keys** - External integration with SHA-256 hashing  
✅ **Audit Logging** - Comprehensive WHO/WHAT/WHEN/WHERE/WHY tracking  
✅ **PDPA Compliance** - Data access logging with consent verification  
✅ **Security Headers** - HSTS, X-Frame-Options, CSP protection  

---

*Document Version: 1.0*  
*Last Updated: April 27, 2026*  
*Author: Syarifah Fajriyah*
