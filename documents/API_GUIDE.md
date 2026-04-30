# USM Autoimmune ML Platform - API Guide

## 🚀 Quick Start

### 1. Access the Platform

- **API Documentation**: http://172.24.175.24:8000/docs
- **Health Check**: http://172.24.175.24:8000/health
- **pgAdmin**: http://172.24.175.24:5050

### 2. Default Credentials

```
Admin User:
  Username: admin
  Password: admin123
  
Doctor User:
  Username: doctor1
  Password: doctor123
  
Regular User:
  Username: user1
  Password: user123

⚠️  CHANGE THESE PASSWORDS IMMEDIATELY IN PRODUCTION!
```

## 📚 API Endpoints

### Authentication (`/api/v1/auth`)

#### Register New User
```bash
curl -X POST "http://172.24.175.24:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "newuser",
    "password": "securepass123",
    "full_name": "New User",
    "role": "user"
  }'
```

#### Login
```bash
curl -X POST "http://172.24.175.24:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User Info
```bash
curl -X GET "http://172.24.175.24:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### ML Prediction (`/api/v1/predict`)

#### Single Prediction
```bash
curl -X POST "http://172.24.175.24:8000/api/v1/predict/predict" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "P001",
    "features": {
      "feature_0": 0.5,
      "feature_1": 0.3,
      "feature_2": 0.8,
      "feature_3": 0.2,
      "feature_4": 0.6,
      "feature_5": 0.4,
      "feature_6": 0.7,
      "feature_7": 0.1,
      "feature_8": 0.9,
      "feature_9": 0.3,
      "feature_10": 0.5,
      "feature_11": 0.4,
      "feature_12": 0.6,
      "feature_13": 0.2,
      "feature_14": 0.8,
      "feature_15": 0.3,
      "feature_16": 0.7,
      "feature_17": 0.1,
      "feature_18": 0.5,
      "feature_19": 0.4
    },
    "model_type": "autoimmune_classifier"
  }'
```

Response:
```json
{
  "patient_id": "P001",
  "prediction": "SLE",
  "confidence": 0.8542,
  "risk_score": 85.42,
  "probabilities": {
    "SLE": 0.8542,
    "Rheumatoid Arthritis": 0.0823,
    "Sjogren's": 0.0412,
    "Scleroderma": 0.0156,
    "Mixed CTD": 0.0067
  },
  "model_version": "1.0.0",
  "predicted_at": "2026-03-12T06:30:00.123456",
  "gpu_used": true,
  "inference_time_ms": 2.34
}
```

#### Batch Prediction
```bash
curl -X POST "http://172.24.175.24:8000/api/v1/predict/predict/batch" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "predictions": [
      {
        "patient_id": "P001",
        "features": {...}
      },
      {
        "patient_id": "P002",
        "features": {...}
      }
    ]
  }'
```

#### Get GPU Info
```bash
curl -X GET "http://172.24.175.24:8000/api/v1/predict/gpu-info" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### File Upload (`/api/v1/upload`)

#### Upload Single File
```bash
curl -X POST "http://172.24.175.24:8000/api/v1/upload/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@patient_data.csv"
```

#### Upload Multiple Files
```bash
curl -X POST "http://172.24.175.24:8000/api/v1/upload/upload/batch" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "files=@file1.csv" \
  -F "files=@file2.xlsx"
```

#### List Uploaded Files
```bash
curl -X GET "http://172.24.175.24:8000/api/v1/upload/uploads" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Administration (`/api/v1/admin`)

**Note: Admin endpoints require superuser privileges**

#### List All Users
```bash
curl -X GET "http://172.24.175.24:8000/api/v1/admin/users" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### Get System Info
```bash
curl -X GET "http://172.24.175.24:8000/api/v1/admin/system/info" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### Get Platform Statistics
```bash
curl -X GET "http://172.24.175.24:8000/api/v1/admin/stats" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 🐍 Python Client Example

```python
import requests
import json

# Base URL
BASE_URL = "http://172.24.175.24:8000"

# Login
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]

# Set authorization header
headers = {"Authorization": f"Bearer {token}"}

# Make a prediction
prediction_data = {
    "patient_id": "P001",
    "features": {f"feature_{i}": i * 0.1 for i in range(20)},
    "model_type": "autoimmune_classifier"
}

response = requests.post(
    f"{BASE_URL}/api/v1/predict/predict",
    headers=headers,
    json=prediction_data
)

result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']:.4f}")
print(f"GPU Used: {result['gpu_used']}")
print(f"Inference Time: {result['inference_time_ms']:.2f}ms")
```

## 🧪 Testing

### Initialize Database
```bash
# On the server
cd ~/usm-autoimmune-ml-platform
sudo docker exec -it usm-autoimmune-api python /app/scripts/init_db.py
```

### Test ML Inference
```bash
# On the server
sudo docker exec -it usm-autoimmune-api python /app/scripts/test_ml_inference.py
```

### Test GPU Access
```bash
sudo docker exec -it usm-autoimmune-api nvidia-smi
```

## 📊 Monitoring

### Check Container Logs
```bash
# All containers
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f fastapi
sudo docker compose logs -f postgres
sudo docker compose logs -f pgadmin
```

### Container Status
```bash
sudo docker compose ps
```

### Resource Usage
```bash
# System resources
sudo docker stats

# GPU monitoring
watch -n 1 nvidia-smi
```

## 🔒 Security Best Practices

1. **Change Default Passwords**: Immediately change all default passwords
2. **Use HTTPS**: Set up SSL/TLS certificates for production
3. **Environment Variables**: Never commit `.env` file to version control
4. **Token Expiry**: Access tokens expire after 60 minutes by default
5. **Network Security**: Only accessible through ZeroTier VPN (172.24.175.24)

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
sudo docker compose logs fastapi

# Rebuild from scratch
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up -d
```

### Database Connection Issues
```bash
# Check if postgres is healthy
sudo docker compose ps

# Check database logs
sudo docker compose logs postgres
```

### GPU Not Available
```bash
# Verify NVIDIA Container Toolkit
sudo docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check Docker daemon.json
cat /etc/docker/daemon.json
```

## 📞 Support

For issues or questions:
- Data Engineer: Syarifah Fajriyah
- ML Engineer: Iznie Humaiera
- Client: Universiti Sains Malaysia (USM)
