# 📦 Deployment Files Created - Summary

I've created a complete deployment setup for your USM Autoimmune ML Platform to deploy on the RTX6000 server following the Aras deployment guide. Here's what's ready:

---

## 📁 Files Created

### 1. **DEPLOYMENT_GUIDE_RTX6000.md** (Comprehensive Guide)
   - Complete step-by-step deployment instructions
   - Troubleshooting section
   - Security best practices
   - Common commands reference

### 2. **QUICK_DEPLOY_RTX6000.md** (Quick Reference)
   - 5-step deployment process
   - Your server credentials (mtuser1@100.122.108.118)
   - Quick commands for common tasks
   - What to tell your senior

### 3. **docker-compose.prod.yml** (Production Configuration)
   - Production overlay for your docker-compose.yml
   - Adds nginx as entry point (port 80)
   - Adds frontend service
   - Configures all services for production (restart policies, no debug mounts)

### 4. **nginx/prod.conf** (Nginx Configuration)
   - Routes `/api/*` → FastAPI backend
   - Routes `/*` → React frontend
   - WebSocket support
   - Gzip compression
   - Security headers
   - Large file upload support (500MB)

### 5. **frontend/Dockerfile.prod** (Frontend Production Build)
   - Multi-stage build (Node builder → nginx:alpine)
   - Optimized ~25MB final image
   - Serves pre-built static files

### 6. **frontend/nginx.conf** (Frontend SPA Config)
   - React Router support (SPA routing)
   - Static asset caching
   - Security headers

### 7. **deploy.sh** (Automated Deployment Script)
   - Pre-flight checks
   - Builds and starts all services
   - Verifies health endpoints
   - Shows you the IP:port to give your senior
   - Color-coded output

---

## 🚀 How to Deploy

### Step 1: SSH to RTX6000

```bash
ssh mtuser1@100.122.108.118
# Password: mezPez19!@
```

### Step 2: Clone Repository (if not already there)

```bash
cd /home/mtuser1
git clone https://github.com/snasrins/usm-autoimmune-ml-platform-.git
cd usm-autoimmune-ml-platform-
```

### Step 3: Configure Environment

```bash
# Copy example
cp .env.example .env

# Edit with production values
nano .env
```

**Required variables:**
- `POSTGRES_PASSWORD` - Strong password for database
- `JWT_SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `MINIO_ROOT_PASSWORD` - Strong password for MinIO

**Secure it:**
```bash
chmod 600 .env
```

### Step 4: Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- ✅ Check prerequisites (Docker, .env file)
- ✅ Pull latest code
- ✅ Build all images
- ✅ Start all services
- ✅ Verify health endpoints
- ✅ Show you the IP:port for reverse proxy

### Step 5: Get IP for Your Senior

The deploy script will show you the IP at the end, or you can manually get it:

```bash
ip addr show | grep "inet " | grep -v "127.0.0.1" | head -n 1 | awk '{print $2}' | cut -d/ -f1
```

**Give to your senior:**
```
IP:Port = <SERVER_IP>:80
Example: 100.122.108.118:80
```

---

## 🏗️ Architecture

```
Internet
   │
   ▼
┌─────────────────────────────────┐
│  Reverse Proxy VM               │  ← Your senior configures this
│  (web.mtailabs.ai or similar)   │
└──────────┬──────────────────────┘
           │ Routes to
           ▼
┌─────────────────────────────────┐
│  RTX6000 Server                 │  ← You deploy here
│  Port 80 (Nginx container)      │
│                                 │
│  Nginx (entry point)            │
│    ├─ /api/* → FastAPI          │
│    └─ /*     → React Frontend   │
│                                 │
│  + PostgreSQL (internal)        │
│  + MinIO (internal)             │
└─────────────────────────────────┘
```

---

## ✅ What You're Deploying

Your RTX6000 will run:

1. **Nginx** (port 80) - Entry point, reverse proxy
2. **FastAPI Backend** (internal) - ML API, training endpoints
3. **React Frontend** (internal) - UI served as static files
4. **PostgreSQL** (internal) - Database
5. **MinIO** (internal) - Object storage for models

**Only port 80 is exposed** - everything else is internal. This is secure and follows the Aras pattern.

---

## 📋 Verification Checklist

After deployment, check:

```bash
# 1. All containers running
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 2. Backend health
curl http://localhost/api/health
# Should return: {"status":"healthy"}

# 3. Frontend
curl http://localhost/
# Should return HTML

# 4. View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

---

## 🎯 Next Steps

1. ✅ **You:** Deploy on RTX6000 using the instructions above
2. ⏳ **You:** Give `<SERVER_IP>:80` to your senior
3. ⏳ **Senior:** Configures reverse proxy to route public traffic to your server
4. ⏳ **Senior:** Sets up DNS (e.g., `autoimmune.yourdomain.com`)
5. ⏳ **Senior:** Configures SSL/TLS with Certbot
6. ✅ **Result:** Public URL is live! 🎉

---

## 🆘 Troubleshooting

### If backend doesn't start:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs fastapi
```

### If database connection fails:
```bash
# Check if postgres is running
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps postgres

# Check postgres logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs postgres

# Verify DATABASE_URL in .env matches POSTGRES_* variables
```

### If port 80 is in use:
```bash
# Check what's using port 80
sudo netstat -tulpn | grep :80

# Stop the conflicting service or change port in docker-compose.prod.yml
```

---

## 📚 Documentation

- **Full Guide:** [DEPLOYMENT_GUIDE_RTX6000.md](./DEPLOYMENT_GUIDE_RTX6000.md)
- **Quick Reference:** [QUICK_DEPLOY_RTX6000.md](./QUICK_DEPLOY_RTX6000.md)
- **Aras Guide:** The guide you shared (for understanding the overall architecture)

---

## 💡 Tips

1. **Test locally first** - Run `./deploy.sh` and verify everything works before telling your senior
2. **Save logs** - If something fails, save logs with: `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs > deployment-logs.txt`
3. **Commit these files** - Push the new deployment files to your GitHub repo so they're on the server:
   ```bash
   git add .
   git commit -m "Add production deployment configuration for RTX6000"
   git push origin main
   ```

---

## 🎉 Summary

You now have:
- ✅ Complete production deployment setup
- ✅ Automated deployment script
- ✅ Comprehensive documentation
- ✅ Security best practices implemented
- ✅ Following the Aras deployment pattern

**You're ready to deploy! 🚀**

Just follow [QUICK_DEPLOY_RTX6000.md](./QUICK_DEPLOY_RTX6000.md) for the fastest path to deployment.
