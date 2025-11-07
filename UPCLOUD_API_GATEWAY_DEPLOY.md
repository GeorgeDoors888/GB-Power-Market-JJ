# 🚀 UpCloud API Gateway Deployment (Complete Guide)

**Server**: 94.237.55.15 (AlmaLinux)  
**Time Required**: 30-45 minutes  
**Difficulty**: Intermediate  

---

## Pre-Deployment Checklist

✅ Local server working on localhost:8000  
✅ All tests passing  
✅ Credentials file ready (inner-cinema-credentials.json)  
✅ API key generated: `33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af`  
✅ SSH access to UpCloud server  

---

## Step 1: Prepare Deployment Files

### **Create deployment package**:

```bash
cd "/Users/georgemajor/GB Power Market JJ"

# Create deployment directory
mkdir -p deploy_package

# Copy necessary files
cp api_gateway.py deploy_package/
cp inner-cinema-credentials.json deploy_package/
cp start_gateway.sh deploy_package/
cp .env.ai-gateway deploy_package/

# Create archive
tar -czf api-gateway-deploy.tar.gz deploy_package/

# Verify contents
tar -tzf api-gateway-deploy.tar.gz
```

---

## Step 2: Upload to UpCloud

```bash
# Upload deployment package
scp -i ~/.ssh/id_ed25519 api-gateway-deploy.tar.gz root@94.237.55.15:/root/

# SSH into server
ssh -i ~/.ssh/id_ed25519 root@94.237.55.15
```

---

## Step 3: Server Setup (Run on UpCloud)

```bash
# Extract package
cd /root
tar -xzf api-gateway-deploy.tar.gz
cd deploy_package

# Move to proper location
mkdir -p /opt/ai-gateway
mv * /opt/ai-gateway/
cd /opt/ai-gateway

# Install Python dependencies
python3.12 -m pip install --upgrade pip
python3.12 -m pip install fastapi uvicorn google-cloud-bigquery gspread oauth2client paramiko slowapi python-multipart requests

# Set permissions
chmod 600 inner-cinema-credentials.json
chmod 600 .env.ai-gateway
chmod +x start_gateway.sh
chown -R root:root /opt/ai-gateway
```

---

## Step 4: Create Systemd Service

Create `/etc/systemd/system/ai-gateway.service`:

```bash
cat > /etc/systemd/system/ai-gateway.service << 'EOF'
[Unit]
Description=AI Gateway API Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-gateway
EnvironmentFile=/opt/ai-gateway/.env.ai-gateway

# Set credentials path
Environment="GOOGLE_APPLICATION_CREDENTIALS=/opt/ai-gateway/inner-cinema-credentials.json"

# Start command
ExecStart=/usr/bin/python3.12 -m uvicorn api_gateway:app --host 0.0.0.0 --port 8000

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/ai-gateway.log
StandardError=append:/var/log/ai-gateway-error.log

# Security
NoNewPrivileges=true
PrivateTmp=true

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```

---

## Step 5: Configure Firewall

```bash
# Check current firewall status
firewall-cmd --list-all

# Add port 8000 (if not already open)
firewall-cmd --permanent --add-port=8000/tcp

# Reload firewall
firewall-cmd --reload

# Verify
firewall-cmd --list-ports
```

---

## Step 6: Start Service

```bash
# Reload systemd
systemctl daemon-reload

# Enable service (start on boot)
systemctl enable ai-gateway.service

# Start service
systemctl start ai-gateway.service

# Check status
systemctl status ai-gateway.service
```

**Expected output**:
```
● ai-gateway.service - AI Gateway API Server
     Loaded: loaded (/etc/systemd/system/ai-gateway.service; enabled)
     Active: active (running) since Wed 2025-11-06 12:00:00 UTC
```

---

## Step 7: Test Remote Access

### **From your Mac**:

```bash
# Test health endpoint
curl -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  "http://94.237.55.15:8000/health" | python3 -m json.tool

# Test BigQuery
curl -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  "http://94.237.55.15:8000/bigquery/prices?days=7" | python3 -m json.tool

# Test UpCloud status (self-check)
curl -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  "http://94.237.55.15:8000/upcloud/status" | python3 -m json.tool
```

---

## Step 8: Monitor Logs

```bash
# Server logs
tail -f /var/log/ai-gateway.log

# Error logs
tail -f /var/log/ai-gateway-error.log

# Audit logs
tail -f /tmp/ai-gateway-audit.log

# Systemd journal
journalctl -u ai-gateway.service -f
```

