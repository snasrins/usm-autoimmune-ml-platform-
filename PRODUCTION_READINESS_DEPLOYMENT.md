# 🔐 PRODUCTION READINESS DEPLOYMENT GUIDE
# USM Autoimmune ML Platform - Security & Compliance Features
# Sprint 3 - April 2026

## 📋 Overview

This guide covers the deployment of **4 critical production features**:
1. ✅ **HTTPS/TLS** - Secure communication
2. ✅ **Rate Limiting** - API abuse prevention
3. ✅ **API Key Management** - External access control
4. ✅ **Audit Logging** - Compliance & security monitoring

---

## 🚀 DEPLOYMENT STEPS

### **Step 1: Database Migration (5 minutes)**

Deploy new security tables to PostgreSQL:

```bash
# On server
docker cp migrations/security_compliance_migration.sql usm-autoimmune-postgres:/tmp/

docker exec -e PGPASSWORD=Mtai2026! usm-autoimmune-postgres \
  psql -U usm_db_admin -d usm_autoimmune_registry \
  -f /tmp/security_compliance_migration.sql
```

**✅ Expected Output:**
```
CREATE TABLE
CREATE INDEX
...
Security & Compliance Migration Complete!
```

**Verify:**
```bash
docker exec -e PGPASSWORD=Mtai2026! usm-autoimmune-postgres \
  psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "SELECT tablename FROM pg_tables WHERE tablename IN ('api_keys', 'audit_logs', 'data_access_logs');"
```

---

### **Step 2: Deploy Updated Backend (5 minutes)**

Upload updated files via WinSCP:

**Files to upload:**
```
app/main.py                            → Updated with middleware
app/models/__init__.py                 → Added new models
app/models/api_key.py                  → NEW
app/models/audit_log.py                → NEW
app/middleware/rate_limiter.py         → NEW
app/middleware/audit_logger.py         → NEW
app/api/endpoints/api_keys.py          → NEW
app/api/endpoints/admin.py             → Fixed stats endpoint
frontend/src/services/api-complete.js  → Fixed predictions path
```

**Restart backend:**
```bash
docker-compose restart usm-autoimmune-backend

# Or full rebuild if needed
docker-compose up -d --build usm-autoimmune-backend
```

**Verify:**
```bash
curl http://100.106.132.15:8001/health
# Should show: "status": "healthy"

curl http://100.106.132.15:8001/docs
# Should show Swagger UI with new "API Key Management" section
```

---

### **Step 3: Setup HTTPS/TLS (10 minutes)**

**Option A: Self-Signed Certificate (Internal Use)**

```bash
# On server
chmod +x setup-https.sh
./setup-https.sh
```

This will:
- Install nginx
- Generate self-signed certificate
- Configure reverse proxy
- Enable HTTPS on port 443

**Option B: Let's Encrypt (If you have a domain)**

```bash
# Install certbot
apt-get install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
certbot --nginx -d your-domain.usm.my

# Auto-renewal
systemctl enable certbot.timer
```

**Verify HTTPS:**
```bash
curl -k https://100.106.132.15/health
# -k flag skips certificate verification for self-signed
```

---

### **Step 4: Test Security Features (10 minutes)**

#### **1. Test Rate Limiting:**

```bash
# Make 110 rapid requests (should hit limit at 100)
for i in {1..110}; do
  curl -s http://100.106.132.15:8001/api/v1/auth/login -o /dev/null -w "%{http_code}\n" &
done
wait

# Expected: First 100 return 200/401, rest return 429 (Too Many Requests)
```

#### **2. Test API Key Management:**

```bash
# Login as admin
TOKEN=$(curl -X POST "http://100.106.132.15:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=s.nasrin&password=USM@22" | jq -r '.access_token')

# Create API key
curl -X POST "http://100.106.132.15:8001/api/v1/admin/keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test API Key",
    "description": "Testing API key management",
    "role": "researcher",
    "rate_limit": 500,
    "expires_in_days": 90
  }'

# Expected: Returns API key starting with "usm_key_..."
# ⚠️ SAVE THIS KEY - it's shown only once!
```

#### **3. Test Audit Logging:**

