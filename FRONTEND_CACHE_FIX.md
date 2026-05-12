# Frontend Cache Issue - Quick Fix Guide

## Problem: Frontend showing old version after deployment

This happens because Docker uses cached layers when building. The frontend container needs to be rebuilt with `--no-cache`.

---

## ✅ SOLUTION - Run on RTX6000 Server:

### Option 1: Using the automated script (Recommended)
```bash
ssh mtuser1@100.122.108.118
# Password: mezPez19!@

cd usm-autoimmune-ml-platform
bash redeploy-frontend.sh
```

### Option 2: Manual commands
```bash
ssh mtuser1@100.122.108.118
cd usm-autoimmune-ml-platform

# Pull latest code
git pull origin main

# Stop containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Remove old frontend image
docker rmi usm-autoimmune-ml-platform-frontend

# Rebuild with NO CACHE
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache nginx

# Start containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify
docker compose ps
```

---

## 🌐 After Rebuilding:

1. **Clear browser cache:**
   - Windows: `Ctrl + Shift + R` or `Ctrl + F5`
   - Mac: `Cmd + Shift + R`

2. **Open:** http://100.122.108.118:8080

3. **Verify changes:**
   - ✅ System section removed from sidebar
   - ✅ No "GPU Monitor" or "Settings" in sidebar
   - ✅ All pages have consistent header (title, breadcrumb, search, bell, profile)
   - ✅ Search bar works with Ctrl+K or Cmd+K

---

## 🔍 Troubleshooting:

### If frontend still shows old version:
```bash
# Check container logs
docker compose logs frontend

# Verify frontend image was rebuilt
docker images | grep frontend

# Nuclear option - remove all images and rebuild
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker system prune -af
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### If containers won't start:
```bash
# Check what's using port 8080
sudo netstat -tulpn | grep 8080

# Check nginx logs
docker compose logs nginx

# Restart everything
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart
```

---

## 📝 What Changed:

1. **Removed from sidebar:**
   - GPU Monitor
   - Settings

2. **Added to all pages:**
   - PageHeader component with search, notifications, profile
   - Consistent navigation structure

3. **Pages now functional:**
   - ML Queue
   - Training Jobs
   - Registry
   - Comparison
   - Explainability
   - Predictions
   - Patient Scoring
   - Clinical Review

---

## 🎯 Expected Result:

After clearing cache, you should see:
- Sidebar has 3 sections only: Platform, Modeling, Clinical Operations
- Every page has same header style
- Search bar (⌘K) works on all pages
- No Settings or GPU Monitor anywhere