---

## Management Commands

### **On UpCloud Server**:

```bash
# Stop service
systemctl stop ai-gateway.service

# Start service
systemctl start ai-gateway.service

# Restart service
systemctl restart ai-gateway.service

# Check status
systemctl status ai-gateway.service

# View recent logs
journalctl -u ai-gateway.service -n 50

# Check resource usage
ps aux | grep api_gateway
netstat -tulpn | grep 8000
```

---

## Update Deployed Code

```bash
# On your Mac - create new package
cd "/Users/georgemajor/GB Power Market JJ"
tar -czf api-gateway-deploy.tar.gz deploy_package/
scp -i ~/.ssh/id_ed25519 api-gateway-deploy.tar.gz root@94.237.55.15:/root/

# On UpCloud
ssh -i ~/.ssh/id_ed25519 root@94.237.55.15
cd /root
tar -xzf api-gateway-deploy.tar.gz
cp deploy_package/api_gateway.py /opt/ai-gateway/

# Restart service
systemctl restart ai-gateway.service
systemctl status ai-gateway.service
```

---

## SSL/HTTPS Setup (Optional but Recommended)

### **Option 1: Self-Signed Certificate (Quick)**

```bash
# On UpCloud
cd /opt/ai-gateway

# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=94.237.55.15"

# Update systemd service ExecStart line to:
ExecStart=/usr/bin/python3.12 -m uvicorn api_gateway:app --host 0.0.0.0 --port 8000 --ssl-keyfile=/opt/ai-gateway/key.pem --ssl-certfile=/opt/ai-gateway/cert.pem

# Restart
systemctl daemon-reload
systemctl restart ai-gateway.service
```

Test with:
```bash
curl -k -H "Authorization: Bearer YOUR_KEY" https://94.237.55.15:8000/health
```

### **Option 2: Nginx Reverse Proxy (Production)**

```bash
# Install nginx
dnf install -y nginx

# Create nginx config
cat > /etc/nginx/conf.d/ai-gateway.conf << 'EOF'
server {
    listen 443 ssl;
    server_name 94.237.55.15;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name 94.237.55.15;
    return 301 https://$server_name$request_uri;
}
EOF

# Generate SSL cert
mkdir -p /etc/nginx/ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/nginx/ssl/key.pem \
  -out /etc/nginx/ssl/cert.pem \
  -days 365 \
  -subj "/CN=94.237.55.15"

# Enable and start nginx
systemctl enable nginx
systemctl start nginx

# Update firewall for HTTPS
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

---

## Troubleshooting

### **Service won't start**

```bash
# Check detailed status
systemctl status ai-gateway.service -l

# Check journal
journalctl -u ai-gateway.service -n 100

# Test Python script directly
cd /opt/ai-gateway
python3.12 -m uvicorn api_gateway:app --host 0.0.0.0 --port 8000
```

### **Can't connect from outside**

```bash
# Check if service is listening
netstat -tulpn | grep 8000

# Check firewall
firewall-cmd --list-all

# Test locally first
curl http://127.0.0.1:8000/
```

### **BigQuery errors on server**

```bash
# Check credentials file
ls -la /opt/ai-gateway/inner-cinema-credentials.json

# Check environment variable
systemctl show ai-gateway.service | grep GOOGLE_APPLICATION_CREDENTIALS

# Test BigQuery access
cd /opt/ai-gateway
python3.12 -c "from google.cloud import bigquery; client = bigquery.Client(); print('OK')"
```

---

## Security Recommendations

### **1. Restrict API Access by IP**

Edit `api_gateway.py` to add IP whitelist:

```python
ALLOWED_IPS = ["YOUR.HOME.IP.ADDRESS", "127.0.0.1"]

@app.middleware("http")
async def check_ip(request: Request, call_next):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        return JSONResponse({"error": "Forbidden"}, status_code=403)
    return await call_next(request)
```

### **2. Rotate API Key Regularly**

```bash
# Generate new key
openssl rand -hex 32

# Update .env.ai-gateway on server
# Update ChatGPT Action authentication
# Restart service
```

---

## Quick Reference

**Server URL**: `http://94.237.55.15:8000`  
**API Key**: `33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af`  
**Logs**: `/var/log/ai-gateway.log`  
**Config**: `/opt/ai-gateway/.env.ai-gateway`  
**Service**: `systemctl status ai-gateway.service`  

---

**Status**: Ready to deploy!  
**Next**: Run Step 1 to create deployment package.