```bash
# Make some API calls
curl -H "Authorization: Bearer $TOKEN" \
  "http://100.106.132.15:8001/api/v1/admin/stats"

# Check audit logs
docker exec -e PGPASSWORD=Mtai2026! usm-autoimmune-postgres \
  psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "SELECT id, username, action, endpoint, response_status, timestamp 
      FROM audit_logs 
      ORDER BY timestamp DESC 
      LIMIT 5;"
```

---

## 📊 VALIDATION CHECKLIST

### ✅ **Backend Security:**
- [ ] Rate limiting active (429 errors after 100 req/min)
- [ ] API keys endpoint accessible at `/api/v1/admin/keys`
- [ ] Audit logs populating in database
- [ ] Admin stats endpoint working (no 500 errors)
- [ ] Predictions history endpoint working (no 404 errors)

### ✅ **HTTPS/TLS:**
- [ ] nginx running and accessible
- [ ] HTTP (port 80) redirects to HTTPS (port 443)
- [ ] SSL certificate valid (or self-signed warning appears)
- [ ] Backend API accessible via `https://100.106.132.15/api/`
- [ ] Frontend accessible via `https://100.106.132.15/`

### ✅ **Database:**
- [ ] `api_keys` table exists with indexes
- [ ] `audit_logs` table exists with indexes
- [ ] `data_access_logs` table exists with indexes
- [ ] Permissions granted to `usm_db_admin`

---

## 🎯 RATE LIMIT CONFIGURATION

Current limits (can be adjusted in `app/middleware/rate_limiter.py`):

| **Endpoint Pattern**           | **Limit**              | **Window** |
|--------------------------------|------------------------|------------|
| `/api/v1/ml/training/`         | 30 requests            | 60 seconds |
| `/api/v1/ml/ensemble/`         | 30 requests            | 60 seconds |
| `/api/v1/upload/`              | 20 requests            | 60 seconds |
| `/api/v1/auth/login`           | 10 requests            | 60 seconds |
| `/api/v1/admin/`               | 50 requests            | 60 seconds |
| **Default (all other)**        | 100 requests           | 60 seconds |

**Rate limit headers returned:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1777020000
```

---

## 🔑 API KEY USAGE

### **Creating API Keys:**

```python
# Python example
import requests

# Login to get JWT token
response = requests.post(
    "http://100.106.132.15:8001/api/v1/auth/login",
    data={"username": "s.nasrin", "password": "USM@22"}
)
token = response.json()["access_token"]

# Create API key
response = requests.post(
    "http://100.106.132.15:8001/api/v1/admin/keys",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "name": "Mobile App",
        "description": "API access for mobile application",
        "role": "researcher",
        "scopes": ["read:patients", "write:predictions"],
        "rate_limit": 2000,
        "expires_in_days": 365
    }
)

api_key = response.json()["key"]  # usm_key_abc123...
print(f"API Key: {api_key}")
# ⚠️ SAVE THIS - shown only once!
```

### **Using API Keys:**

```bash
# Instead of JWT token, use API key in header
curl -H "X-API-Key: usm_key_abc123..." \
  "http://100.106.132.15:8001/api/v1/ml/predictions/history"
```

---

## 📈 MONITORING & COMPLIANCE

### **Audit Log Queries:**

```sql
-- Recent security-sensitive actions
SELECT 
    username,
    action,
    resource_type,
    timestamp,
    ip_address,
    success
FROM audit_logs
WHERE is_sensitive = true
ORDER BY timestamp DESC
LIMIT 20;

-- Failed login attempts (potential attacks)
SELECT 
    ip_address,
    COUNT(*) as failed_attempts,
    MAX(timestamp) as last_attempt
FROM audit_logs
WHERE action = 'USER_LOGIN_FAILED'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING COUNT(*) > 5
ORDER BY failed_attempts DESC;

-- Data access tracking (PDPA compliance)
SELECT 
    username,
    patient_anonymous_id,
    access_purpose,
    COUNT(*) as access_count,
    MAX(accessed_at) as last_access
FROM data_access_logs
GROUP BY username, patient_anonymous_id, access_purpose
ORDER BY access_count DESC
LIMIT 20;

