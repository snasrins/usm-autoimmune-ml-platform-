# JWT Security Enhancements - Sprint 2 Days 2-3

**Project:** USM Autoimmune ML Platform  
**Engineer:** Syarifah Fajriyah  
**Date:** March 31, 2026  
**Sprint:** Sprint 2 Days 2-3  
**Tickets:** USMA-88, USMA-89, USMA-90, USMA-91 (partial)

---

## Table of Contents
1. [Overview](#overview)
2. [What We Built](#what-we-built)
3. [Why These Security Features Matter](#why-these-security-features-matter)
4. [Architecture & Database Schema](#architecture--database-schema)
5. [Implementation Details](#implementation-details)
6. [API Endpoints](#api-endpoints)
7. [Testing Guide](#testing-guide)
8. [Security Best Practices](#security-best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Sprint 2 Days 2-3 implemented **enterprise-grade JWT security** with three critical features:

1. **Refresh Token Mechanism** (USMA-88) - Long-lived tokens with database tracking
2. **Token Versioning** (USMA-90) - Global token invalidation per user
3. **Token Blacklist** (USMA-89) - Immediate access token revocation

These features prevent common JWT security vulnerabilities and enable proper session management.

---

## What We Built

### Feature 1: Refresh Tokens (USMA-88)

**Problem:** JWT access tokens are short-lived (60 min). Users must re-login frequently, poor UX.

**Solution:** 
- Issue **refresh tokens** (7-day expiry) alongside access tokens
- Store refresh tokens in database for tracking
- Exchange refresh token for new access token without re-login
- Rotate tokens on each refresh (revoke old, issue new)

**Benefits:**
- ✅ Users stay logged in for 7 days
- ✅ Can track and revoke specific sessions
- ✅ Token rotation prevents replay attacks
- ✅ Database audit trail of all active sessions

### Feature 2: Token Versioning (USMA-90)

**Problem:** No way to invalidate ALL tokens for a user (e.g., password change, security breach).

**Solution:**
- Add `token_version` column to `users` table
- Include `token_version` in every JWT payload
- Increment version on "logout all" → invalidates ALL existing tokens
- Validate version on every API request

**Benefits:**
- ✅ Instant global token invalidation
- ✅ Logout from all devices
- ✅ Security response (compromised account)
- ✅ No database lookup needed (version in JWT)

### Feature 3: Token Blacklist (USMA-89)

**Problem:** Access tokens can't be revoked before expiry (JWT is stateless).

**Solution:**
- Add `revoked_tokens` table (blacklist)
- Assign unique `jti` (JWT ID) to every access token
- On logout, add token `jti` to blacklist
- Check blacklist on every protected endpoint

**Benefits:**
- ✅ Immediate access token revocation
- ✅ Proper logout functionality
- ✅ Compliance with security requirements
- ✅ Audit trail of revoked tokens

---

## Why These Security Features Matter

### The Problem with Basic JWT

**Basic JWT Implementation** (Sprint 1):
```python
# Login
access_token = create_jwt(user_id, expires_in=60_min)
return {"access_token": access_token}

# Problems:
# ❌ Token valid until expiry (can't revoke)
# ❌ User must login every 60 minutes
# ❌ No way to logout (token stays valid)
# ❌ No way to invalidate all sessions
# ❌ Stolen token works until expiry
```

**Enhanced JWT Implementation** (Sprint 2):
```python
# Login
access_token = create_jwt(user_id, token_version, jti, expires_in=60_min)
refresh_token = create_jwt(user_id, token_version, jti, expires_in=7_days)
store_refresh_token_in_db(refresh_token)
return {"access_token": access_token, "refresh_token": refresh_token}

# Solutions:
# ✅ Access token revocable via blacklist (jti)
# ✅ Refresh token extends session to 7 days
# ✅ Logout adds token to blacklist
# ✅ Logout-all increments token_version
# ✅ Stolen token detected via blacklist/version check
```

### Real-World Security Scenarios

**Scenario 1: User Logs Out**
```
Without Blacklist:
1. User clicks logout
2. Frontend deletes tokens
3. ❌ Stolen token still works until expiry (up to 60 min)
4. ❌ Attacker can use stolen token

With Blacklist:
1. User clicks logout
2. Backend adds token jti to blacklist
3. ✅ Token immediately invalid
4. ✅ Attacker's stolen token rejected: "Token has been revoked"
```

**Scenario 2: Compromised Account**
```
Without Token Versioning:
1. Admin detects suspicious activity
2. ❌ No way to kill all active sessions
3. ❌ Must wait for tokens to expire (up to 7 days!)
4. ❌ Attacker keeps access during investigation

With Token Versioning:
1. Admin clicks "Logout from all devices"
2. ✅ token_version incremented (0 → 1)
3. ✅ All tokens with version=0 instantly invalid
4. ✅ Attacker locked out immediately
5. ✅ User must re-login with new password
```

**Scenario 3: Token Refresh**
```
Without Refresh Tokens:
1. Access token expires after 60 min
2. User forced to re-login
3. ❌ Poor user experience
4. ❌ Users choose weak passwords (login fatigue)

With Refresh Tokens:
1. Access token expires after 60 min
2. Frontend automatically refreshes via /refresh endpoint
3. ✅ New access token issued (no password needed)
4. ✅ User stays logged in for 7 days
5. ✅ Old refresh token rotated (security)
```

---

## Architecture & Database Schema

### Database Tables

#### 1. refresh_tokens
**Purpose:** Track long-lived refresh tokens

```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    device_info VARCHAR(255),  -- User-Agent for tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    
    INDEX idx_refresh_token (token),
    INDEX idx_refresh_user (user_id),
    INDEX idx_refresh_revoked (is_revoked)
);
```

**Example Data:**
```
id  user_id  token                  expires_at           is_revoked  device_info
1   4        eyJhbGci...            2026-04-07 02:56:01  false       curl/8.5.0
2   4        eyJzdWIi...            2026-04-07 03:10:21  true        Chrome/121
```

#### 2. revoked_tokens (Blacklist)
**Purpose:** Block revoked access tokens immediately

```sql
CREATE TABLE revoked_tokens (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(255) UNIQUE NOT NULL,  -- JWT ID (unique token identifier)
    token_type VARCHAR(20) NOT NULL,   -- 'access' or 'refresh'
    user_id INTEGER NOT NULL,
    revoked_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,   -- Original token expiry
    reason VARCHAR(100),               -- 'logout', 'security', 'admin_action'
    
    INDEX idx_revoked_jti (jti),
    INDEX idx_revoked_jti_expires (jti, expires_at)  -- Composite for fast lookup
);
```

**Example Data:**
```
id  jti                             token_type  user_id  reason   expires_at
1   EHDvfkWdSagWFvqyBY3ZYD-u7SVNsF  access      4        logout   2026-03-31 03:50:26
2   k76IDNxIhTG0NfawSwhHFKVkogzmWo  access      4        security 2026-03-31 04:12:15
```

#### 3. users.token_version
**Purpose:** Enable global token invalidation

```sql
ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 0 NOT NULL;
```

**Token Lifecycle:**
```
1. User logs in → token_version=0 → tokens issued with version=0
2. User logs out from one device → blacklist that token, version stays 0
3. User logs out from ALL devices → increment version to 1
4. All tokens with version=0 now invalid
5. User must re-login → new tokens issued with version=1
```

---

## Implementation Details

### File Structure

```
app/
├── models/
│   ├── refresh_token.py       # RefreshToken model (NEW)
│   ├── revoked_token.py       # RevokedToken model (NEW)
│   ├── user.py                # Added token_version column
│   └── __init__.py            # Export new models
├── api/
│   ├── endpoints/
│   │   └── auth.py            # Enhanced with refresh/logout/blacklist
│   └── deps.py                # Token validation checks blacklist + version
├── core/
│   └── security.py            # JWT creation (unchanged)
└── alembic/
    └── versions/
        ├── 9a2e81360415_...   # Migration: refresh_tokens + token_version
        └── cd668b5a9c62_...   # Migration: revoked_tokens

```

### Key Code Changes

#### 1. Token Creation (auth.py - Login)

**Before (Sprint 1):**
```python
access_token = create_access_token(data={"sub": user.username})
return {"access_token": access_token, "token_type": "bearer"}
```

**After (Sprint 2):**
```python
# Access token with jti and token_version
access_token_data = {
    "sub": user.username,
    "user_id": user.id,
    "token_version": user.token_version,  # For global invalidation
    "jti": secrets.token_urlsafe(32)      # For blacklist checking
}
access_token = create_access_token(data=access_token_data)

# Refresh token stored in database
refresh_token_data = {
    "sub": user.username,
    "user_id": user.id,
    "token_version": user.token_version,
    "jti": secrets.token_urlsafe(32)
}
refresh_token = create_refresh_token(data=refresh_token_data)

# Store refresh token in DB
db_refresh_token = RefreshToken(
    user_id=user.id,
    token=refresh_token,
    expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    device_info=user_agent
)
db.add(db_refresh_token)
db.commit()

return {
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "bearer"
}
```

#### 2. Token Validation (deps.py)

**Before (Sprint 1):**
```python
async def get_current_user(token: str, db: Session):
    payload = decode_token(token)
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    return user
```

**After (Sprint 2):**
```python
async def get_current_user(token: str, db: Session):
    payload = decode_token(token)
    username = payload.get("sub")
    token_version = payload.get("token_version")
    jti = payload.get("jti")
    
    # 1. Check blacklist (revoked tokens)
    if jti:
        revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
        if revoked:
            raise HTTPException(401, "Token has been revoked")
    
    # 2. Get user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(401, "User not found")
    
    # 3. Validate token version
    if token_version != user.token_version:
        raise HTTPException(401, "Token has been invalidated. Please login again.")
    
    return user
```

#### 3. Refresh Token Endpoint (auth.py)

```python
@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str, db: Session):
    # 1. Decode and validate refresh token
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")
    
    user_id = payload.get("user_id")
    token_version = payload.get("token_version")
    
    # 2. Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    
    # 3. Check token version
    if token_version != user.token_version:
        raise HTTPException(401, "Token has been invalidated")
    
    # 4. Check refresh token in database
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.user_id == user_id
    ).first()
    
    if not db_token:
        raise HTTPException(401, "Refresh token not found")
    if db_token.is_revoked:
        raise HTTPException(401, "Refresh token has been revoked")
    if db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(401, "Refresh token has expired")
    
    # 5. Revoke old refresh token (rotation)
    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    
    # 6. Create new tokens
    new_access_token = create_access_token({
        "sub": user.username,
        "user_id": user.id,
        "token_version": user.token_version,
        "jti": secrets.token_urlsafe(32)
    })
    
    new_refresh_token = create_refresh_token({
        "sub": user.username,
        "user_id": user.id,
        "token_version": user.token_version,
        "jti": secrets.token_urlsafe(32)
    })
    
    # 7. Store new refresh token
    new_db_token = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(new_db_token)
    db.commit()
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
```

#### 4. Logout with Blacklist (auth.py)

```python
@router.post("/logout")
async def logout(
    current_user: User,
    refresh_token: Optional[str],
    authorization: Optional[str] = Header(None),
    db: Session
):
    # 1. Blacklist access token
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.replace("Bearer ", "")
        payload = decode_token(access_token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if jti:
            revoked_access = RevokedToken(
                jti=jti,
                token_type="access",
                user_id=current_user.id,
                expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
                reason="logout"
            )
            db.add(revoked_access)
    
    # 2. Revoke refresh token
    if refresh_token:
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == current_user.id
        ).first()
        
        if db_token and not db_token.is_revoked:
            db_token.is_revoked = True
            db_token.revoked_at = datetime.now(timezone.utc)
    
    db.commit()
    return {"message": "Successfully logged out"}
```

#### 5. Logout All Devices (auth.py)

```python
@router.post("/logout-all")
async def logout_all_devices(current_user: User, db: Session):
    # 1. Increment token_version (invalidates ALL tokens)
    current_user.token_version += 1
    db.commit()
    
    # 2. Also revoke all refresh tokens in database
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    db.commit()
    
    return {"message": "Successfully logged out from all devices"}
```

---

## API Endpoints

### POST /api/v1/auth/login
**Purpose:** Authenticate user, return access + refresh tokens

**Request:**
```bash
curl -X POST http://192.168.196.97:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=Test1234!"
```

**Response:**
```json
{
  "access_token": "eyJhbGci...EHDvfkWd...",
  "refresh_token": "eyJzdWIi...t-FSqjXQ...",
  "token_type": "bearer"
}
```

**Token Payload (Decoded):**
```json
{
  "sub": "testuser",
  "user_id": 4,
  "token_version": 1,
  "jti": "EHDvfkWdSagWFvqyBY3ZYD-u7SVNsFBnp8Acyec-7MU",
  "exp": 1774931426,
  "type": "access"
}
```

### GET /api/v1/auth/me
**Purpose:** Get current user info (protected endpoint)

**Request:**
```bash
curl -X GET http://192.168.196.97:8001/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": 4,
  "username": "testuser",
  "email": "testuser@example.com",
  "full_name": "Test User",
  "role": "user",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-03-31T02:47:16.447525Z"
}
```

### POST /api/v1/auth/refresh
**Purpose:** Exchange refresh token for new access token

**Request:**
```bash
curl -X POST "http://192.168.196.97:8001/api/v1/auth/refresh?refresh_token=YOUR_REFRESH_TOKEN"
```

**Response:**
```json
{
  "access_token": "eyJhbGci...NEW_TOKEN...",
  "refresh_token": "eyJzdWIi...NEW_REFRESH...",
  "token_type": "bearer"
}
```

**What Happens:**
- ✅ Old refresh token revoked (`is_revoked=true`)
- ✅ New refresh token issued and stored
- ✅ New access token issued
- ✅ Token rotation security implemented

### POST /api/v1/auth/logout
**Purpose:** Logout from current device

**Request:**
```bash
curl -X POST "http://192.168.196.97:8001/api/v1/auth/logout?refresh_token=YOUR_REFRESH_TOKEN" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "message": "Successfully logged out",
  "username": "testuser"
}
```

**What Happens:**
- ✅ Access token added to blacklist (via `jti`)
- ✅ Refresh token revoked in database
- ✅ Both tokens immediately invalid

### POST /api/v1/auth/logout-all
**Purpose:** Logout from ALL devices (global invalidation)

**Request:**
```bash
curl -X POST http://192.168.196.97:8001/api/v1/auth/logout-all \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "message": "Successfully logged out from all devices",
  "username": "testuser"
}
```

**What Happens:**
- ✅ `token_version` incremented (e.g., 0 → 1)
- ✅ ALL existing tokens (all devices) instantly invalid
- ✅ All refresh tokens revoked in database
- ✅ User must re-login on ALL devices

---

## JWT Token Expiry Monitoring Endpoints (USMA-91)

### GET /api/v1/auth/sessions
**Purpose:** View your own active sessions with expiry times

**Request:**
```bash
curl -X GET http://192.168.196.97:8001/api/v1/auth/sessions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "user_id": 4,
  "username": "testjwt",
  "token_version": 1,
  "total_sessions": 5,
  "active_sessions": 2,
  "sessions": [
    {
      "id": 5,
      "created_at": "2026-03-31T03:59:39.650596+00:00",
      "expires_at": "2026-04-07T03:59:39.821546+00:00",
      "is_revoked": false,
      "revoked_at": null,
      "device_info": "curl/8.5.0",
      "is_expired": false,
      "time_until_expiry_hours": 167.98,
      "status": "active"
    },
    {
      "id": 4,
      "created_at": "2026-03-31T03:30:26.304117+00:00",
      "expires_at": "2026-04-07T03:30:26.469621+00:00",
      "is_revoked": true,
      "revoked_at": "2026-03-31T03:31:10.417983+00:00",
      "device_info": "curl/8.5.0",
      "is_expired": false,
      "time_until_expiry_hours": 167.5,
      "status": "revoked"
    }
  ]
}
```

**Use Cases:**
- Users can see all their active login sessions
- Shows which devices are logged in
- Track when tokens expire
- Monitor for suspicious sessions

---

### GET /api/v1/auth/admin/token-stats
**Purpose:** Get global JWT token statistics (admin only)

**Request:**
```bash
curl -X GET http://192.168.196.97:8001/api/v1/auth/admin/token-stats \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Response:**
```json
{
  "timestamp": "2026-03-31T04:04:00.517643+00:00",
  "refresh_tokens": {
    "total": 6,
    "active": 3,
    "revoked": 3,
    "expired": 0
  },
  "blacklist": {
    "total": 1,
    "still_valid": 1,
    "expired": 0
  },
  "users": {
    "total": 2,
    "with_active_sessions": 1
  },
  "revocation_reasons": {
    "logout": 1
  }
}
```

**Use Cases:**
- Monitor overall system security health
- Track active user sessions
- Identify token usage patterns
- Plan blacklist cleanup

---

### GET /api/v1/auth/admin/sessions
**Purpose:** View all sessions across all users (admin only)

**Request:**
```bash
# View all sessions
curl -X GET http://192.168.196.97:8001/api/v1/auth/admin/sessions \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# Filter by user
curl -X GET "http://192.168.196.97:8001/api/v1/auth/admin/sessions?user_id=4" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# Active sessions only
curl -X GET "http://192.168.196.97:8001/api/v1/auth/admin/sessions?active_only=true" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Response:**
```json
{
  "total_sessions": 6,
  "filters": {
    "user_id": null,
    "active_only": false
  },
  "sessions": [
    {
      "id": 6,
      "user_id": 4,
      "username": "testjwt",
      "email": "testjwt@example.com",
      "created_at": "2026-03-31T04:02:04.516138+00:00",
      "expires_at": "2026-04-07T04:02:04.690833+00:00",
      "is_revoked": false,
      "revoked_at": null,
      "device_info": "curl/8.5.0",
      "is_expired": false,
      "time_until_expiry_hours": 167.98,
      "status": "active"
    }
  ]
}
```

**Query Parameters:**
- `user_id` (optional): Filter sessions by specific user
- `active_only` (optional): Show only active sessions (not revoked or expired)

**Use Cases:**
- Admin dashboard showing all active users
- Security audit of login sessions
- Investigate suspicious activity
- Support: "Which devices is this user logged in on?"

---

### DELETE /api/v1/auth/admin/sessions/{token_id}
**Purpose:** Revoke a specific session (admin only)

**Request:**
```bash
curl -X DELETE http://192.168.196.97:8001/api/v1/auth/admin/sessions/5 \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

**Response (Success):**
```json
{
  "message": "Session 5 revoked successfully",
  "token_id": 5,
  "user_id": 4,
  "username": "testjwt"
}
```

**Response (Already Revoked):**
```json
{
  "detail": "Session 5 is already revoked"
}
```

**Response (Not Found):**
```json
{
  "detail": "Session 999 not found"
}
```

**Use Cases:**
- Force logout specific user session
- Security response: revoke suspicious session
- Support: "My phone was stolen, can you logout that device?"
- Admin: Kill all sessions for compromised account

---

## Testing Guide

### Complete Test Flow

```bash
# ==========================================
# Test 1: Login
# ==========================================
curl -X POST http://192.168.196.97:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testjwt&password=Test1234!"

# Save tokens:
ACCESS_TOKEN="eyJhbGci..."
REFRESH_TOKEN="eyJzdWIi..."

# ==========================================
# Test 2: Access Protected Endpoint
# ==========================================
curl -X GET http://192.168.196.97:8001/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# ✅ Expected: User data returned
# {"id": 4, "username": "testjwt", "email": "testjwt@example.com", ...}

# ==========================================
# Test 3: View My Sessions (USMA-91)
# ==========================================
curl -X GET http://192.168.196.97:8001/api/v1/auth/sessions \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# ✅ Expected: List of all sessions with expiry times
# {"total_sessions": 5, "active_sessions": 2, "sessions": [...]}

# ==========================================
# Test 4: Refresh Token
# ==========================================
curl -X POST "http://192.168.196.97:8001/api/v1/auth/refresh?refresh_token=$REFRESH_TOKEN"

# ✅ Expected: New token pair returned
# {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}

# Save new tokens:
NEW_ACCESS="eyJhbGci..."
NEW_REFRESH="eyJzdWIi..."

# ==========================================
# Test 5: Old Refresh Token Revoked
# ==========================================
curl -X POST "http://192.168.196.97:8001/api/v1/auth/refresh?refresh_token=$REFRESH_TOKEN"

# ✅ Expected: Error "Refresh token has been revoked"
# {"detail": "Refresh token has been revoked"}

# ==========================================
# Test 6: Logout (Blacklist)
# ==========================================
curl -X POST "http://192.168.196.97:8001/api/v1/auth/logout?refresh_token=$NEW_REFRESH" \
  -H "Authorization: Bearer $NEW_ACCESS"

# ✅ Expected: Success message
# {"message": "Successfully logged out", "username": "testjwt"}

# ==========================================
# Test 7: Blacklisted Token Rejected
# ==========================================
curl -X GET http://192.168.196.97:8001/api/v1/auth/me \
  -H "Authorization: Bearer $NEW_ACCESS"

# ✅ Expected: Error "Token has been revoked"
# {"detail": "Token has been revoked"}

# ==========================================
# Test 8: Login Again + Logout All
# ==========================================
curl -X POST http://192.168.196.97:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testjwt&password=Test1234!"

FRESH_ACCESS="eyJhbGci..."

curl -X POST http://192.168.196.97:8001/api/v1/auth/logout-all \
  -H "Authorization: Bearer $FRESH_ACCESS"

# ✅ Expected: Success message
# {"message": "Successfully logged out from all devices", "username": "testjwt"}

# ==========================================
# Test 9: Token Version Mismatch
# ==========================================
curl -X GET http://192.168.196.97:8001/api/v1/auth/me \
  -H "Authorization: Bearer $FRESH_ACCESS"

# ✅ Expected: Error "Token has been invalidated"
# {"detail": "Token has been invalidated. Please login again."}

# ==========================================
# Test 10: Admin Monitoring (USMA-91)
# ==========================================
# First, make user superuser:
docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "UPDATE users SET is_superuser = true WHERE username = 'testjwt';"

# Login as admin
curl -X POST http://192.168.196.97:8001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testjwt&password=Test1234!"

ADMIN_TOKEN="eyJhbGci..."

# Test 10a: Token Statistics
curl -X GET http://192.168.196.97:8001/api/v1/auth/admin/token-stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# ✅ Expected: Global statistics
# {"refresh_tokens": {"total": 6, "active": 3, ...}, "blacklist": {...}, ...}

# Test 10b: View All Sessions
curl -X GET http://192.168.196.97:8001/api/v1/auth/admin/sessions \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# ✅ Expected: All sessions across all users
# {"total_sessions": 6, "sessions": [...]}

# Test 10c: Filter Active Sessions
curl -X GET "http://192.168.196.97:8001/api/v1/auth/admin/sessions?active_only=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# ✅ Expected: Only active sessions
# {"total_sessions": 3, "sessions": [...]}

# Test 10d: Revoke Session
curl -X DELETE http://192.168.196.97:8001/api/v1/auth/admin/sessions/3 \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# ✅ Expected: Success or "already revoked"
# {"message": "Session 3 revoked successfully", ...}

# ==========================================
# Test 11: Database Verification
# ==========================================
# Check refresh_tokens table
docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "SELECT id, user_id, is_revoked, expires_at FROM refresh_tokens ORDER BY id;"

# Check revoked_tokens table
docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "SELECT id, LEFT(jti, 30) as jti, token_type, reason FROM revoked_tokens ORDER BY id;"

# Check token_version
docker exec usm-autoimmune-postgres psql -U usm_db_admin -d usm_autoimmune_registry \
  -c "SELECT id, username, token_version FROM users WHERE username='testjwt';"
```

### Expected Database State

**After Complete Test:**

```sql
-- refresh_tokens
id  user_id  is_revoked  expires_at
1   4        true        2026-04-07 02:56:01  -- First login, rotated
2   4        false       2026-04-07 03:10:21  -- After refresh, revoked on logout
3   4        false       2026-04-07 03:15:42  -- After re-login

-- revoked_tokens
id  jti                              token_type  reason
1   EHDvfkWdSagWFvqyBY3ZYD-u7SVNsF  access      logout

-- users
id  username  token_version
4   testjwt   1  -- Incremented from 0 by logout-all
```

---

## Security Best Practices

### 1. Token Expiry Times

```python
# app/core/config.py
ACCESS_TOKEN_EXPIRE_MINUTES = 60    # Short-lived (1 hour)
REFRESH_TOKEN_EXPIRE_DAYS = 7       # Medium-lived (7 days)
```

**Rationale:**
- **Access tokens (60 min)**: Short expiry limits damage from stolen tokens
- **Refresh tokens (7 days)**: Long enough for good UX, short enough for security

**Tune Based on Risk:**
- **High security**: Access 15 min, Refresh 1 day
- **Balanced** (current): Access 60 min, Refresh 7 days
- **Convenience**: Access 240 min, Refresh 30 days (⚠️ not recommended)

### 2. Refresh Token Rotation

**Always rotate refresh tokens:**
```python
# On /refresh endpoint
db_token.is_revoked = True  # Revoke old
new_token = create_new()     # Issue new
```

**Why:**
- Prevents refresh token replay attacks
- Limits damage if refresh token stolen
- Industry standard (OAuth 2.0 best practice)

### 3. Token Blacklist Cleanup

**Problem:** `revoked_tokens` table grows forever

**Solution:** Periodic cleanup of expired tokens

```sql
-- Run daily via cron
DELETE FROM revoked_tokens 
WHERE expires_at < NOW() - INTERVAL '7 days';
```

**Implementation (Future):**
```python
# app/tasks/cleanup.py (add in Sprint 3)
@scheduler.scheduled_job('cron', hour=3)  # Run at 3 AM daily
def cleanup_expired_tokens():
    db.query(RevokedToken).filter(
        RevokedToken.expires_at < datetime.now(timezone.utc) - timedelta(days=7)
    ).delete()
    db.commit()
```

### 4. Rate Limiting

**Protect refresh endpoint from abuse:**
```python
# Add rate limiting (Sprint 3)
from slowapi import Limiter

@router.post("/refresh")
@limiter.limit("10/minute")  # Max 10 refreshes per minute
async def refresh_access_token(...):
    ...
```

### 5. Secure Token Storage (Frontend)

**DO NOT store in localStorage** (XSS vulnerable):
```javascript
// ❌ BAD
localStorage.setItem('access_token', token);
```

**Store in httpOnly cookie** (XSS safe):
```python
# Backend sets cookie
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,  # Not accessible via JavaScript
    secure=True,    # HTTPS only
    samesite='lax'  # CSRF protection
)
```

---

## Troubleshooting

### Issue 1: "Token has been revoked" on valid token

**Symptoms:**
- User can't access endpoints
- Token was just issued
- Blacklist shows unexpected entry

**Diagnosis:**
```sql
SELECT * FROM revoked_tokens WHERE jti = 'TOKEN_JTI';
```

**Causes:**
1. **Logout called twice** (frontend bug)
2. **Token reused after logout** (frontend not deleting token)
3. **Cookie/localStorage mix** (frontend storing both)

**Solution:**
```javascript
// Frontend: Clear tokens immediately after logout
async function logout() {
    await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${accessToken}`}
    });
    
    // Clear immediately
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
}
```

### Issue 2: "Token has been invalidated" after logout-all

**Symptoms:**
- All users logged out unexpectedly
- Token version mismatch error

**Diagnosis:**
```sql
SELECT username, token_version FROM users ORDER BY token_version DESC;
```

**Causes:**
1. **Admin called /logout-all** (intended behavior)
2. **Password change** (should increment version)
3. **Security response** (account compromise)

**Solution:**
- ✅ This is **expected behavior**
- User must re-login to get new tokens with correct version
- Document this UX flow for users

### Issue 3: Refresh token rotation breaks mobile app

**Symptoms:**
- Mobile app keeps tokens after refresh
- Old refresh token attempted, fails
- User forced to re-login

**Cause:**
Mobile app stores tokens but doesn't update after refresh.

**Solution:**
```javascript
// Mobile app: Update stored tokens after refresh
async function refreshToken(oldRefreshToken) {
    const response = await fetch(`/api/v1/auth/refresh?refresh_token=${oldRefreshToken}`);
    const { access_token, refresh_token } = await response.json();
    
    // IMPORTANT: Update stored refresh token
    await SecureStore.setItemAsync('access_token', access_token);
    await SecureStore.setItemAsync('refresh_token', refresh_token);  // ← Critical!
    
    return access_token;
}
```

### Issue 4: Slow API responses after blacklist

**Symptoms:**
- API latency increased
- Database query time high on protected endpoints

**Diagnosis:**
```sql
EXPLAIN ANALYZE 
SELECT * FROM revoked_tokens WHERE jti = 'TOKEN_JTI';
```

**Causes:**
1. **Missing index** on `jti` column
2. **Large blacklist** table (millions of entries)
3. **No cleanup** of expired tokens

**Solutions:**

**Short-term (Index):**
```sql
CREATE INDEX idx_revoked_jti ON revoked_tokens(jti);
-- Already exists from migration
```

**Medium-term (Cleanup):**
```sql
-- Run weekly
DELETE FROM revoked_tokens WHERE expires_at < NOW();
```

**Long-term (Redis Cache):**
```python
# Sprint 3: Cache blacklist in Redis for faster lookup
import redis
redis_client = redis.Redis()

# Check cache first
if redis_client.sismember('blacklist', jti):
    raise HTTPException(401, "Token revoked")

# Fallback to database
db_check = db.query(RevokedToken).filter(...).first()
```

### Issue 5: Token expiry mismatch (timezone issues)

**Symptoms:**
- `TypeError: can't compare offset-naive and offset-aware datetimes`
- Tokens expired too early/late

**Cause:**
Mixing `datetime.utcnow()` (naive) with database `TIMESTAMPTZ` (aware).

**Solution:**
✅ **Always use timezone-aware datetimes:**
```python
from datetime import datetime, timezone

# ✅ CORRECT
expires_at = datetime.now(timezone.utc) + timedelta(days=7)

# ❌ WRONG
expires_at = datetime.utcnow() + timedelta(days=7)
```

**Verify in code:**
```bash
grep -r "datetime.utcnow()" app/
# Should return 0 results (all replaced with datetime.now(timezone.utc))
```

---

## Summary

### Tickets Completed

- ✅ **USMA-88**: Refresh token mechanism (7-day sessions, database tracking, rotation)
- ✅ **USMA-89**: Token revocation on logout (blacklist implementation)
- ✅ **USMA-90**: Token versioning (global invalidation via version increment)
- ✅ **USMA-91**: JWT token expiry monitoring (4 new endpoints - all tested and working)

### Key Metrics

**Database Migrations:**
- Migration `9a2e81360415`:  refresh_tokens table + users.token_version
- Migration `cd668b5a9c62`: revoked_tokens blacklist table

**Security Improvements:**
- ✅ Tokens can be revoked immediately (blacklist)
- ✅ Sessions extend to 7 days (refresh tokens)
- ✅ Global logout from all devices (token versioning)
- ✅ Token rotation prevents replay attacks
- ✅ Audit trail of all sessions and revocations
- ✅ Real-time monitoring of active sessions
- ✅ Admin tools for security management

**API Endpoints Implemented:**
- ✅ POST /login - Create tokens with JTI and version
- ✅ POST /refresh - Rotate tokens securely
- ✅ POST /logout - Blacklist access token + revoke refresh token
- ✅ POST /logout-all - Global invalidation via version increment
- ✅ GET /sessions - User view of their active sessions
- ✅ GET /admin/token-stats - Global token statistics
- ✅ GET /admin/sessions - View all sessions with filters
- ✅ DELETE /admin/sessions/{id} - Admin revoke session

**Testing Coverage:**
- ✅ Login returns both tokens with JTI
- ✅ Refresh endpoint exchanges tokens (rotation verified)
- ✅ Logout blacklists access token (immediate revocation)
- ✅ Logout-all increments token_version (global invalidation)
- ✅ Blacklisted tokens rejected (security enforced)
- ✅ Version mismatch tokens rejected (version check working)
- ✅ User sessions endpoint shows expiry tracking
- ✅ Admin stats endpoint provides system-wide metrics
- ✅ Admin sessions endpoint filters correctly
- ✅ Admin revoke session endpoint with proper error handling

### Next Steps (Sprint 2 Continuation)

**JWT Security: COMPLETE ✅**
All 4 JWT security tickets finished and tested:
- USMA-88, 89, 90, 91 ✅

**Option A: Streamlit UI (USMA-92-95)**
- USMA-92: Login interface (Streamlit/React)
- USMA-93: User profile dashboard
- USMA-94: Role-based UI navigation
- USMA-95: Session management UI
- Timeline: 8-12 hours (Days 4-5)

**Option B: ETL/EDA Pipeline (USMA-22-33, 61-63)**
Recommended next priority - core business value:
- USMA-61: Secure data upload interface
- USMA-62: Dataset preview interface
- USMA-22: Missing value handling
- USMA-23: Outlier detection
- USMA-24: Categorical encoding
- USMA-25: Data standardization/normalization
- USMA-26: Automated preprocessing
- USMA-33: EDA platform
- Timeline: 2-3 weeks (Sprint 3)

**Option C: ML Baseline Models (USMA-81-82)**
- USMA-81: XGBoost classifier
- USMA-82: CatBoost for categorical features
- Timeline: 1 week (Sprint 4)

**Recommendation:** 
Move to **Option B (ETL/EDA)** to build core data processing capabilities. UI can be added later once backend has real data to display. This provides maximum business value and impressive demos with actual autoimmune disease data analysis.

---

**Document Version:** 1.1  
**Last Updated:** March 31, 2026 (USMA-91 Complete)  
**Status:** All JWT Security Features Complete ✅  
**Next Review:** Sprint 3 Planning (ETL/EDA Pipeline)
