# Deployment Instructions

## 📦 Files to Upload to Server

You need to upload the following directories and files to the server:

```
usm-autoimmune-ml-platform/
├── app/
│   ├── __init__.py
│   ├── main.py (UPDATED)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── predict.py
│   │       ├── upload.py
│   │       └── admin.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── patient.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── prediction.py
│   └── ml/
│       ├── __init__.py
│       ├── inference.py
│       └── preprocessing.py
├── scripts/
│   ├── init_db.py (NEW)
│   └── test_ml_inference.py (NEW)
├── requirements.txt (UPDATED)
└── API_GUIDE.md (NEW)
```

## 🚀 Step-by-Step Deployment

### Option 1: Using WinSCP or FileZilla (Recommended)

1. **Connect to server**:
   - Host: 172.24.175.24
   - Username: mtuser2
   - Protocol: SFTP
   
2. **Navigate to**: `/home/mtuser2/usm-autoimmune-ml-platform/`

3. **Upload the following folders** (overwrite existing):
   - `app/` (entire folder - includes all new code)
   - `scripts/` (updated with new scripts)
   
4. **Upload files**:
   - `requirements.txt` (updated)
   - `API_GUIDE.md` (new)

### Option 2: Using tar Archive

**On your local machine (PowerShell):**

```powershell
# Create archive of app directory
cd c:\Users\Syarifah\usm-autoimmune-ml-platform
tar -czf app-update.tar.gz app/ scripts/ requirements.txt API_GUIDE.md

# Now use WinSCP or another tool to upload app-update.tar.gz
```

**On the server:**

```bash
cd ~/usm-autoimmune-ml-platform
tar -xzf app-update.tar.gz
rm app-update.tar.gz
```

### Option 3: Copy-Paste Individual Files

If you can only use terminal, create files one by one using `nano` or `vim`.

## 🔧 After Upload - Deployment Steps

**On the server, run these commands:**

```bash
# 1. Navigate to project directory
cd ~/usm-autoimmune-ml-platform

# 2. Stop running containers
sudo docker compose down

# 3. Rebuild with updated code
sudo docker compose build --no-cache

# 4. Start containers
sudo docker compose up -d

# 5. Wait for containers to be healthy
sleep 15
sudo docker compose ps

# 6. Initialize database and create users
sudo docker exec -it usm-autoimmune-api python /app/scripts/init_db.py

# 7. Test ML inference
sudo docker exec -it usm-autoimmune-api python /app/scripts/test_ml_inference.py

# 8. Check API health
curl http://172.24.175.24:8000/health

# 9. Check logs
sudo docker compose logs -f fastapi
```

## ✅ Verification

### 1. Check Container Status
```bash
sudo docker compose ps
```

All containers should show status "Up" and fastapi should be "(healthy)".

### 2. Test Health Endpoint
```bash
curl http://172.24.175.24:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 3090"
  ...
}
```

### 3. Access API Documentation
Open in browser: http://172.24.175.24:8000/docs

You should see all endpoints:
- Authentication
- ML Prediction  
- Data Ingestion
- Administration

### 4. Test Login
```bash
curl -X POST "http://172.24.175.24:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Should return access_token and refresh_token.

### 5. Test GPU Inference

```bash
# Get token first
TOKEN=$(curl -X POST "http://172.24.175.24:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Make prediction
curl -X POST "http://172.24.175.24:8000/api/v1/predict/predict" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "TEST001",
    "features": {
      "feature_0": 0.5, "feature_1": 0.3, "feature_2": 0.8, "feature_3": 0.2,
      "feature_4": 0.6, "feature_5": 0.4, "feature_6": 0.7, "feature_7": 0.1,
      "feature_8": 0.9, "feature_9": 0.3, "feature_10": 0.5, "feature_11": 0.4,
      "feature_12": 0.6, "feature_13": 0.2, "feature_14": 0.8, "feature_15": 0.3,
      "feature_16": 0.7, "feature_17": 0.1, "feature_18": 0.5, "feature_19": 0.4
    }
  }'
```

Should return prediction with GPU usage confirmed.

## 🐛 Troubleshooting

### Import Errors
```bash
# Check if all modules are in place
sudo docker exec -it usm-autoimmune-api ls -R /app/app/

# Should show:
# /app/app/api
# /app/app/core
# /app/app/ml
# /app/app/models
# /app/app/schemas
```

### Database Not Initialized
```bash
# Manually run init script
sudo docker exec -it usm-autoimmune-api python /app/scripts/init_db.py
```

### Container Keeps Restarting
```bash
# Check logs for errors
sudo docker compose logs fastapi --tail=100

# Common issues:
# - Missing dependencies (rebuild with updated requirements.txt)
# - Import errors (check file structure)
# - Database connection failed (check postgres health)
```

### Can't Connect to API
```bash
# Check if port is listening
sudo netstat -tlnp | grep 8000

# Check firewall (if needed)
sudo ufw status

# Test from server itself
curl http://localhost:8000/health
curl http://172.24.175.24:8000/health
```

## 📝 Post-Deployment Checklist

- [ ] All containers running and healthy
- [ ] Database initialized with admin user
- [ ] API documentation accessible
- [ ] Health endpoint returns GPU info
- [ ] Login works and returns tokens
- [ ] ML prediction endpoint works
- [ ] GPU inference confirmed (gpu_used: true)
- [ ] File upload endpoint accessible
- [ ] Admin endpoints require superuser
- [ ] Default passwords changed (PRODUCTION ONLY)

## 🎉 Success!

Once all checks pass, your ML platform is fully operational!

Access the interactive API docs at: **http://172.24.175.24:8000/docs**

Default credentials:
- Admin: admin / admin123
- Doctor: doctor1 / doctor123
- User: user1 / user123

**⚠️ Remember to change default passwords before production use!**
