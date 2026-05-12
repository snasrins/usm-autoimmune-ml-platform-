# ✅ RTX6000 Deployment Checklist

Use this checklist to track your deployment progress.

---

## Pre-Deployment (On Your Local Machine)

- [ ] All new deployment files committed and pushed to GitHub:
  ```bash
  cd C:\Users\Syarifah\usm-autoimmune-ml-platform
  git add .
  git commit -m "Add production deployment configuration for RTX6000"
  git push origin main
  ```

- [ ] You have the RTX6000 server credentials:
  - **Server:** mtuser1@100.122.108.118
  - **Password:** mezPez19!@

- [ ] You've read [QUICK_DEPLOY_RTX6000.md](./QUICK_DEPLOY_RTX6000.md)

---

## On RTX6000 Server

### Step 1: Connect

- [ ] SSH into RTX6000 server:
  ```bash
  ssh mtuser1@100.122.108.118
  # Password: mezPez19!@
  ```

### Step 2: Get Code

- [ ] Clone or update repository:
  ```bash
  # First time:
  cd /home/mtuser1
  git clone https://github.com/snasrins/usm-autoimmune-ml-platform-.git
  cd usm-autoimmune-ml-platform-
  
  # Or update:
  cd /home/mtuser1/usm-autoimmune-ml-platform-
  git pull origin main
  ```

### Step 3: Configure Environment

- [ ] Create .env file:
  ```bash
  cp .env.example .env
  ```

- [ ] Generate JWT secret:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
  Copy the output.

- [ ] Edit .env with production values:
  ```bash
  nano .env
  ```

- [ ] Set these required variables:
  - [ ] `POSTGRES_PASSWORD` = (strong password)
  - [ ] `JWT_SECRET_KEY` = (generated secret from above)
  - [ ] `MINIO_ROOT_PASSWORD` = (strong password)
  - [ ] `MINIO_ACCESS_KEY` = (same as MINIO_ROOT_USER)
  - [ ] `MINIO_SECRET_KEY` = (same as MINIO_ROOT_PASSWORD)
  - [ ] `DATABASE_URL` = postgresql://usm_db_admin:(POSTGRES_PASSWORD)@postgres:5432/usm_autoimmune_registry

- [ ] Save and secure .env:
  ```bash
  # Press Ctrl+X, then Y, then Enter to save in nano
  chmod 600 .env
  ```

### Step 4: Deploy

- [ ] Make deploy script executable:
  ```bash
  chmod +x deploy.sh
  ```

- [ ] Run deployment:
  ```bash
  ./deploy.sh
  ```

- [ ] Wait for deployment to complete (should take 5-10 minutes for first build)

### Step 5: Verify

- [ ] All containers are running:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
  ```
  Should show all services as "Up".

- [ ] Backend health check passes:
  ```bash
  curl http://localhost/api/health
  ```
  Should return: `{"status":"healthy"}`

- [ ] Frontend loads:
  ```bash
  curl http://localhost/
  ```
  Should return HTML.

- [ ] Check logs for any errors:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=50
  ```

### Step 6: Get IP for Reverse Proxy

- [ ] Get server IP:
  ```bash
  ip addr show | grep "inet " | grep -v "127.0.0.1" | head -n 1 | awk '{print $2}' | cut -d/ -f1
  ```
  Write it down: ___________________

- [ ] Test from another machine (optional but recommended):
  ```bash
  # From your local machine
  curl http://<SERVER_IP>/api/health
  ```

- [ ] Format for senior: `<SERVER_IP>:80`
  Example: `100.122.108.118:80`

---

## After Deployment

### Tell Your Senior

- [ ] Send them this information:

```
✅ USM Autoimmune ML Platform deployed on RTX6000

Server IP:Port: <YOUR_IP>:80
Health Check: http://<YOUR_IP>:80/api/health
Frontend: http://<YOUR_IP>:80/

Services:
- Nginx (entry point) on port 80
- Backend (FastAPI) - internal
- Frontend (React) - internal
- PostgreSQL - internal
- MinIO - internal

Ready for reverse proxy configuration.
```

### Documentation for Senior

- [ ] Share these links with your senior (if they need technical details):
  - The Aras deployment guide (that you shared with me)
  - [DEPLOYMENT_GUIDE_RTX6000.md](./DEPLOYMENT_GUIDE_RTX6000.md) (your specific setup)

---

## Common Issues & Solutions

### Issue: Port 80 already in use

```bash
# Check what's using port 80
sudo netstat -tulpn | grep :80

# Stop the conflicting service or use a different port
# To use different port, edit docker-compose.prod.yml:
nano docker-compose.prod.yml
# Change nginx ports from "80:80" to "8080:80" (or any available port)
# Then tell your senior to use <IP>:8080 instead
```

### Issue: Backend won't start

```bash
# Check backend logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs fastapi

# Common causes:
# - Database connection failed (check DATABASE_URL in .env)
# - Missing environment variables (check .env has all required vars)
# - MinIO connection failed (check MINIO_* vars in .env)
```

### Issue: Database connection refused

```bash
# Check if postgres is running
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps postgres

# Check postgres logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs postgres

# Verify DATABASE_URL format:
# postgresql://usm_db_admin:<POSTGRES_PASSWORD>@postgres:5432/usm_autoimmune_registry
```

### Issue: MinIO not accessible

```bash
# Check MinIO logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs minio

# Verify credentials match:
# MINIO_ROOT_USER = MINIO_ACCESS_KEY
# MINIO_ROOT_PASSWORD = MINIO_SECRET_KEY
```

---

## Quick Commands Reference

```bash
# View logs (all services)
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# View logs (specific service)
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f fastapi

# Restart all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Stop all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Check container status
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Check resource usage
docker stats

# Update and redeploy
git pull origin main
./deploy.sh
```

---

## Next Steps After Your Senior Configures Reverse Proxy

1. ⏳ Senior configures reverse proxy on `web.mtailabs.ai` (or your equivalent)
2. ⏳ DNS points to reverse proxy VM (e.g., `autoimmune.yourdomain.com`)
3. ⏳ SSL/TLS configured via Certbot
4. ✅ Public URL is live!
5. ✅ Test the public URL
6. ✅ Celebrate! 🎉

---

## Save This Information

Once deployment is successful, save:

- [ ] Server IP: ___________________
- [ ] Port: 80
- [ ] .env file location: `/home/mtuser1/usm-autoimmune-ml-platform-/.env`
- [ ] Project location: `/home/mtuser1/usm-autoimmune-ml-platform-/`
- [ ] Date deployed: ___________________

---

**Good luck with your deployment! 🚀**

If you encounter any issues, check the logs first:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```
