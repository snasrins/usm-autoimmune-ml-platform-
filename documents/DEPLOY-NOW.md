# 🚀 DEPLOYMENT INSTRUCTIONS

**Date:** March 12, 2026  
**Platform:** USM Autoimmune ML Platform  
**Status:** Ready to Deploy

---

## 📦 Step 1: Upload Files to Server

Your project is packaged in: **`usm-platform.zip`** (located in project root)

### Method A: Using WinSCP (Easiest)
1. Download WinSCP: https://winscp.net/
2. Connect to: `172.24.175.24`
3. Username: `mtuser2`
4. Password: `<your-password>`
5. Upload `usm-platform.zip` to `/home/mtuser2/`

### Method B: Using PowerShell + OpenSSH
```powershell
# If you have OpenSSH installed
scp usm-platform.zip mtuser2@172.24.175.24:~/
```

### Method C: Copy-paste via SSH
```powershell
# SSH to server first
ssh mtuser2@172.24.175.24

# On server, download from a shared location
# (if you upload to cloud storage like Google Drive first)
```

---

## 🖥️ Step 2: SSH to Server

```powershell
ssh mtuser2@172.24.175.24
```

---

## 📂 Step 3: Extract Files

```bash
# On the server
cd ~
unzip usm-platform.zip -d usm-autoimmune-ml-platform
cd usm-autoimmune-ml-platform
ls -la
```

---

## 🔧 Step 4: Run Automated Deployment

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Run deployment (this does everything!)
./scripts/deploy.sh
```

**What the script does:**
1. ✓ Installs ZeroTier
2. ✓ Joins network d5e5fb653720782f
3. ✓ Installs Docker + NVIDIA Container Toolkit
4. ✓ Installs Docker Compose
5. ✓ Creates directory structure
6. ✓ Deploys platform with `docker compose up -d`
7. ✓ Tests API health
8. ✓ Verifies database connection

---

## ✅ Step 5: Verify Deployment

After deployment completes, test:

```bash
# Check services are running
docker compose ps

# Test API health
curl http://172.24.50.103:8000/health

# Should return: {"status":"healthy",...}

# View logs
docker compose logs -f

# Test database
docker compose exec postgres psql -U usm_db_admin -d usm_autoimmune_registry -c "\dt"
```

---

## 🌐 Step 6: Access from Windows

### Install ZeroTier on Windows
1. Download: https://www.zerotier.com/download/
2. Install and run
3. Join network: `d5e5fb653720782f`
4. Go to https://my.zerotier.com and authorize your Windows device

### Access URLs
- **API Docs:** http://172.24.50.103:8000/docs
- **API Health:** http://172.24.50.103:8000/health
- **PgAdmin:** http://172.24.50.103:5050
- **Database:** 172.24.50.103:5432

---

## 🔐 Security Checklist

After deployment:
- [ ] Change `POSTGRES_PASSWORD` in .env
- [ ] Change `PGADMIN_PASSWORD` in .env
- [ ] Update `SMTP_PASSWORD` with real credentials
- [ ] Default admin password: `ChangeThisSecurePassword123!` (change after first login)

---

## 🐛 Troubleshooting

### If deployment fails:

```bash
# View all logs
docker compose logs

# View specific service logs
docker compose logs postgres
docker compose logs fastapi

# Restart services
docker compose restart

# Full restart
docker compose down
docker compose up -d
```

### If ZeroTier IP is different:

```bash
# Check actual IP
ip addr show | grep zt

# Update .env file
nano .env
# Change ZEROTIER_IP to your actual IP

# Restart services
docker compose restart
```

### If GPU not working:

```bash
# Test GPU access
nvidia-smi

# Test in Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Restart Docker
sudo systemctl restart docker
```

---

## 📊 What's Next?

After successful deployment:

### Week 1 (March 12-15):
- [ ] Verify all services running
- [ ] Test GPU access in container
- [ ] Start authentication module (UPB-17, 18, 19)

### Week 2 (March 16-22):
- [ ] Build upload interface (UPB-01, 02)
- [ ] Implement ETL pipeline (UPB-22, 23, 24, 32)

### Week 3 (March 23-29):
- [ ] Complete Sprint 1 deliverables
- [ ] Prepare for Sprint 2

---

## 📞 Support

For issues:
1. Check logs: `docker compose logs -f`
2. Review documentation in `documents/` folder
3. Contact team via project channels

---

**Ready to deploy!** 🚀

Follow the steps above in order. The automated script (`deploy.sh`) handles most of the work!
