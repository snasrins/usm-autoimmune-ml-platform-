# EDA Backend - Quick Deployment Checklist

**Run this when GPU is back and ready to deploy**

---

## ✅ Pre-Deployment

### 1. Verify Code on Windows
```powershell
# Check all files exist
Get-ChildItem -Path "C:\Users\Syarifah\usm-autoimmune-ml-platform\app\models\dataset.py"
Get-ChildItem -Path "C:\Users\Syarifah\usm-autoimmune-ml-platform\app\services\preprocessing.py"
Get-ChildItem -Path "C:\Users\Syarifah\usm-autoimmune-ml-platform\app\services\eda_analyzer.py"
Get-ChildItem -Path "C:\Users\Syarifah\usm-autoimmune-ml-platform\app\api\endpoints\eda.py"
```

### 2. Check for Errors Locally
```powershell
# Check Python syntax (if Python installed)
python -m py_compile app/models/dataset.py
python -m py_compile app/services/preprocessing.py
python -m py_compile app/services/eda_analyzer.py
python -m py_compile app/api/endpoints/eda.py
```

---

## 🚀 Deployment Steps

### Step 1: Upload Files to Server
```powershell
# Option A: WinSCP (GUI) - Recommended
# 1. Open WinSCP
# 2. Connect to shaggy@192.168.196.97
# 3. Navigate to /home/shaggy/usm-autoimmune-ml-platform/
# 4. Upload these files:
#    - app/models/dataset.py
#    - app/services/preprocessing.py
#    - app/services/eda_analyzer.py
#    - app/api/endpoints/eda.py
#    - app/main.py (updated)
#    - app/models/__init__.py (updated)

# Option B: Git (if code is committed)
# On Windows:
cd C:\Users\Syarifah\usm-autoimmune-ml-platform
git add .
git commit -m "Add EDA platform backend - Sprint 3 complete"
git push origin main

# On Server:
ssh shaggy@192.168.196.97
cd usm-autoimmune-ml-platform
git pull origin main
```

---

### Step 2: Create Upload Directory
```bash
# SSH to server
ssh shaggy@192.168.196.97

# Create directory for EDA uploads
sudo mkdir -p /data/eda_uploads
sudo chown shaggy:shaggy /data/eda_uploads
sudo chmod 755 /data/eda_uploads

# Verify
ls -la /data/
```

---

### Step 3: Create Database Migration
```bash
# Inside Docker container
docker exec -it usm-autoimmune-fastapi alembic revision --autogenerate -m "add_eda_tables_datasets_and_reports"

# Check the generated migration file
docker exec -it usm-autoimmune-fastapi ls -la alembic/versions/

# Expected: New file like "abc123_add_eda_tables_datasets_and_reports.py"
```

---

### Step 4: Review Migration (Important!)
```bash
# View the migration file
docker exec -it usm-autoimmune-fastapi cat alembic/versions/<migration_file>.py

# Check for:
# ✅ CREATE TABLE datasets (...)
# ✅ CREATE TABLE eda_reports (...)
# ✅ CREATE INDEX statements
# ✅ Foreign key constraints
```

---

### Step 5: Apply Migration
```bash
# Run migration
docker exec -it usm-autoimmune-fastapi alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade 9a2e81360415 -> abc123, add_eda_tables_datasets_and_reports
```

---

### Step 6: Verify Tables Created
```bash
# Connect to database
docker exec -it usm-autoimmune-postgres psql -U shaggy -d usm_autoimmune_ml

# Check tables exist
\dt

# Expected output should include:
#  public | datasets    | table | shaggy
#  public | eda_reports | table | shaggy

# Describe datasets table
\d datasets

# Describe eda_reports table
\d eda_reports

# Exit
\q
```

---

### Step 7: Restart FastAPI
```bash
# Restart container to load new code
docker compose restart fastapi

# Wait 10 seconds
sleep 10

# Check container is healthy
docker ps | grep fastapi

# Check logs for errors
docker logs usm-autoimmune-fastapi --tail 50
```

