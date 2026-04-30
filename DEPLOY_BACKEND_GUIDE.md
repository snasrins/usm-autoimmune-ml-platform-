# Backend Deployment Guide via WinSCP

## Problem: Error Code 4 - General Failure

**Error message:**
```
General failure (server should provide error description).
Error code: 4
Error message from server: Failure
```

**Root cause:** Backend service is running and has the Python file open/locked.

---

## ✅ Deployment Steps (Windows → Linux via WinSCP)

### **Step 1: Connect to Server via SSH**

**Windows PowerShell:**
```powershell
ssh shaggy@100.106.132.15
```

### **Step 2: Stop Backend Service**

```bash
# Navigate to project directory
cd /home/shaggy/usm-autoimmune-ml-platform

# Check if backend is running
docker ps | grep backend
# OR if running directly:
ps aux | grep uvicorn

# Stop with Docker Compose:
docker-compose down

# OR stop specific backend container:
docker stop backend

# OR if running directly (find PID and kill):
pkill -f "uvicorn app.main:app"
```

### **Step 3: Deploy Files with WinSCP**

**Now upload the file:**
1. Open WinSCP
2. Connect to `100.106.132.15`
3. Navigate to `/home/shaggy/usm-autoimmune-ml-platform/app/services/`
4. Upload `gemma_conversational_service.py`
5. ✅ Should work without error!

### **Step 4: Restart Backend**

```bash
# Return to SSH terminal

# Restart with Docker Compose:
docker-compose up -d backend

# OR start directly:
cd /home/shaggy/usm-autoimmune-ml-platform
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &

# Verify it's running:
curl http://localhost:8001/health
```

### **Step 5: Verify Dr. Myra**

**Check backend logs:**
```bash
# Docker logs:
docker logs backend -f

# Direct logs:
tail -f /var/log/backend.log

# Look for:
# "Loading Gemma-4-E4B model from Hugging Face..."
```

**Test from browser:**
- Open chat with Dr. Myra
- Ask: "explain the platform to me"
- Check console for: `model: 'gemma-4-E4B'`

---

## 🚨 Alternative: Deploy Without Stopping (Risky)

If you can't stop the backend:

### **Option A: Use `--reload` Mode**

If backend is running with `--reload` flag, it will auto-reload on file changes:

```bash
# On server, edit directly:
ssh shaggy@100.106.132.15
cd /home/shaggy/usm-autoimmune-ml-platform
nano app/services/gemma_conversational_service.py

# Make changes, save, backend auto-reloads
```

### **Option B: Deploy to Temporary Location First**

```bash
# On server:
ssh shaggy@100.106.132.15

# Create temp directory
mkdir -p /tmp/deploy

# Upload to /tmp/deploy via WinSCP (no conflicts)

# Then move files:
cd /home/shaggy/usm-autoimmune-ml-platform
docker-compose down
cp /tmp/deploy/gemma_conversational_service.py app/services/
docker-compose up -d backend
```

---

## 🔍 Other Possible Causes of Error 4

### **Check Disk Space:**
```bash
ssh shaggy@100.106.132.15
df -h

# Should show available space on /home partition
# If disk is full, clean up:
docker system prune -a
```

### **Check File Permissions:**
```bash
ssh shaggy@100.106.132.15
ls -la /home/shaggy/usm-autoimmune-ml-platform/app/services/

# Should show:
# -rw-r--r-- shaggy shaggy gemma_conversational_service.py

# Fix permissions if needed:
sudo chown shaggy:shaggy app/services/gemma_conversational_service.py
chmod 644 app/services/gemma_conversational_service.py
```

### **Check if File is Locked:**
```bash
ssh shaggy@100.106.132.15
lsof | grep gemma_conversational_service.py

# If output shows a process, that's the lock
# Kill the process ID:
kill -9 <PID>
```

---

## 📋 Quick Deployment Checklist

- [ ] SSH into server: `ssh shaggy@100.106.132.15`
- [ ] Navigate to project: `cd /home/shaggy/usm-autoimmune-ml-platform`
- [ ] Stop backend: `docker-compose down`
- [ ] Upload files via WinSCP
- [ ] Restart backend: `docker-compose up -d backend`
- [ ] Check logs: `docker logs backend -f`
- [ ] Test Dr. Myra in browser
- [ ] Verify `model: 'gemma-4-E4B'` in console

---

## 🎯 Recommended Workflow

**For Development:**
1. Edit files locally on Windows
2. Test locally if possible
3. Stop remote backend
4. Deploy via WinSCP
5. Restart remote backend
6. Verify in production

**For Quick Changes:**
1. SSH directly to server
2. Edit with nano/vim
3. Backend auto-reloads (if using `--reload`)
4. Test immediately

---

## 💡 Pro Tips

1. **Use `--reload` in development:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```
   Auto-reloads on file changes!

2. **Keep backups before deployment:**
   ```bash
   ssh shaggy@100.106.132.15
   cp app/services/gemma_conversational_service.py \
      app/services/gemma_conversational_service.py.bak
   ```

3. **Use rsync instead of WinSCP:**
   ```powershell
   # From Windows (if rsync installed)
   rsync -avz app/services/gemma_conversational_service.py \
         shaggy@100.106.132.15:/home/shaggy/usm-autoimmune-ml-platform/app/services/
   ```

4. **Deploy via Git (cleanest method):**
   ```bash
   # On Windows:
   git add app/services/gemma_conversational_service.py
   git commit -m "Update Dr. Myra to use gemma-4-E4B"
   git push

   # On server:
   ssh shaggy@100.106.132.15
   cd /home/shaggy/usm-autoimmune-ml-platform
   docker-compose down
   git pull
   docker-compose up -d backend
   ```