-- API usage by endpoint
SELECT 
    endpoint,
    COUNT(*) as request_count,
    AVG(response_time_ms) as avg_response_ms,
    COUNT(CASE WHEN success = false THEN 1 END) as error_count
FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY endpoint
ORDER BY request_count DESC
LIMIT 10;
```

### **API Key Usage:**

```sql
-- Active API keys
SELECT 
    name,
    key_prefix,
    role,
    usage_count,
    last_used_at,
    expires_at
FROM api_keys
WHERE is_active = true
  AND is_revoked = false
ORDER BY last_used_at DESC;

-- Expired or unused API keys
SELECT 
    name,
    key_prefix,
    created_at,
    expires_at,
    usage_count,
    CASE 
        WHEN expires_at < NOW() THEN 'EXPIRED'
        WHEN last_used_at IS NULL THEN 'NEVER USED'
        ELSE 'OK'
    END as status
FROM api_keys
WHERE is_active = true
ORDER BY created_at DESC;
```

---

## 🔒 SECURITY BEST PRACTICES

### **1. API Key Management:**
- ✅ Create separate keys for each external integration
- ✅ Use least-privilege roles (viewer/researcher, not admin)
- ✅ Set expiration dates (max 1 year)
- ✅ Rotate keys regularly (every 90 days recommended)
- ✅ Revoke keys immediately when compromised
- ✅ Monitor usage patterns for anomalies

### **2. Rate Limiting:**
- ✅ Adjust limits based on actual usage patterns
- ✅ Monitor 429 errors (too many rejections = legitimate traffic blocked)
- ✅ Whitelist trusted IPs if needed (future enhancement)
- ✅ Use exponential backoff on client side

### **3. Audit Logging:**
- ✅ Review sensitive actions daily
- ✅ Alert on suspicious patterns (many failed logins, unusual data access)
- ✅ Archive logs older than 2 years (PDPA compliance)
- ✅ Export logs for external SIEM if needed

### **4. HTTPS/TLS:**
- ✅ Use Let's Encrypt for production (free, auto-renewing)
- ✅ Enable HSTS (HTTP Strict Transport Security)
- ✅ Use TLS 1.2+ only (disable TLS 1.0/1.1)
- ✅ Regular certificate renewal checks

---

## 🚨 TROUBLESHOOTING

### **Issue: Rate limiting too strict**
```python
# Edit app/middleware/rate_limiter.py
self.rate_limits = {
    "default": (200, 60)  # Increase from 100 to 200
}
# Restart backend
```

### **Issue: HTTPS not working**
```bash
# Check nginx status
systemctl status nginx

# Check nginx logs
tail -f /var/log/nginx/usm-autoimmune-error.log

# Test configuration
nginx -t

# Reload configuration
systemctl reload nginx
```

### **Issue: Audit logs not populating**
```bash
# Check database connection
docker exec -e PGPASSWORD=Mtai2026! usm-autoimmune-postgres \
  psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "SELECT COUNT(*) FROM audit_logs;"

# Check backend logs
docker logs usm-autoimmune-backend --tail=50 | grep AUDIT
```

---

## ✅ DEPLOYMENT COMPLETION

After completing all steps, your platform will have:

| **Feature**                | **Status** | **Impact**                              |
|----------------------------|------------|-----------------------------------------|
| **HTTPS/TLS**              | ✅ Active  | Encrypted communication                 |
| **Rate Limiting**          | ✅ Active  | API abuse prevention                    |
| **API Key Management**     | ✅ Active  | External integration control            |
| **Audit Logging**          | ✅ Active  | Compliance & security monitoring        |
| **Admin Stats Fixed**      | ✅ Fixed   | Dashboard no longer shows 500 errors    |
| **Predictions API Fixed**  | ✅ Fixed   | Dashboard no longer shows 404 errors    |

---

## 📞 SUPPORT

For issues or questions:
- **Technical Lead:** Syarifah Fajriyah
- **Documentation:** See `SYSTEM_INTEGRATION_TESTING_SPRINT1-3.md`
- **Security:** Review audit logs regularly via SQL queries above

---

**Platform Version:** 3.0.0 (Production Ready)  
**Deployment Date:** April 24, 2026  
**Next Review:** July 2026 (3 months)