---

### Step 8: Test API Docs
```bash
# Test FastAPI is running
curl http://192.168.196.97:8001/health

# Expected: {"status": "healthy"}

# Open API docs in browser (on Windows)
start http://192.168.196.97:8001/docs

# or via curl
curl http://192.168.196.97:8001/docs
```

**Check for EDA endpoints in the docs:**
- Should see "EDA & Preprocessing" section
- 15 endpoints should be visible

---

### Step 9: Get Authentication Token
```bash
# Login to get token
curl -X POST "http://192.168.196.97:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testjwt&password=Test1234!"

# Save the access_token from response
export TOKEN="<paste_your_access_token_here>"
```

---

### Step 10: Test Upload Endpoint
```bash
# Create test CSV file
cat > /tmp/test_eda.csv << EOF
age,gender,disease_activity
35,Female,12
42,Male,18
28,Female,8
EOF

# Test upload
curl -X POST "http://192.168.196.97:8001/api/v1/eda/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_eda.csv" \
  -F "name=Test EDA Dataset" \
  -F "description=Testing EDA upload"

# Expected: 201 response with dataset details
```

---

### Step 11: Test Preview Endpoint
```bash
# Use dataset_id from upload response (e.g., 1)
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/1/preview?rows=3" \
  -H "Authorization: Bearer $TOKEN"

# Expected: JSON with preview data
```

---

### Step 12: Test Quality Analysis
```bash
curl -X GET "http://192.168.196.97:8001/api/v1/eda/datasets/1/quality" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Comprehensive quality report
```

---

## ✅ Deployment Success Checklist

- [ ] Files uploaded to server
- [ ] Upload directory created (/data/eda_uploads)
- [ ] Migration created successfully
- [ ] Migration applied (tables created)
- [ ] Tables visible in database (\dt)
- [ ] FastAPI restarted without errors
- [ ] API docs accessible
- [ ] EDA endpoints visible in docs
- [ ] Authentication works (token received)
- [ ] Upload endpoint works (201 response)
- [ ] Preview endpoint works (data returned)
- [ ] Quality analysis works (report generated)

**All checked? Backend is LIVE!** 🎉

---

## 🐛 Troubleshooting

### Error: ModuleNotFoundError
```bash
# Check files exist in container
docker exec -it usm-autoimmune-fastapi ls -la app/models/dataset.py
docker exec -it usm-autoimmune-fastapi ls -la app/services/preprocessing.py
docker exec -it usm-autoimmune-fastapi ls -la app/api/endpoints/eda.py

# If missing, re-upload files
```

### Error: "Table already exists"
```bash
# Check if tables exist
docker exec -it usm-autoimmune-postgres psql -U shaggy -d usm_autoimmune_ml -c "\dt"

# If tables exist but migration failed, mark as complete
docker exec -it usm-autoimmune-fastapi alembic stamp head
```

### Error: 404 Not Found on /eda endpoints
```bash
# Check router is included in main.py
docker exec -it usm-autoimmune-fastapi grep "eda.router" app/main.py

# Expected: app.include_router(eda.router, prefix=...)

# If missing, main.py wasn't uploaded correctly
```

### Error: Permission denied on /data/eda_uploads
```bash
# Fix permissions
sudo chown -R shaggy:shaggy /data/eda_uploads
sudo chmod -R 755 /data/eda_uploads
```

---

## 📝 Post-Deployment

### Run Full Test Suite
See **EDA_TESTING_GUIDE.md** for 13 comprehensive tests

### Update Frontend CORS (if needed)
If frontend can't connect:
```python
# In app/main.py
allowed_origins = [
    f"http://{settings.ZEROTIER_IP}:8000",
    "http://localhost:3000",  # Add this for local React dev
    "http://192.168.196.97:3000",  # Add this if frontend on server
]
```

---

**Ready? Start with Step 1!** 🚀
