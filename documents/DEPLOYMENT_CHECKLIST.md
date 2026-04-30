# Deployment Checklist - Unstructured Data Pipeline
## When GPU Server is Back Online

**Date Prepared:** March 23, 2026  
**For:** Syarifah Fajriyah (Data Engineer)  
**Status:** BLOCKED - Server unstable (100% packet loss)

---

## ⚠️ Pre-Deployment: Verify Server Stability

```powershell
# Test connectivity
ping 172.24.175.24

# Should show: 0% packet loss, <100ms latency
# If 100% loss or timeouts → DO NOT PROCEED, contact IT admin
```

---

## 📤 STEP 1: Upload Files to Server (WinSCP - 5 minutes)

### 1.1 Connect via WinSCP
- Host: `172.24.175.24`
- Port: `22`
- User: `mtuser2`
- Password: [your password]

### 1.2 Upload These Files
Navigate to `/home/mtuser2/usm-autoimmune-ml-platform/` and upload:

**NEW FILES:**
- `app/services/unstructured_pipeline_service.py` (700 lines)
- `app/api/endpoints/unstructured.py` (500 lines)
- `init-db/02-flexible-schema.sql` (400 lines)

**UPDATED FILES:**
- `app/main.py` (add unstructured router import)
- `requirements.txt` (add minio==7.2.0)

**OPTIONAL (for testing):**
- `test_qwen_gpu.py` (200 lines)

---

## 🔧 STEP 2: SSH into Server (PuTTY - Interactive Session)

### 2.1 Connect via PuTTY
- Host: `172.24.175.24`
- Port: `22`
- User: `mtuser2`

### 2.2 Navigate to Project
```bash
cd /home/mtuser2/usm-autoimmune-ml-platform
pwd
# Should show: /home/mtuser2/usm-autoimmune-ml-platform
```

---

## 📦 STEP 3: Install Python Dependencies (2-3 minutes)

```bash
# Install packages INSIDE Docker container
docker exec usm-autoimmune-api pip install \
  transformers==4.36.2 \
  accelerate==0.25.0 \
  sentencepiece==0.1.99 \
  torchvision==0.16.2 \
  einops==0.7.0 \
  minio==7.2.0 \
  --no-cache-dir
```

### 3.1 Verify Installation
```bash
docker exec usm-autoimmune-api pip list | grep -E "transformers|accelerate|sentencepiece|torchvision|einops|minio"
```

**Expected output:**
```
accelerate      0.25.0
einops          0.7.0
minio           7.2.0
sentencepiece   0.1.99
torchvision     0.16.2
transformers    4.36.2
```

---

## 🧪 STEP 4: Test GPU Memory (3 minutes)

```bash
# Test Qwen models on GPU
python test_qwen_gpu.py
```

**Expected output:**
```
✅ Qwen2-1.5B Embedding: ~3GB VRAM
✅ Qwen2-VL-2B Vision: ~4GB VRAM
✅ Combined: ~7GB VRAM (17GB free)
```

**If CUDA out of memory → Contact ML team (models too large)**

---

## 🗄️ STEP 5: Deploy Database Schema (2 minutes)

```bash
# Deploy flexible schema to PostgreSQL
docker exec -i usm-autoimmune-postgres psql \
  -U usm_db_admin \
  -d usm_autoimmune_registry \
  < init-db/02-flexible-schema.sql
```

### 5.1 Verify Tables Created
```bash
docker exec usm-autoimmune-postgres psql \
  -U usm_db_admin \
  -d usm_autoimmune_registry \
  -c "\dt" | grep -E "dim_|fact_|metadata|validation"
```

**Expected tables:**
- `dim_patients`, `dim_diseases`, `dim_hospitals`, `dim_lab_tests`, `dim_medications`, `dim_time`
- `fact_patient_visits`, `fact_lab_results`, `fact_diagnoses`, `fact_prescriptions`
- `metadata_datasets`, `metadata_columns`
- `validation_queue`, `audit_trail`

---

## 🪣 STEP 6: Setup MinIO Object Storage (5 minutes)

### 6.1 Start MinIO Container
```bash
docker run -d \
  --name usm-autoimmune-minio \
  --network usm-network \
  -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin123" \
  -v minio_data:/data \
  minio/minio server /data --console-address ":9001"
```

### 6.2 Verify MinIO Running
```bash
docker ps | grep minio
# Should show: usm-autoimmune-minio container running
```

### 6.3 Test MinIO API
```bash
curl http://172.24.175.24:9000/minio/health/live
# Should return: 200 OK
```

### 6.4 Access MinIO Console (Browser)
- URL: `http://172.24.175.24:9001`
- User: `minioadmin`
- Password: `minioadmin123`
- You should see MinIO dashboard

---

## ⚙️ STEP 7: Update Environment Variables (2 minutes)

```bash
# Edit .env file
nano .env
```

**Add these lines at the end:**
```bash
# MinIO Configuration
MINIO_ENDPOINT=172.24.175.24:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false
```

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🔄 STEP 8: Restart API Container (1 minute)

