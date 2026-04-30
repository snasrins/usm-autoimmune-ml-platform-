#!/bin/bash
# ============================================
# Setup HTTPS/TLS for USM Autoimmune Platform
# ============================================

set -e

echo "================================================"
echo "USM Autoimmune ML Platform - HTTPS/TLS Setup"
echo "================================================"

# 1. Install nginx
echo ""
echo "Step 1/5: Installing nginx..."
if ! command -v nginx &> /dev/null; then
    apt-get update
    apt-get install -y nginx
    echo "✅ nginx installed"
else
    echo "✅ nginx already installed"
fi

# 2. Generate self-signed certificate (for testing/internal use)
echo ""
echo "Step 2/5: Generating self-signed SSL certificate..."
mkdir -p /etc/nginx/ssl
if [ ! -f /etc/nginx/ssl/usm-autoimmune.crt ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/usm-autoimmune.key \
        -out /etc/nginx/ssl/usm-autoimmune.crt \
        -subj "/C=MY/ST=Penang/L=George Town/O=Universiti Sains Malaysia/OU=School of Medical Sciences/CN=100.106.132.15"
    echo "✅ Self-signed certificate generated"
else
    echo "✅ Certificate already exists"
fi

# 3. Copy nginx configuration
echo ""
echo "Step 3/5: Copying nginx configuration..."
cp nginx-https.conf /etc/nginx/sites-available/usm-autoimmune
ln -sf /etc/nginx/sites-available/usm-autoimmune /etc/nginx/sites-enabled/usm-autoimmune
# Remove default site
rm -f /etc/nginx/sites-enabled/default
echo "✅ nginx configuration installed"

# 4. Test nginx configuration
echo ""
echo "Step 4/5: Testing nginx configuration..."
nginx -t
echo "✅ nginx configuration valid"

# 5. Restart nginx
echo ""
echo "Step 5/5: Restarting nginx..."
systemctl restart nginx
systemctl enable nginx
echo "✅ nginx restarted and enabled"

echo ""
echo "================================================"
echo "✅ HTTPS/TLS Setup Complete!"
echo "================================================"
echo ""
echo "Platform is now accessible via HTTPS:"
echo "  • Frontend: https://100.106.132.15/"
echo "  • Backend:  https://100.106.132.15/api/"
echo "  • Docs:     https://100.106.132.15/docs"
echo ""
echo "⚠️  IMPORTANT:"
echo "  1. This uses a self-signed certificate"
echo "  2. Browsers will show a security warning"
echo "  3. For production, replace with Let's Encrypt certificate"
echo ""
echo "To get Let's Encrypt certificate (if you have a domain):"
echo "  apt-get install certbot python3-certbot-nginx"
echo "  certbot --nginx -d yourdomain.com"
echo ""
