# Backend + Database Integration Overview
**Date:** April 2, 2026  
**Purpose:** Verify Sign Up flow end-to-end connectivity

---

## 📊 System Architecture Map

```
Frontend (localhost:3000)
    ↓ HTTP POST
API Proxy (Vite)
    ↓ Forward to
Backend (192.168.196.97:8001)
    ↓ FastAPI /auth/register
SQLAlchemy ORM
    ↓ INSERT
PostgreSQL Database (192.168.196.97:5433)
    └─ usm_autoimmune_ml.users table
```

---

## 🔍 Component Verification

### 1. Frontend API Call
**File:** `frontend/src/services/api.js`

```javascript
register: async (userData) => {
  const response = await axios.post(`${API_BASE_URL}/auth/register`, userData);
  return response.data;
}
```

**Sends:** JSON payload
```json
{
  "username": "testresearcher",
  "email": "testresearcher@myaria.com",
  "password": "ResearchTest2026!",
  "full_name": "Test Researcher"
}
```

**API_BASE_URL:** `/api/v1` (proxied by Vite to http://192.168.196.97:8001/api/v1)

---

### 2. Backend Endpoint
**File:** `app/api/endpoints/auth.py` (Line 31-62)

```python
@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        role=user_data.role,  # Defaults to "user"
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user
```

**Input Schema:** `UserCreate` (Pydantic)
```python
class UserCreate(UserBase):
    email: EmailStr           # Required, validated email format
    username: str             # Required
    full_name: Optional[str]  # Optional
    role: Optional[str]       # Optional, defaults to "user"
    password: str             # Required
```

**Output Schema:** `UserResponse` (Pydantic)
```python
class UserResponse(UserBase):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
```

---

### 3. Database Model
**File:** `app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user")  # user, doctor, admin
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    token_version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

### 4. PostgreSQL Database Structure

**Connection String:**
```
postgresql://shaggy:shaggy@192.168.196.97:5433/usm_autoimmune_ml
```

**Users Table Schema:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    role VARCHAR DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    token_version INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE UNIQUE INDEX ix_users_email ON users(email);
CREATE UNIQUE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_id ON users(id);
```

**Constraints:**
- ✅ `email` - UNIQUE, NOT NULL
- ✅ `username` - UNIQUE, NOT NULL
- ✅ `hashed_password` - NOT NULL
- ✅ Password is hashed with bcrypt (`$2b$12$...`)

---

## ✅ Connection Verification Script

### Step 1: Check Backend API Health
```bash
# From Windows PowerShell or Git Bash
curl http://192.168.196.97:8001/docs
```
**Expected:** Opens FastAPI Swagger UI documentation

### Step 2: Check Database Connection
```bash
# SSH to server
ssh shaggy@192.168.196.97

# Connect to PostgreSQL
docker exec -it usm-autoimmune-postgres psql -U shaggy -d usm_autoimmune_ml
```

### Step 3: Verify Users Table Exists
```sql
-- Check table structure
\d users

-- Expected output:
--                                      Table "public.users"
--      Column      |            Type             | Collation | Nullable |              Default
-- -----------------+-----------------------------+-----------+----------+-----------------------------------
--  id              | integer                     |           | not null | nextval('users_id_seq'::regclass)
--  email           | character varying           |           | not null |
--  username        | character varying           |           | not null |
--  hashed_password | character varying           |           | not null |
--  full_name       | character varying           |           |          |
--  role            | character varying           |           |          | 'user'::character varying
--  is_active       | boolean                     |           |          | true
--  is_superuser    | boolean                     |           |          | false
--  token_version   | integer                     |           | not null | 0
--  created_at      | timestamp with time zone    |           |          | now()
--  updated_at      | timestamp with time zone    |           |          |
```

### Step 4: Check Existing Users
```sql
SELECT id, username, email, full_name, role, is_active, is_superuser, created_at
FROM users
ORDER BY created_at DESC;
```

**Current Expected Users:**
```
 id | username  |         email          |   full_name    | role | is_active | is_superuser |        created_at
----+-----------+------------------------+----------------+------+-----------+--------------+---------------------------
  4 | testjwt   | test@jwt.com           | JWT Test User  | user | t         | t            | 2026-03-31 ...
  1 | admin     | admin@myaria.com       | Admin User     | user | t         | f            | ...
```

---

## 🧪 End-to-End Test Flow

### Test 1: Direct Backend API Test (Bypass Frontend)
```bash
# Test registration directly via curl
curl -X POST "http://192.168.196.97:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "curltest",
    "email": "curltest@myaria.com",
    "password": "CurlTest2026!",
    "full_name": "Curl Test User"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": 5,
  "email": "curltest@myaria.com",
  "username": "curltest",
  "full_name": "Curl Test User",
  "role": "user",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-04-02T..."
}
```

**Verify in Database:**
```sql
SELECT * FROM users WHERE username = 'curltest';
```

### Test 2: Frontend Sign Up (Full Flow)
1. **Open:** http://localhost:3000/signup
2. **Fill form:**
   ```
   Full Name: Frontend Test
   Username: frontendtest
   Email: frontendtest@myaria.com
   Password: FrontendTest2026!
   Confirm: FrontendTest2026!
   ☑ Terms
   ```
3. **Submit** → Should redirect to login with success message
4. **Login** with same credentials → Should access dashboard

**Verify in Database:**
```sql
SELECT id, username, email, full_name, 
       LEFT(hashed_password, 10) as password_preview,
       role, is_active, created_at
FROM users
WHERE username = 'frontendtest';
```

**Expected:**
```
 id |   username   |           email             |   full_name    | password_preview | role | is_active |        created_at
----+--------------+-----------------------------+----------------+------------------+------+-----------+---------------------------
  6 | frontendtest | frontendtest@myaria.com     | Frontend Test  | $2b$12$abc...   | user | t         | 2026-04-02 ...
```

---

## 🐛 Troubleshooting Checklist

### Issue: "Network Error" or "Cannot POST"
**Check:**
```bash
# 1. Backend is running
curl http://192.168.196.97:8001/health

# 2. CORS allows localhost:3000
# Check backend logs: docker logs usm-autoimmune-fastapi
```

**Fix:** Add to `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.196.97:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "User with this email or username already exists"
**Check:**
```sql
SELECT username, email FROM users WHERE username = 'testresearcher' OR email = 'testresearcher@myaria.com';
```

**Fix:** Use different username/email OR delete test user:
```sql
DELETE FROM users WHERE username = 'testresearcher';
```

### Issue: "Internal Server Error 500"
**Check Backend Logs:**
```bash
docker logs usm-autoimmune-fastapi --tail 50
```

**Common Causes:**
- Database connection lost
- Missing column in users table
- Password hashing error

### Issue: Database Connection Failed
**Check:**
```bash
# 1. Container running
docker ps | grep usm-autoimmune-postgres

# 2. Port accessible
nc -zv 192.168.196.97 5433

# 3. Credentials correct
psql -h 192.168.196.97 -p 5433 -U shaggy -d usm_autoimmune_ml
```

---

## 📊 Data Flow Validation

### Sign Up Success Flow:
```
1. Frontend sends: {"username": "test", "email": "test@...", "password": "...", "full_name": "..."}
   ↓
2. Vite proxy forwards to: http://192.168.196.97:8001/api/v1/auth/register
   ↓
3. FastAPI receives → Pydantic validates UserCreate schema
   ↓
4. Check duplicate: SELECT * FROM users WHERE email=? OR username=?
   ↓
5. Hash password: bcrypt.hashpw(password, bcrypt.gensalt())
   ↓
6. Insert: INSERT INTO users (email, username, hashed_password, full_name, role) VALUES (...)
   ↓
7. Response: UserResponse with id, email, username, role, is_active, created_at
   ↓
8. Frontend receives 201 → Redirects to /login with success message
   ↓
9. User logs in → JWT tokens issued → Dashboard access
```

### Sign Up Duplicate User Flow:
```
1. Frontend sends duplicate username/email
   ↓
2. Backend checks: existing_user = db.query(User).filter(...)
   ↓
3. Found existing → Raise HTTPException(400, "User with this email or username already exists")
   ↓
4. Frontend catches error → Shows red banner with message
   ↓
5. User corrects and resubmits
```

---

## 🔐 Security Verification

### Password Hashing Check:
```sql
-- Raw passwords should NEVER appear in database
SELECT username, 
       LEFT(hashed_password, 7) as hash_prefix,
       LENGTH(hashed_password) as hash_length
FROM users;
```

**Expected:**
```
 username  | hash_prefix | hash_length
-----------+-------------+-------------
 testjwt   | $2b$12$     | 60
 admin     | $2b$12$     | 60
```

**Hash Format:** `$2b$12$` = bcrypt with cost factor 12

### JWT Token Validation:
After login, tokens should be stored in localStorage and used for authenticated requests.

```javascript
// Check in browser console
localStorage.getItem('access_token')  // Should return JWT token
localStorage.getItem('refresh_token') // Should return JWT token
```

---

## ✅ Ready to Test Checklist

- [ ] Backend running: `http://192.168.196.97:8001/docs` accessible
- [ ] Database running: `docker ps | grep usm-autoimmune-postgres` shows healthy
- [ ] Frontend running: `npm run dev` at http://localhost:3000
- [ ] No errors in: `docker logs usm-autoimmune-fastapi`
- [ ] Users table exists: `\dt users` in psql
- [ ] Test user NOT already registered: Query username/email

**All checked? Proceed to testing!** 🚀

---

## 📝 Quick Verification Commands

```bash
# === ON WINDOWS (PowerShell) ===
# 1. Test backend health
curl http://192.168.196.97:8001/health

# 2. Test registration endpoint directly
curl -X POST "http://192.168.196.97:8001/api/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d '{"username":"quicktest","email":"quicktest@test.com","password":"Test1234!","full_name":"Quick Test"}'

# === ON SERVER (SSH) ===
# 3. Check database
ssh shaggy@192.168.196.97
docker exec -it usm-autoimmune-postgres psql -U shaggy -d usm_autoimmune_ml -c "SELECT COUNT(*) as total_users FROM users;"

# 4. Check backend logs
docker logs usm-autoimmune-fastapi --tail 20
```

---

**Everything linked up? Let's test!** 🎯
