# TSD Security Features - Screenshot Guide
## Production Readiness & Security Compliance
**Created:** April 26, 2026  
**Sprint 3 - Advanced Security Implementation**

---

## 🎯 Overview

This guide covers screenshots for **4 NEW production security features** implemented beyond the original Sprint 3 scope:

| Feature | JIRA ID | Status | Priority |
|---------|---------|--------|----------|
| HTTPS/TLS Encryption | USMA-130 | ✅ Deployed | 🔴 Critical |
| API Rate Limiting | USMA-131 | ✅ Deployed | 🔴 Critical |
| API Key Management | NEW | ✅ Deployed | 🟡 High |
| Audit Logging & Compliance | NEW | ✅ Deployed | 🟡 High |

**Note:** JWT Authentication (USMA-86) and RBAC (USMA-115, USMA-52) are covered in [TSD_SCREENSHOT_GUIDE_FUNCTIONAL.md](TSD_SCREENSHOT_GUIDE_FUNCTIONAL.md#35-security--governance)

---

## 📸 Screenshot List

### Core Security (Already Documented)
- ✅ Screenshot 29: JWT Login Response
- ✅ Screenshot 30: Swagger Authorization
- ✅ Screenshot 31: RBAC Permission Matrix
- ✅ Screenshot 32: Users Table (Roles)
- ✅ Screenshots 33-35: UI RBAC (Admin/Researcher/Viewer)
- ✅ Screenshot 36: RBAC 403 Enforcement

### **NEW - Production Security (This Guide)**
- **Screenshot 42:** HTTPS Connection (Browser Lock Icon)
- **Screenshot 43:** Rate Limiting in Action (429 Errors)
- **Screenshot 44:** API Key Creation (Swagger)
- **Screenshot 45:** API Keys Table (Database)
- **Screenshot 46:** Audit Logs Table (Database)
- **Screenshot 47:** Security Comparison Table (PowerPoint)
- **Screenshot 48:** nginx HTTPS Configuration (Terminal)

---

## 🔐 SECTION 1: HTTPS/TLS Encryption

### 📸 Screenshot 42: HTTPS Secure Connection

**What to capture:** Browser showing HTTPS connection with padlock icon

**Location:** https://100.106.132.15 (or your domain)

**Steps:**
1. Open browser (Chrome/Edge recommended)
2. Navigate to: `https://100.106.132.15`
3. **Screenshot showing:**
   - **Address bar with padlock icon** 🔒
   - URL starting with `https://`
   - Page content: Platform dashboard or login page
   - Click on padlock icon to show certificate details

**What to highlight:**
- **Circle the padlock icon**
- **Box the "https://" in URL**
- Add annotation: "TLS encryption active"

**Alternative view: Certificate Details**
1. Click padlock icon → "Certificate is valid"
2. **Screenshot certificate information:**
   - Issued to: `100.106.132.15`
   - Issued by: (Self-signed or Let's Encrypt)
   - Valid from/to dates
   - Encryption: TLS 1.3 or TLS 1.2

**Caption:**
"Platform secured with HTTPS/TLS encryption. Self-signed certificate for development; production uses Let's Encrypt."

---

### 📸 Screenshot 48: nginx HTTPS Configuration

**What to capture:** Terminal showing nginx configuration

**Location:** SSH to server

**Commands:**
```bash
# Show nginx HTTPS configuration
cat /etc/nginx/sites-enabled/usm-autoimmune-https

# Show certificate files
ls -lh /etc/nginx/ssl/
```

**Expected output to screenshot:**
```nginx
server {
    listen 80;
    server_name 100.106.132.15;
    return 301 https://$server_name$request_uri;  # HTTP → HTTPS redirect
}

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

**Certificate files:**
```
-rw-r--r-- 1 root root 1.8K Apr 25 10:30 cert.pem
-rw------- 1 root root 1.7K Apr 25 10:30 key.pem
```

**What to highlight:**
- **Box the SSL certificate paths**
- **Circle "ssl_protocols TLSv1.2 TLSv1.3"**
- **Highlight security headers (HSTS, X-Frame-Options)**
- **Circle the HTTP → HTTPS redirect (line 4)**

**Caption:**
"nginx reverse proxy configured with TLS 1.2/1.3 encryption, security headers, and automatic HTTP-to-HTTPS redirection."

---

## 🚦 SECTION 2: API Rate Limiting

### 📸 Screenshot 43: Rate Limiting in Action

**What to capture:** Terminal showing rate limiting returning 429 errors

**Location:** SSH to server or local terminal

**Test command:**
```bash
# Make 110 rapid requests to login endpoint (limit: 10/min)
for i in {1..110}; do 
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://100.106.132.15:8001/api/v1/auth/login
done | sort | uniq -c
```

**Expected output to screenshot:**
```
     10 405  (Method Not Allowed - GET instead of POST, expected)
    100 429  (Too Many Requests - RATE LIMITED!)
```

**Alternative test (showing rate limit headers):**
```bash
# Single request showing rate limit headers
curl -i http://100.106.132.15:8001/api/v1/ml/predictions/history

# Expected headers in output:
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1777020000
...
```

**What to highlight:**
- **Circle the "100 429" count** (rate limited responses)
- **Box the X-RateLimit-* headers**
- Add annotation: "Rate limiting active - 100 requests blocked"

**Create PowerPoint slide showing rate limits:**

| Endpoint Pattern | Limit | Window | Purpose |
|-----------------|-------|--------|---------|
| `/api/v1/ml/training/*` | 30 req | 60 sec | Prevent training spam |
| `/api/v1/ml/ensemble/*` | 30 req | 60 sec | Prevent ensemble spam |
| `/api/v1/upload/*` | 20 req | 60 sec | Prevent upload abuse |
| `/api/v1/auth/login` | **10 req** | 60 sec | Prevent brute force |
| `/api/v1/admin/*` | 50 req | 60 sec | Admin protection |
| **All other endpoints** | 100 req | 60 sec | General protection |

**Caption:**
"Sliding window rate limiting protects all API endpoints from abuse. Login endpoint limited to 10 requests/minute to prevent brute-force attacks."

---

## 🔑 SECTION 3: API Key Management

### 📸 Screenshot 44: Create API Key (Swagger UI)

**What to capture:** API key creation endpoint with response

**Location:** http://100.106.132.15:8001/docs

**Prerequisites:**
1. Login as admin user and get JWT token
2. Authorize Swagger with the token

**Steps:**
1. Find: `POST /api/v1/admin/keys` (in "API Key Management" section)
2. Click **"Try it out"**
3. Enter request body:
```json
{
  "name": "Mobile App Integration",
  "description": "API access for mobile application",
  "role": "researcher",
  "scopes": ["read:patients", "write:predictions"],
  "rate_limit": 2000,
  "expires_in_days": 90
}
```
4. Click **"Execute"**
5. **Screenshot the Response (200 OK):**

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

**What to highlight:**
- **Circle the full API key** (long string starting with `usm_key_`)
- **Box the key_prefix** (first 14 characters, used for identification)
- **Highlight expires_at** (90 days from creation)
- **Circle role: "researcher"** (restricted permissions)
- Add warning: "⚠️ API key shown only once - must be saved immediately!"

**Caption:**
"API keys enable external system integration with role-based permissions and automatic expiration. Keys are SHA-256 hashed before storage."

---

### 📸 Screenshot 45: API Keys Table (Database)

**What to capture:** PostgreSQL table showing stored API keys

**Location:** SSH to server or pgAdmin

**SQL Query:**
```sql
SELECT 
    id,
    name,
    key_prefix,
    role,
    rate_limit,
    usage_count,
    last_used_at,
    expires_at,
    is_active,
    is_revoked,
    created_by,
    created_at
FROM api_keys
ORDER BY created_at DESC
LIMIT 5;
```

**Expected result to screenshot:**

| id | name | key_prefix | role | rate_limit | usage_count | last_used_at | expires_at | is_active | is_revoked | created_by | created_at |
|----|------|-----------|------|-----------|-------------|--------------|------------|-----------|-----------|-----------|-----------|
| 1 | Mobile App | usm_key_abc123 | researcher | 2000 | 0 | NULL | 2026-07-25 | true | false | s.nasrin | 2026-04-25 |
| 2 | Analytics System | usm_key_def456 | viewer | 1000 | 42 | 2026-04-26 | 2027-01-01 | true | false | s.nasrin | 2026-04-20 |
| 3 | Test Key | usm_key_ghi789 | researcher | 500 | 156 | 2026-04-26 | 2026-06-01 | false | true | s.nasrin | 2026-03-15 |

**What to highlight:**
- **Circle key_prefix column** (note: full key hash NOT stored in plain text)
- **Box usage_count and last_used_at** (tracking usage)
- **Highlight is_revoked: true** on row 3 (key revoked for security)
- Add annotation: "Full keys stored as SHA-256 hash, only prefix visible"

**Create separate screenshot showing indexes:**
```sql
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'api_keys';
```

**Expected indexes:**
```
idx_api_keys_hash        → CREATE INDEX ON api_keys(key_hash)
idx_api_keys_prefix      → CREATE INDEX ON api_keys(key_prefix)
idx_api_keys_created_by  → CREATE INDEX ON api_keys(created_by)
```

**Caption:**
"API keys table stores hashed keys (SHA-256) with usage tracking, expiration, and revocation support. Three indexes optimize lookup performance."

---

## 📊 SECTION 4: Audit Logging & Compliance

### 📸 Screenshot 46: Audit Logs (Database)

**What to capture:** Comprehensive audit trail in PostgreSQL

**Location:** SSH to server or pgAdmin

**SQL Query:**
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

**Expected result to screenshot:**

| id | username | action | resource_type | endpoint | http_method | ip_address | response_status | response_time_ms | is_sensitive | timestamp |
|----|----------|--------|--------------|----------|------------|-----------|----------------|-----------------|-------------|-----------|
| 145 | s.nasrin | API_KEY_CREATED | api_key | /admin/keys | POST | 100.106.132.1 | 200 | 45 | true | 2026-04-26 10:30:00 |
| 144 | s.nasrin | DATASET_PREPARED | dataset | /ml/prepare-dataset | POST | 100.106.132.1 | 200 | 2341 | false | 2026-04-26 10:25:00 |
| 143 | s.nasrin | TRAINING_STARTED | training_job | /ml/train/base-model | POST | 100.106.132.1 | 200 | 89 | false | 2026-04-26 10:20:00 |
| 142 | researcher1 | PREDICTION_MADE | prediction | /ml/predict | POST | 100.106.132.5 | 200 | 234 | false | 2026-04-26 10:15:00 |
| 141 | researcher1 | PATIENT_VIEWED | patient | /patients/123 | GET | 100.106.132.5 | 200 | 23 | true | 2026-04-26 10:10:00 |
| 140 | unknown | USER_LOGIN_FAILED | auth | /auth/login | POST | 203.123.45.67 | 401 | 12 | true | 2026-04-26 10:05:00 |

**What to highlight:**
- **Circle is_sensitive: true** (flagged for security review)
- **Box the failed login attempt** (row 6, potential attack)
- **Highlight response_time_ms** (performance monitoring)
- **Circle API_KEY_CREATED action** (critical security event)

**Create second screenshot for data access logs:**
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

**Expected result:**

| id | username | patient_anonymous_id | fields_accessed | access_purpose | consent_verified | accessed_at |
|----|----------|---------------------|----------------|---------------|-----------------|------------|
| 23 | s.nasrin | PAT_001 | ["diagnosis", "lab_results", "medications"] | Clinical research | true | 2026-04-26 10:10:00 |
| 22 | researcher1 | PAT_002 | ["lab_results", "biomarkers"] | Model training | true | 2026-04-26 09:45:00 |

**What to highlight:**
- **Circle fields_accessed** (JSONB column tracks exact fields viewed)
- **Box access_purpose** (required for PDPA compliance)
- **Highlight consent_verified: true** (legal requirement)

**Create PowerPoint slide - Audit Log Coverage:**

| Event Type | Logged? | Contains |
|-----------|---------|----------|
| **User Authentication** | ✅ Yes | WHO, WHEN, WHERE (IP), SUCCESS/FAIL |
| **Data Access** | ✅ Yes | USER, PATIENT, FIELDS, PURPOSE, CONSENT |
| **Model Training** | ✅ Yes | USER, DATASET, PARAMS, DURATION |
| **Predictions** | ✅ Yes | USER, PATIENT, MODEL, RESULT, CONFIDENCE |
| **Admin Actions** | ✅ Yes | USER, ACTION, RESOURCE, BEFORE/AFTER |
| **API Key Operations** | ✅ Yes | CREATOR, KEY_PREFIX, PERMISSIONS |
| **Security Events** | ✅ Yes | FAILED_LOGINS, RATE_LIMITS, 403_ERRORS |

**Caption:**
"Comprehensive audit logging captures WHO, WHAT, WHEN, WHERE, WHY for all platform operations. Critical for PDPA compliance and security monitoring."

---

## 📊 SECTION 5: Security Comparison (PowerPoint)

### 📸 Screenshot 47: Security Implementation Comparison Table

**What to create:** Comparison table showing security evolution

**Tool:** PowerPoint

**Create this table:**

| Security Feature | Sprint 1-2 (Original) | Sprint 3 (Enhanced) | Status |
|-----------------|----------------------|-------------------|--------|
| **Authentication** | Session-based cookies | ✅ JWT tokens (12-hour expiry) | ✅ Complete |
| **Authorization** | Basic login | ✅ RBAC (3 roles: Admin/Researcher/Viewer) | ✅ Complete |
| **Transport Security** | ❌ HTTP only | ✅ HTTPS/TLS 1.2+ with nginx | ✅ Complete |
| **Rate Limiting** | ❌ None | ✅ Per-endpoint limits (10-100 req/min) | ✅ Complete |
| **API Access Control** | ❌ JWT only | ✅ API key management with expiration | ✅ Complete |
| **Audit Trail** | ❌ None | ✅ Comprehensive logging (22 columns) | ✅ Complete |
| **PDPA Compliance** | ❌ None | ✅ Data access logs with consent tracking | ✅ Complete |
| **Security Headers** | ❌ None | ✅ HSTS, X-Frame-Options, CSP | ✅ Complete |
| **Password Security** | Basic hashing | ✅ bcrypt with salt | ✅ Complete |
| **Key Management** | ❌ None | ✅ SHA-256 hashing, auto-expiration | ✅ Complete |

**Styling:**
- Title: "Security Implementation Evolution - Sprint 1-3"
- Use green checkmarks ✅ and red X ❌
- Highlight Sprint 3 column (green background)
- Add subtitle: "From Basic Authentication to Enterprise-Grade Security"

---

## 📊 SECTION 6: Security Tables Summary (PowerPoint)

**Create slide showing database schema:**

### **api_keys table** (18 columns, 3 indexes)
```
- id, name, key_hash, key_prefix
- role, scopes (JSONB), rate_limit
- created_by, created_at, expires_at
- last_used_at, usage_count
- is_active, is_revoked, revoked_at, revoked_by
```

**Indexes:**
- `idx_api_keys_hash` → Fast key verification
- `idx_api_keys_prefix` → Management UI lookup
- `idx_api_keys_created_by` → Audit queries

---

### **audit_logs table** (22 columns, 6 indexes)
```
WHO: user_id, username, user_role
WHAT: action, resource_type, resource_id, http_method
WHEN: timestamp
WHERE: ip_address, user_agent, endpoint
WHY: description, request_payload, changes
HOW: response_time_ms, response_status, data_accessed
FLAGS: is_sensitive, is_suspicious, success
```

**Indexes:**
- `idx_audit_logs_user_timestamp` → User activity queries
- `idx_audit_logs_action_timestamp` → Security event analysis
- `idx_audit_logs_resource` → Resource access tracking
- `idx_audit_logs_ip_timestamp` → IP-based threat detection
- `idx_audit_logs_action` → Action-type filtering
- `idx_audit_logs_timestamp` → Chronological queries

---

### **data_access_logs table** (13 columns, 3 indexes)
```
- id, user_id, username, user_role
- patient_id, patient_anonymous_id
- fields_accessed (JSONB)
- access_purpose, consent_verified
- access_level (read/write/delete)
- accessed_at, ip_address
```

**Indexes:**
- `idx_data_access_patient_time` → Patient access history
- `idx_data_access_user_time` → User activity audit
- `idx_data_access_accessed_at` → Time-based queries

**Caption:**
"Three new security tables with 12 indexes support enterprise-grade security, compliance, and auditing requirements."

---

## ✅ SCREENSHOT CHECKLIST

### Core Security (Existing - See TSD_SCREENSHOT_GUIDE_FUNCTIONAL.md)
- [ ] Screenshot 29: JWT Login Response (Swagger)
- [ ] Screenshot 30: Swagger Authorization (JWT token)
- [ ] Screenshot 31: RBAC Permission Matrix (PowerPoint)
- [ ] Screenshot 32: Users Table with Roles (Database)
- [ ] Screenshot 33: Admin UI View (full sidebar)
- [ ] Screenshot 34: Researcher UI View (limited sidebar)
- [ ] Screenshot 35: Viewer UI View (minimal sidebar)
- [ ] Screenshot 36: RBAC 403 Forbidden (Swagger)

### **NEW - Production Security (This Guide)**
- [ ] Screenshot 42: HTTPS Connection (Browser with padlock)
- [ ] Screenshot 43: Rate Limiting 429 Errors (Terminal)
- [ ] Screenshot 44: API Key Creation (Swagger)
- [ ] Screenshot 45: API Keys Table (Database)
- [ ] Screenshot 46: Audit Logs Tables (Database - 2 queries)
- [ ] Screenshot 47: Security Comparison Table (PowerPoint)
- [ ] Screenshot 48: nginx HTTPS Configuration (Terminal)

### **Additional PowerPoint Slides**
- [ ] Rate Limits by Endpoint (Table)
- [ ] Audit Log Coverage (Table)
- [ ] Security Tables Schema (Slide)

---

## 📝 NOTES FOR TSD DOCUMENT

### Security Achievements (Sprint 3)

**1. Transport Layer Security**
- HTTPS/TLS 1.2+ encryption via nginx reverse proxy
- HTTP-to-HTTPS automatic redirection
- Security headers (HSTS, X-Frame-Options, CSP)
- Self-signed certificate for development, Let's Encrypt for production

**2. API Protection**
- Sliding window rate limiting on all endpoints
- Per-endpoint limits (10-100 requests/minute)
- Prevents brute-force attacks, DDoS, and API abuse
- Rate limit headers inform clients of remaining quota

**3. External Integration**
- API key management for third-party systems
- SHA-256 key hashing (never stores plain keys)
- Role-based permissions (admin/researcher/viewer)
- Automatic expiration and manual revocation
- Usage tracking and monitoring

**4. Compliance & Auditing**
- Comprehensive audit logs (WHO, WHAT, WHEN, WHERE, WHY)
- Specialized data access logs for PDPA compliance
- Sensitive action flagging (login, API key creation, patient access)
- 22-column audit trail with performance metrics
- JSONB fields for flexible payload storage

**5. Security Headers**
```nginx
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

---

## 🎯 TESTING COMMANDS (For Verification)

### Test HTTPS
```bash
# Should return healthy status with TLS
curl -k https://100.106.132.15/health
```

### Test Rate Limiting
```bash
# Should see 429 errors after limit
for i in {1..110}; do curl -s -o /dev/null -w "%{http_code}\n" http://100.106.132.15:8001/api/v1/auth/login; done | sort | uniq -c
```

### Test API Key Creation
```bash
TOKEN=$(curl -X POST "http://100.106.132.15:8001/api/v1/auth/login" \
  -d "username=s.nasrin&password=USM@22" | jq -r '.access_token')

curl -X POST "http://100.106.132.15:8001/api/v1/admin/keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Key","role":"researcher","rate_limit":1000,"expires_in_days":90}'
```

### View Audit Logs
```bash
docker exec -e PGPASSWORD=Mtai2026! usm-autoimmune-postgres \
  psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "SELECT username, action, endpoint, response_status, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 10;"
```

---

## 📚 RELATED DOCUMENTATION

- **Deployment Guide:** [PRODUCTION_READINESS_DEPLOYMENT.md](../../PRODUCTION_READINESS_DEPLOYMENT.md)
- **JWT/RBAC Screenshots:** [TSD_SCREENSHOT_GUIDE_FUNCTIONAL.md](TSD_SCREENSHOT_GUIDE_FUNCTIONAL.md#35-security--governance)
- **Security Implementation:** [DAY1_SECURITY_COMPLETE.md](../../DAY1_SECURITY_COMPLETE.md)
- **Platform Summary:** [PLATFORM_COMPLETION_SUMMARY.md](../../PLATFORM_COMPLETION_SUMMARY.md)

---

**Document Status:** ✅ Ready for Screenshot Collection  
**Next Steps:** 
1. Follow this guide to collect all 7 new screenshots
2. Create 3 PowerPoint slides (comparison tables)
3. Compile into TSD Security section
4. Cross-reference with functional screenshots (29-36)

**Estimated Time:** 30-45 minutes for all screenshots + slides
