# USM Autoimmune ML Platform - Setup Instructions

**Data Engineer:** Syarifah Fajriyah  
**Project:** Hybrid ML Platform for Autoimmune Disease Registry  
**Sprint 1:** Environment Setup (UPB-21)

---

##  Quick Start Checklist

### Step 1: Configure Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and fill in all values:
# - ZEROTIER_IP (your ZeroTier network IP)
# - Database passwords
# - JWT secret key (generate with: openssl rand -hex 32)
nano .env
```

### Step 2: Install Dependencies on GPU Server

**On the Ubuntu GPU server (mtuser2@172.24.175.24):**

```bash
# Navigate to project directory
cd ~/usm-autoimmune-ml-platform

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install all dependencies
pip install -r requirements.txt

# Download spaCy models
python -m spacy download en_core_web_sm
pip install https://s3-us-west-2.amazonaws.com/ai2-s3-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz

# Test GPU access
python test_gpu.py
```

### Step 3: Install Docker & Docker Compose

**On the GPU server:**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit (for GPU access in containers)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Install Docker Compose
sudo apt-get install docker-compose-plugin
docker compose version
```

### Step 4: Configure ZeroTier Network

```bash
# Install ZeroTier client
curl -s https://install.zerotier.com | sudo bash

# Join your ZeroTier network
sudo zerotier-cli join d5e5fb653720782f

# Check your ZeroTier IP
ip addr show | grep zt

# Update .env with the ZeroTier IP
```

**In ZeroTier Central (my.zerotier.com):**
- Authorize the new device
- Note the assigned IP address
- Update `ZEROTIER_IP` in `.env` file

### Step 5: Update docker-compose.yml

Edit `docker-compose.yml` and replace all instances of `${ZEROTIER_IP}` binding if needed:

```yaml
ports:
  - "172.24.50.103:5432:5432"  # Your actual ZeroTier IP
```

### Step 6: Launch the Platform

```bash
# Create required directories
mkdir -p data/uploads data/processed data/raw models logs init-db

# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f

# Test PostgreSQL connection
docker compose exec postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "SELECT version();"
```

### Step 7: Verify the Setup

```bash
# Check API health endpoint (from within ZeroTier network)
curl http://172.24.50.103:8000/health

# Check PgAdmin (open in browser via ZeroTier)
http://172.24.50.103:5050

# Check database is ready
docker compose exec postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\dt"
```

---

## 🔒 Security Checklist

- [ ] `.env` file created and **NOT** committed to git
- [ ] Strong passwords set for all services (min 16 characters)
- [ ] JWT secret key generated with `openssl rand -hex 32`
- [ ] All services bind to ZeroTier IP only (not 0.0.0.0)
- [ ] ZeroTier network is PRIVATE (not public)
- [ ] Only authorized devices can join ZeroTier network
- [ ] PostgreSQL encryption at rest configured
- [ ] Ethics clearance certificate received before processing real data

---

## 📋 Testing GPU Access from Docker

```bash
# Enter the FastAPI container
docker compose exec fastapi bash

# Run GPU test
python test_gpu.py

# Expected output:
# ✓ PyTorch CUDA available: True
# ✓ GPU Device: NVIDIA GeForce RTX 3090
# ✓ GPU Memory: 24.00 GB
```

---

## 🛠️ Troubleshooting

### GPU not detected in Docker

```bash
# Restart Docker with NVIDIA runtime
sudo systemctl restart docker

# Verify NVIDIA runtime is available
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Cannot connect to PostgreSQL

```bash
# Check if PostgreSQL is running
docker compose logs postgres

# Verify port binding
netstat -tulpn | grep 5432

# Test connection from host
psql -h 172.24.50.103 -U usm_db_admin -d usm_autoimmune_registry
```

### ZeroTier connection issues

```bash
# Check ZeroTier status
sudo zerotier-cli status

# Check network membership
sudo zerotier-cli listnetworks

# Restart ZeroTier service
sudo systemctl restart zerotier-one
```

---

## 📦 Next Steps (Sprint 1 Continuation)

After environment setup is complete, proceed to:

1. **UPB-06:** Design and deploy all 6 PostgreSQL tables
2. **UPB-17/18:** Implement JWT authentication + RBAC
3. **UPB-01/02:** Build file upload and validation pipeline

---

## 📞 Support Contacts

- **Project Manager:** Alia
- **Solution Architect:** Veytri Yogan
- **ML Engineer:** Iznie Humaiera (ml_experiments table)
- **Data Engineer:** Syarifah Fajriyah (you!)

**ZeroTier Network ID:** [TO BE FILLED]  
**NMRR Registration:** [PENDING ETHICS CLEARANCE]
