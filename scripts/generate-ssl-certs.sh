#!/bin/bash
# ============================================
# Generate PostgreSQL SSL Certificates
# USM Autoimmune ML Platform
# ============================================

echo "=== Generating PostgreSQL SSL Certificates ==="
echo

# Create directory if it doesn't exist
mkdir -p ./ssl

# Generate private key
openssl genrsa -out ./ssl/server.key 2048
echo "✓ Generated private key (server.key)"

# Generate certificate signing request
openssl req -new -key ./ssl/server.key -out ./ssl/server.csr \
  -subj "/C=MY/ST=Penang/L=Gelugor/O=Universiti Sains Malaysia/OU=Autoimmune ML Platform/CN=usm-autoimmune-postgres"
echo "✓ Generated certificate signing request (server.csr)"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in ./ssl/server.csr -signkey ./ssl/server.key -out ./ssl/server.crt
echo "✓ Generated self-signed certificate (server.crt)"

# Set proper permissions
chmod 600 ./ssl/server.key
chmod 644 ./ssl/server.crt
echo "✓ Set proper file permissions"

# Copy to PostgreSQL volume location (will be mounted in Docker)
cp ./ssl/server.key ./ssl/server.crt ./init-db/
echo "✓ Copied certificates to init-db directory"

echo
echo "=== SSL Certificate Generation Complete ==="
echo
echo "Certificates location:"
echo "  - Private key: ./ssl/server.key"
echo "  - Certificate: ./ssl/server.crt"
echo
echo "To enable SSL in docker-compose.yml, uncomment the SSL command section."
echo
