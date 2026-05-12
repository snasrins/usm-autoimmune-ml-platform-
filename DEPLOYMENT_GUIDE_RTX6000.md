# USM Autoimmune ML Platform - RTX6000 Deployment Guide

## Quick Reference

- **Server:** mtuser1@100.122.108.118
- **Password:** mezPez19!@
- **Target Port:** 80 (production nginx)
- **Services:** Backend (FastAPI), Frontend (React), PostgreSQL, MinIO

---

## Pre-Deployment Checklist

- [ ] SSH access to RTX6000 server confirmed
- [ ] Docker and Docker Compose installed on RTX6000
- [ ] Git repository accessible from RTX6000
- [ ] `.env` file configured with production secrets
- [ ] Nginx reverse proxy configured (if using frontend)

---

## Step 1: Connect to RTX6000 Server

```bash
ssh mtuser1@100.122.108.118
# Password: mezPez19!@
```

---

## Step 2: Clone or Update Repository

### If first time deployment:

```bash
cd /home/mtuser1
git clone https://github.com/snasrins/usm-autoimmune-ml-platform-.git
cd usm-autoimmune-ml-platform-
```

### If updating existing deployment:

```bash
cd /home/mtuser1/usm-autoimmune-ml-platform-
git pull origin main
```

---

## Step 3: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit with production values
nano .env
```

### Required Environment Variables:

```bash
# === PostgreSQL ===
POSTGRES_DB=usm_autoimmune_registry
POSTGRES_USER=usm_db_admin
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>

# === JWT Authentication ===
# Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=<GENERATED_SECRET_KEY>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# === MinIO ===
MINIO_ROOT_USER=minio_admin
MINIO_ROOT_PASSWORD=<STRONG_MINIO_PASSWORD>
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=<SAME_AS_MINIO_ROOT_PASSWORD>
MINIO_SECURE=false

# === Database URL ===
DATABASE_URL=postgresql://usm_db_admin:<POSTGRES_PASSWORD>@postgres:5432/usm_autoimmune_registry
```

**Secure the .env file:**

```bash
chmod 600 .env
```

---

## Step 4: Build and Start Services

### Option A: Backend + Database + MinIO Only (No Frontend)

```bash
docker-compose up -d --build
```

This will expose:
- Backend API: Port 8001 (or 8000 internally)
- PostgreSQL: Port 5432 (internal)
- MinIO: Port 9000 (API), Port 9001 (Console)

### Option B: Full Stack with Frontend + Nginx (Recommended)

If you have nginx configured in your docker-compose:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

This will expose:
- Nginx (entry point): Port 80
- Backend API: Internal only
- Frontend: Internal only
- PostgreSQL: Internal only
- MinIO: Internal only

---

## Step 5: Verify Deployment

### Check container status:

```bash
docker-compose ps
```

All containers should show "Up" or "Up (healthy)".

### Test backend health:

```bash
# If backend is directly exposed on port 8001
curl http://localhost:8001/api/health

# If using nginx on port 80
curl http://localhost/api/health
```

Expected response: `{"status":"healthy"}`

### Test frontend (if deployed):

```bash
curl http://localhost/
```

Should return HTML.

### Check logs if something fails:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f minio
```

---

## Step 6: Get IP Address for Reverse Proxy

### Find the server's internal IP:

```bash
# Get all IP addresses
ip addr show

# Or get specific interface (e.g., eth0, ens160, etc.)
ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
```

**Expected output examples:**
- `100.122.108.118` (if this is the internal IP)
- `10.x.x.x` or `192.168.x.x` (if on internal network)

### Determine the port:

- **If using nginx in docker-compose:** Port 80
- **If backend only (no nginx):** Port 8001 (or whatever port is exposed in your docker-compose)

### Information to give to your senior:

**Format:** `<INTERNAL_IP>:<PORT>`

**Examples:**
- Full stack with nginx: `100.122.108.118:80`
- Backend only: `100.122.108.118:8001`

---

## Step 7: Test from Another Machine (Optional)

Before giving the IP to your senior, test if it's accessible:

```bash
# From your local machine or another server
curl http://100.122.108.118:80/api/health

# Or for backend-only deployment
curl http://100.122.108.118:8001/api/health
```

---

## Common Commands

### Update deployment:

```bash
cd /home/mtuser1/usm-autoimmune-ml-platform-
git pull origin main
docker-compose down
docker-compose up -d --build
```

### View logs:

```bash
# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f backend
```

### Restart services:

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
```

### Stop services:

```bash
docker-compose down
```

### Check resource usage:

```bash
docker stats
```

---

## Troubleshooting

### Issue: Backend not starting

```bash
docker-compose logs backend
```

Common causes:
- Database connection failed (check DATABASE_URL in .env)
- Missing environment variables
- Port conflict

### Issue: Database connection refused

```bash
# Check if postgres container is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Verify DATABASE_URL matches POSTGRES_* variables in .env
```

### Issue: MinIO not accessible

```bash
# Check MinIO logs
docker-compose logs minio

# Verify MinIO credentials in .env match
# MINIO_ROOT_USER = MINIO_ACCESS_KEY
# MINIO_ROOT_PASSWORD = MINIO_SECRET_KEY
```

### Issue: Port already in use

```bash
# Check what's using the port
sudo netstat -tulpn | grep :8001

# Change port in docker-compose.yml or stop conflicting service
```

---

## Security Notes

1. **Never commit `.env` to git**
2. **Use strong passwords** for database and MinIO
3. **Restrict port access** - only expose ports needed by reverse proxy
4. **Keep Docker images updated**: `docker-compose pull && docker-compose up -d`
5. **Backup database regularly**:

```bash
docker-compose exec postgres pg_dump -U usm_db_admin usm_autoimmune_registry > backup_$(date +%Y%m%d).sql
```

---

## What to Give Your Senior

After successful deployment, provide:

```
Server: RTX6000 (mtuser1@100.122.108.118)
Application IP:Port: <INTERNAL_IP>:80
Health Check: http://<INTERNAL_IP>:80/api/health
Frontend: http://<INTERNAL_IP>:80/
API Docs: http://<INTERNAL_IP>:80/api/docs

Services Running:
- Backend (FastAPI)
- Frontend (React)
- PostgreSQL (internal)
- MinIO (internal)
```

---

## Next Steps After Deployment

1. Senior configures reverse proxy on `web.mtailabs.ai` (or equivalent)
2. DNS points to reverse proxy VM
3. SSL/TLS configured via Certbot
4. Public URL becomes accessible (e.g., `https://autoimmune.yourdomain.com`)

---

## Quick Deploy Script

Save this as `deploy.sh` on RTX6000:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying USM Autoimmune ML Platform..."

# Pull latest code
git pull origin main

# Build and start services
docker-compose down
docker-compose up -d --build

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Check health
if curl -sf http://localhost:80/api/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs backend --tail=30
    exit 1
fi

echo "✅ Deployment complete!"
docker-compose ps
```

Make it executable:

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## Rollback Script

Save as `rollback.sh`:

```bash
#!/bin/bash
set -e

echo "⏮️  Rolling back to previous commit..."

git checkout HEAD~1
docker-compose down
docker-compose up -d --build

echo "✅ Rolled back to: $(git rev-parse --short HEAD)"
```

---

**Need help?** Check logs first: `docker-compose logs -f`
