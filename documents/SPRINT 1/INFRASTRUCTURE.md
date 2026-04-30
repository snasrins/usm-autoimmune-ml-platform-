# Infrastructure Setup Documentation

**Data Engineer:** Syarifah Fajriyah  
**Project:** USM Autoimmune ML Platform  
**Phase 1 - Weeks 1-3:** Infrastructure Provisioning & Environment Configuration  
**Status:** ✅ COMPLETE

---

## Table of Contents

1. [Server Specifications](#server-specifications)
2. [GPU Configuration](#gpu-configuration)
3. [Docker Environment](#docker-environment)
4. [Network Configuration](#network-configuration)
5. [Database Setup](#database-setup)
6. [Python Environment](#python-environment)
7. [Verification Tests](#verification-tests)

---

## Server Specifications

### Hardware
- **Server Type:** Ubuntu 24.04.2 LTS GPU Server
- **GPU:** NVIDIA RTX 3090 (24GB VRAM)
- **CPU:** Multi-core processor
- **RAM:** Sufficient for ML workloads
- **Storage:** 36.19GB system drive (76.6% utilized)
- **Network:** ZeroTier private network + public IP

### Access Information
- **Hostname:** `server-gpu`
- **ZeroTier IP:** `172.24.175.24`
- **Public IP:** `10.40.90.42`
- **SSH User:** `mtuser2`
- **Project Directory:** `/home/mtuser2/usm-autoimmune-ml-platform`

---

## GPU Configuration

### NVIDIA Driver & CUDA

**Installed Versions:**
- **CUDA Version:** 12.1.0
- **Driver Version:** Latest for Ubuntu 24.04
- **Container Toolkit:** nvidia-container-toolkit

**Verification Command:**
```bash
nvidia-smi
```

**Expected Output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.1   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce RTX 3090  On   | 00000000:01:00.0  Off |                  N/A |
| 30%   45C    P8    25W / 350W |      0MiB / 24576MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

### CUDA Libraries Installed

**Deep Learning Frameworks:**
```bash
# PyTorch with CUDA support
torch==2.1.0+cu121
torchvision==0.16.0+cu121
torchaudio==2.1.0+cu121

# TensorFlow (if needed for future models)
# tensorflow-gpu==2.15.0
```

**Verification:**
```bash
python3 test_gpu.py
```

**test_gpu.py script:**
```python
import torch
import sys

print("=" * 60)
print("GPU ENVIRONMENT TEST")
print("=" * 60)

# Check CUDA availability
print(f"\nCUDA Available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    print(f"Current GPU: {torch.cuda.current_device()}")
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # Test GPU computation
    print("\nTesting GPU computation...")
    x = torch.rand(1000, 1000).cuda()
    y = torch.rand(1000, 1000).cuda()
    z = torch.matmul(x, y)
    print(f"✓ Matrix multiplication on GPU successful")
    print(f"Result shape: {z.shape}")
else:
    print("ERROR: CUDA not available!")
    sys.exit(1)

print("\n" + "=" * 60)
print("GPU ENVIRONMENT: READY ✓")
print("=" * 60)
```

### NVIDIA Docker Configuration

**Installation Steps:**
```bash
# 1. Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 2. Restart Docker
sudo systemctl restart docker

# 3. Test GPU access in container
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**Docker Compose GPU Configuration:**
```yaml
# In docker-compose.yml
services:
  api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## Docker Environment

### Docker Installation

**Version Information:**
```bash
docker --version
# Expected: Docker version 24.0.x or higher

docker compose version
# Expected: Docker Compose version v2.x.x
```

**Installation Commands:**
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose plugin
sudo apt-get install docker-compose-plugin
```

### Container Architecture

**Services Defined in docker-compose.yml:**

1. **usm-autoimmune-api** (FastAPI + ML)
   - Base Image: `nvidia/cuda:12.1.0-devel-ubuntu22.04`
   - Python: 3.10
   - Port: 8000
   - GPU: Enabled
   - Volume: `/app` mounted

2. **usm-autoimmune-postgres** (PostgreSQL 15)
   - Base Image: `postgres:15-alpine`
   - Port: 5432
   - Volume: Persistent data storage
   - Database: `usm_autoimmune_registry`

**Container Communication:**
- Internal Docker network: `usm-network`
- API → Database: via service name `postgres`
- External access: via ZeroTier IP

### Dockerfile Configuration

**Key Components:**
```dockerfile
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Python 3.10 installation
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
WORKDIR /app
COPY ./app /app

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Build & Run:**
```bash
# Build containers
docker compose build

# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f api
docker compose logs -f postgres

# Restart services
docker compose restart api

# Stop services
docker compose down
```

---

## Network Configuration

### ZeroTier Private Network

**Network Details:**
- **Network ID:** `d5e5fb653720782f`
- **Network Type:** Private
- **Security:** Encrypted peer-to-peer
- **Authorization:** Manual device approval required

**Installation on Server:**
```bash
# Install ZeroTier client
curl -s https://install.zerotier.com | sudo bash

# Join network
sudo zerotier-cli join d5e5fb653720782f

# Check status
sudo zerotier-cli status
sudo zerotier-cli listnetworks

# Get assigned IP
ip addr show | grep zt
```

**Client Access:**
1. Install ZeroTier on your machine
2. Join network `d5e5fb653720782f`
3. Authorize device in ZeroTier Central (my.zerotier.com)
4. Access API at `http://172.24.175.24:8000`

### Firewall Configuration

**Required Ports:**
- **8000:** FastAPI application (HTTP)
- **5432:** PostgreSQL (internal only, not exposed)
- **22:** SSH access
- **9993:** ZeroTier (UDP)

**UFW Configuration (if enabled):**
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp
sudo ufw allow 9993/udp
sudo ufw enable
```

---

## Database Setup

### PostgreSQL 15 Configuration

**Container Configuration:**
```yaml
postgres:
  image: postgres:15-alpine
  container_name: usm-autoimmune-postgres
  environment:
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: usm_autoimmune_registry
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./init-db:/docker-entrypoint-initdb.d
  ports:
    - "5432:5432"
  restart: unless-stopped
```

**Database Credentials (.env file):**
```bash
POSTGRES_USER=usm_admin
POSTGRES_PASSWORD=<secure_password>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=usm_autoimmune_registry
```

**Initialization Scripts:**
Location: `init-db/` directory
- `001_create_flexible_schema.sql` - Creates 8 tables
- `002_fix_patients_table.sql` - Adds missing columns
- `003_seed_sle_lab_tests.sql` - Seeds 49 standard lab tests
- `004_make_test_date_nullable.sql` - Makes test_date nullable

**Database Schema (9 tables):**
1. `patients` - Anonymous patient demographics
2. `diagnoses` - Disease diagnoses per patient
3. `lab_test_definitions` - Lab test catalog
4. `lab_results_flexible` - Individual lab results
5. `lab_results_batch` - Batch lab results (JSONB)
6. `disease_specific_data` - Disease-specific JSONB data
7. `uploaded_files` - File upload tracking
8. `data_ingestion_audit` - Import audit trail
9. `users` - System users (authentication)

**Access Database:**
```bash
# From host (via Docker exec)
docker exec -it usm-autoimmune-postgres psql -U usm_admin -d usm_autoimmune_registry

# Common queries
\dt                              # List tables
\d patients                      # Describe patients table
SELECT COUNT(*) FROM patients;   # Count patients
```

---

## Python Environment

### Virtual Environment Setup

**Location:** `/opt/venv` (inside container)

**Creation:**
```bash
# On host (if needed)
python3 -m venv venv
source venv/bin/activate

# Inside container (automatic)
ENV PATH="/opt/venv/bin:$PATH"
```

### Dependencies (requirements.txt)

**Core Framework:**
```
fastapi==0.108.0
uvicorn[standard]==0.25.0
pydantic==2.5.3
pydantic-settings==2.1.0
```

**Database & ORM:**
```
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1
```

**Authentication:**
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

**Data Processing:**
```
pandas==2.1.4
numpy==1.26.3
openpyxl==3.1.2
xlrd==2.0.1
python-dateutil==2.8.2
```

**ML Libraries (for future use):**
```
torch==2.1.0+cu121
torchvision==0.16.0+cu121
scikit-learn==1.3.2
xgboost==2.0.3
```

**NLP (for text processing):**
```
spacy==3.7.2
scispacy==0.5.3
en-core-sci-sm @ https://s3-us-west-2.amazonaws.com/ai2-s3-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz
```

**Utilities:**
```
python-dotenv==1.0.0
pytest==7.4.3
httpx==0.26.0
```

**Installation:**
```bash
# Inside container (automatic via Dockerfile)
pip install -r requirements.txt

# Download spaCy models
python -m spacy download en_core_web_sm
```

---

## Verification Tests

### 1. GPU Access Test
```bash
# Test NVIDIA driver
nvidia-smi

# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Test PyTorch GPU
python3 test_gpu.py
```

**Expected:** All tests pass, GPU detected

### 2. Database Connection Test
```bash
# Check container is running
docker compose ps postgres

# Test connection
docker exec -it usm-autoimmune-postgres psql -U usm_admin -d usm_autoimmune_registry -c "SELECT version();"
```

**Expected:** PostgreSQL version displayed

### 3. API Health Check
```bash
# Check container is running
docker compose ps api

# Test API endpoint
curl http://172.24.175.24:8000/health

# Test Swagger UI (in browser)
http://172.24.175.24:8000/docs
```

**Expected Output:**
```json
{
  "status": "healthy",
  "database": "connected",
  "gpu": "available",
  "version": "1.0.0"
}
```

### 4. Network Connectivity Test
```bash
# Test ZeroTier
sudo zerotier-cli listnetworks

# Test from client machine
ping 172.24.175.24
curl http://172.24.175.24:8000/health
```

**Expected:** Network reachable, API responds

### 5. Container Logs Check
```bash
# Check for errors in API logs
docker compose logs api | grep ERROR

# Check for errors in database logs
docker compose logs postgres | grep ERROR

# Watch live logs
docker compose logs -f --tail=50
```

**Expected:** "Application startup complete", no errors

---

## Troubleshooting Guide

### GPU Not Detected

**Problem:** CUDA not available in container

**Solutions:**
```bash
# 1. Verify NVIDIA driver on host
nvidia-smi

# 2. Reinstall NVIDIA Container Toolkit
sudo apt-get install --reinstall nvidia-container-toolkit
sudo systemctl restart docker

# 3. Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 4. Verify docker-compose.yml has GPU config
grep -A 5 "resources:" docker-compose.yml
```

### Database Connection Failed

**Problem:** API can't connect to PostgreSQL

**Solutions:**
```bash
# 1. Check postgres container is running
docker compose ps postgres

# 2. Check database logs
docker compose logs postgres

# 3. Verify credentials in .env
cat .env | grep POSTGRES

# 4. Test connection from API container
docker exec -it usm-autoimmune-api psql -h postgres -U usm_admin -d usm_autoimmune_registry
```

### API Container Crashes

**Problem:** Container exits immediately

**Solutions:**
```bash
# 1. Check logs for error details
docker compose logs api

# 2. Check Python dependencies
docker compose exec api pip list

# 3. Test manually
docker compose exec api python -c "import app.main"

# 4. Rebuild container
docker compose down
docker compose build --no-cache api
docker compose up -d
```

### ZeroTier Connection Issues

**Problem:** Can't access API from client

**Solutions:**
```bash
# 1. Check ZeroTier status on server
sudo zerotier-cli status
sudo zerotier-cli listnetworks

# 2. Check device is authorized in ZeroTier Central
# Visit: https://my.zerotier.com

# 3. Verify IP assignment
ip addr show | grep zt

# 4. Test local access first
curl http://localhost:8000/health
curl http://172.24.175.24:8000/health
```

---

## Performance Monitoring

### Container Resource Usage
```bash
# Real-time stats
docker stats

# Specific container
docker stats usm-autoimmune-api
```

### GPU Monitoring
```bash
# Continuous monitoring
watch -n 1 nvidia-smi

# GPU utilization graph (if nvidia-smi-pmon available)
nvidia-smi dmon -s u
```

### Database Performance
```bash
# Active connections
docker exec -it usm-autoimmune-postgres psql -U usm_admin -d usm_autoimmune_registry -c "SELECT count(*) FROM pg_stat_activity;"

# Database size
docker exec -it usm-autoimmune-postgres psql -U usm_admin -d usm_autoimmune_registry -c "SELECT pg_size_pretty(pg_database_size('usm_autoimmune_registry'));"
```

---

## Maintenance Tasks

### Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker compose pull
docker compose up -d

# Update Python packages
docker compose exec api pip install --upgrade -r requirements.txt
```

### Backup Procedures
```bash
# Backup database
docker exec usm-autoimmune-postgres pg_dump -U usm_admin usm_autoimmune_registry > backup_$(date +%Y%m%d).sql

# Backup uploaded files (if stored locally)
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz data/uploads/

# Restore database
cat backup_20260316.sql | docker exec -i usm-autoimmune-postgres psql -U usm_admin usm_autoimmune_registry
```

### Log Rotation
```bash
# Docker log size limit (in docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Environment Variables Reference

**Complete .env file template:**
```bash
# Database Configuration
POSTGRES_USER=usm_admin
POSTGRES_PASSWORD=<generate_secure_password>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=usm_autoimmune_registry

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=USM Autoimmune ML Platform
BACKEND_CORS_ORIGINS=["http://172.24.175.24:8000","http://localhost:8000"]

# Security
SECRET_KEY=<generate_with_openssl_rand_-hex_32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Network
ZEROTIER_IP=172.24.175.24

# ML Configuration (for future use)
MODEL_PATH=/app/models
BATCH_SIZE=32
MAX_WORKERS=4
```

**Generate secure secrets:**
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate POSTGRES_PASSWORD
openssl rand -base64 32
```

---

## Infrastructure Status: ✅ PRODUCTION READY

**Verified Components:**
- ✅ GPU server with CUDA 12.1
- ✅ Docker environment with GPU support
- ✅ PostgreSQL 15 database
- ✅ Python 3.10 virtual environment
- ✅ ZeroTier private network
- ✅ FastAPI application
- ✅ All dependencies installed
- ✅ Health checks passing

**Next Phase:** Data Pipeline Development (Completed in Sprint 1)

---

**Last Updated:** March 16, 2026  
**Maintained By:** Syarifah Fajriyah (Data Engineer)