```bash
# Restart to load new code
docker restart usm-autoimmune-api

# Wait 10 seconds for startup
sleep 10

# Check logs for errors
docker logs usm-autoimmune-api --tail 30
```

**Expected logs:**
```
INFO: Started server process
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
✅ Created MinIO bucket: usm-raw-unstructured
✅ Created MinIO bucket: usm-processed-unstructured
✅ Created MinIO bucket: usm-failed-processing
```

---

## ✅ STEP 9: Verify API Endpoints (5 minutes)

### 9.1 Test Health Check
```bash
curl http://172.24.175.24:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 3090"
}
```

### 9.2 Check API Documentation
**Open in browser:** `http://172.24.175.24:8000/docs`

**Look for NEW section:** "Unstructured Pipeline"

**New endpoints should appear:**
- `POST /api/v1/unstructured/upload`
- `POST /api/v1/unstructured/ocr/{dataset_id}`
- `POST /api/v1/unstructured/cleaning/{dataset_id}`
- `POST /api/v1/unstructured/features/{dataset_id}`
- `GET /api/v1/validation/pending`
- `GET /api/v1/validation/{validation_id}`
- `POST /api/v1/validation/{validation_id}/approve`
- `POST /api/v1/validation/{validation_id}/reject`

---

## 🧪 STEP 10: Test Pipeline (10 minutes)

### 10.1 Create Test JSON File
```bash
cat > test_data.json << 'EOF'
[
  {
    "patient_name": "Test Patient",
    "diagnosis": "SLE",
    "visit_date": "2026-03-23",
    "lab_wbc": 5.2
  }
]
EOF
```

### 10.2 Test Upload (Requires Auth Token)
```bash
# Get auth token first (replace with your credentials)
TOKEN=$(curl -X POST "http://172.24.175.24:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"your_user","password":"your_pass"}' | jq -r '.access_token')

# Upload test file
curl -X POST "http://172.24.175.24:8000/api/v1/unstructured/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_data.json"
```

**Expected response:**
```json
{
  "success": true,
  "stage": 1,
  "validation_id": 1,
  "message": "File uploaded successfully. Please review extracted columns."
}
```

### 10.3 Get Pending Validations
```bash
curl -X GET "http://172.24.175.24:8000/api/v1/validation/pending" \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✨ SUCCESS CRITERIA

All steps completed successfully if:
- ✅ All 6 Python packages installed
- ✅ GPU test shows ~7GB VRAM usage
- ✅ 12 database tables created
- ✅ MinIO console accessible
- ✅ API health check returns "healthy"
- ✅ 8 new API endpoints visible in /docs
- ✅ Test file upload returns validation_id

---

## 🚨 TROUBLESHOOTING

### Server keeps timing out
```bash
# Check ZeroTier network
zerotier-cli info
zerotier-cli listnetworks
```
→ Contact IT admin (Faiz) to restart physical server

### Docker container not found
```bash
# List all containers
docker ps -a

# Start stopped container
docker start usm-autoimmune-api
```

### CUDA out of memory
```bash
# Check GPU memory
nvidia-smi

# Restart container to clear VRAM
docker restart usm-autoimmune-api
```

### MinIO connection failed
```bash
# Check if MinIO running
docker ps | grep minio

# Restart MinIO
docker restart usm-autoimmune-minio

# Check logs
docker logs usm-autoimmune-minio
```

### Database table already exists
```bash
# Drop and recreate (WARNING: deletes data!)
docker exec usm-autoimmune-postgres psql \
  -U usm_db_admin \
  -d usm_autoimmune_registry \
  -c "DROP TABLE IF EXISTS validation_queue CASCADE;"

# Redeploy schema
docker exec -i usm-autoimmune-postgres psql \
  -U usm_db_admin \
  -d usm_autoimmune_registry \
  < init-db/02-flexible-schema.sql
```

---

## ⏱️ ESTIMATED TIME

- Server stable: 0 minutes (prerequisite)
- File upload (WinSCP): 5 minutes
- SSH connection: 1 minute
- Install dependencies: 3 minutes
- Test GPU: 3 minutes
- Deploy schema: 2 minutes
- Setup MinIO: 5 minutes
- Update .env: 2 minutes
- Restart container: 1 minute
- Verify endpoints: 5 minutes
- Test pipeline: 10 minutes

**Total: ~40 minutes** (if server is stable)

---

## 📋 FILES TO UPLOAD

Check these files exist locally before uploading:
- [ ] `app/services/unstructured_pipeline_service.py`
- [ ] `app/api/endpoints/unstructured.py`
- [ ] `app/main.py`
- [ ] `requirements.txt`
- [ ] `init-db/02-flexible-schema.sql`
- [ ] `test_qwen_gpu.py`

---

**Last Updated:** March 23, 2026, 11:00 PM  
**Status:** Ready to deploy once server is stable  
**Next Action:** Contact IT admin about server instability
