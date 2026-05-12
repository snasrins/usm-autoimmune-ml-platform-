# 🚀 RTX6000 Deployment - Quick Reference

## Your Server Info

- **Server:** mtuser1@100.122.108.118  
- **Password:** mezPez19!@  
- **Target Port:** 80 (nginx entry point)  

---

## Quick Deploy (5 Steps)

### 1️⃣ SSH into RTX6000

```bash
ssh mtuser1@100.122.108.118
# Password: mezPez19!@
```

### 2️⃣ Clone/Update Repository

**First time:**
```bash
cd /home/mtuser1
git clone https://github.com/snasrins/usm-autoimmune-ml-platform-.git
cd usm-autoimmune-ml-platform-
```

**Or update existing:**
```bash
cd /home/mtuser1/usm-autoimmune-ml-platform-
git pull origin main
```

### 3️⃣ Configure Environment

```bash
cp .env.example .env
nano .env
```

**Minimum required variables:**
```bash
POSTGRES_PASSWORD=<strong_password>
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
MINIO_ROOT_PASSWORD=<strong_password>
```

**Save and secure:**
```bash
chmod 600 .env
```

### 4️⃣ Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

**Or manually:**
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 5️⃣ Get IP for Reverse Proxy

The deploy script will show you, or manually:

```bash
# Get server IP
ip addr show | grep "inet " | grep -v "127.0.0.1" | head -n 1 | awk '{print $2}' | cut -d/ -f1
```

**Give to your senior:**
```
IP:Port = <SERVER_IP>:80
Example: 100.122.108.118:80
```

---

## Verification

```bash
# Check containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Test health
curl http://localhost/api/health
# Should return: {"status":"healthy"}

# Test frontend
curl http://localhost/

# View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

---

## Common Commands

```bash
# View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Stop services
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Update and redeploy
git pull origin main
./deploy.sh
```

---

## Troubleshooting

### Backend not starting:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend
```

### Database connection failed:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs postgres
# Check DATABASE_URL in .env
```

### Port conflict:
```bash
sudo netstat -tulpn | grep :80
# Change port in docker-compose.prod.yml if needed
```

---

## What Your Senior Needs

After deployment succeeds, tell them:

```
✅ Application deployed on RTX6000
Server IP:Port: <YOUR_IP>:80
Health Check: http://<YOUR_IP>:80/api/health

Services Running:
- Backend (FastAPI) - internal only
- Frontend (React) - internal only  
- PostgreSQL - internal only
- MinIO - internal only
- Nginx - port 80 (entry point)
```

---

## Architecture

```
Internet → Reverse Proxy VM → RTX6000:80 (nginx) → Backend/Frontend
```

Your app exposes **only port 80** (nginx). The reverse proxy will route public traffic to it.

---

## Next Steps

1. ✅ Deploy on RTX6000 (you do this)
2. ⏳ Senior configures reverse proxy
3. ⏳ DNS points to reverse proxy
4. ⏳ SSL/TLS configured
5. ✅ Public URL live! (e.g., https://autoimmune.yourdomain.com)

---

Need help? See full guide: [DEPLOYMENT_GUIDE_RTX6000.md](./DEPLOYMENT_GUIDE_RTX6000.md)
