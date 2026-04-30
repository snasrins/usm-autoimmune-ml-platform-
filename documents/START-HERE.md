# 🚀 IMMEDIATE DEPLOYMENT STEPS

**Current Status:** Project packaged and ready  
**Next Action:** Upload and deploy to server

---

## 📤 STEP 1: Upload to Server

### Download WinSCP (Recommended)
1. Go to: https://winscp.net/eng/download.php
2. Download and install
3. Launch WinSCP

### Connect with WinSCP:
- **File protocol:** SFTP
- **Host name:** `172.24.175.24`
- **Port:** 22
- **User name:** `mtuser2`
- **Password:** `<your-server-password>`

### Upload File:
1. After connecting, navigate to `/home/mtuser2/`
2. Drag and drop `usm-platform.zip` from your Windows machine
3. Wait for upload to complete (~30 KB, should be instant)

---

## 🖥️ STEP 2: Connect to Server

### Download PuTTY:
1. Go to: https://www.putty.org/
2. Download putty.exe
3. Run PuTTY

### Connect via PuTTY:
- **Host Name:** `172.24.175.24`
- **Port:** 22
- **Connection type:** SSH
- Click **Open**
- Login as: `mtuser2`
- Password: `<your-server-password>`

---

## 🚀 STEP 3: Deploy on Server

After logging in via PuTTY, copy-paste these commands one by one:

```bash
# 1. Extract the uploaded zip file
cd ~
unzip -o usm-platform.zip -d usm-autoimmune-ml-platform
cd usm-autoimmune-ml-platform

# 2. Make deploy script executable
chmod +x scripts/deploy.sh

# 3. Run automated deployment
./scripts/deploy.sh
```

**The script will:**
- ✓ Install ZeroTier and join your network
- ✓ Install Docker + NVIDIA Container Toolkit
- ✓ Create all required directories
- ✓ Deploy the platform
- ✓ Test everything automatically

**During deployment:**
- When prompted about ZeroTier authorization: Open https://my.zerotier.com and authorize the device
- After authorization, press Enter to continue

---

## ✅ STEP 4: Verify Deployment

After deployment completes, test in PuTTY:

```bash
# Check service status
docker compose ps

# Test API
curl http://172.24.50.103:8000/health

# Should see: {"status":"healthy","service":"USM Autoimmune ML Platform",...}
```

---

## 🌐 STEP 5: Access from Windows

### Install ZeroTier on Windows:
1. Download: https://www.zerotier.com/download/
2. Install and run ZeroTier One
3. Right-click system tray icon → Join Network
4. Enter: `d5e5fb653720782f`
5. Go to https://my.zerotier.com → Authorize your Windows PC

### Open in Browser:
- **API Documentation:** http://172.24.50.103:8000/docs
- **API Health:** http://172.24.50.103:8000/health
- **PgAdmin:** http://172.24.50.103:5050

---

## 🎯 SUCCESS CHECKLIST

- [ ] WinSCP installed
- [ ] usm-platform.zip uploaded to server
- [ ] PuTTY installed  
- [ ] Connected to server via SSH
- [ ] Ran `./scripts/deploy.sh` successfully
- [ ] All services showing "Up (healthy)"
- [ ] API health endpoint returns success
- [ ] ZeroTier installed on Windows
- [ ] Can access http://172.24.50.103:8000/docs

---

## 🐛 Troubleshooting

**Can't connect with PuTTY?**
- Check server IP is correct: `172.24.175.24`
- Verify port 22 is open
- Check you're on the right network

**Upload fails in WinSCP?**
- Try SFTP protocol instead of SCP
- Check credentials are correct

**Deployment script fails?**
- Check logs in PuTTY
- Ensure you have sudo access
- Try running commands manually

**Services won't start?**
- Check: `docker compose logs`
- Restart: `docker compose restart`
- Check GPU: `nvidia-smi`

---

## ⏱️ Time Estimate

- WinSCP download & upload: 5 minutes
- PuTTY download & connect: 2 minutes
- Deployment script: 10-15 minutes
- **Total: ~20 minutes**

---

## 📞 Need Help?

If you encounter issues:
1. Take screenshots of error messages
2. Check `docker compose logs -f`
3. Review full documentation in `documents/DEPLOYMENT.md`

---

**You're almost there! Just 3 tools to download: WinSCP, PuTTY, ZeroTier** 🚀

Start with WinSCP to upload the file, then use PuTTY to run the deployment!
