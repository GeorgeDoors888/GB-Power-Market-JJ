# 🚀 Quick Setup Reference Card

## **1️⃣ Slack Notifications** (10 minutes)

### **Get Webhook URL**:
1. Go to: https://api.slack.com/messaging/webhooks
2. Create app: "AI Gateway Alerts"
3. Enable Incoming Webhooks
4. Add webhook to workspace → Copy URL

### **Configure**:
```bash
# Edit .env.ai-gateway
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Restart server
pkill -f api_gateway && ./start_gateway.sh
```

### **Test**:
```bash
curl -X POST \
  -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  -H "Content-Type: application/json" \
  -d '{"tab":"Raw Data","range":"Z1","values":[["Test"]]}' \
  "http://localhost:8000/sheets/update"
```

**Expected**: Message in Slack channel ✅

---

## **2️⃣ UpCloud Deployment** (30-45 minutes)

### **Quick Deploy**:
```bash
# 1. Package files
mkdir -p deploy_package
cp api_gateway.py deploy_package/
cp inner-cinema-credentials.json deploy_package/
cp .env.ai-gateway deploy_package/
tar -czf api-gateway-deploy.tar.gz deploy_package/

# 2. Upload
scp -i ~/.ssh/id_ed25519 api-gateway-deploy.tar.gz root@94.237.55.15:/root/

# 3. SSH and deploy
ssh -i ~/.ssh/id_ed25519 root@94.237.55.15
cd /root && tar -xzf api-gateway-deploy.tar.gz
mkdir -p /opt/ai-gateway && mv deploy_package/* /opt/ai-gateway/
cd /opt/ai-gateway
python3.12 -m pip install fastapi uvicorn google-cloud-bigquery gspread oauth2client paramiko slowapi python-multipart requests
```

### **Create Service**:
```bash
cat > /etc/systemd/system/ai-gateway.service << 'EOF'
[Unit]
Description=AI Gateway API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-gateway
EnvironmentFile=/opt/ai-gateway/.env.ai-gateway
Environment="GOOGLE_APPLICATION_CREDENTIALS=/opt/ai-gateway/inner-cinema-credentials.json"
ExecStart=/usr/bin/python3.12 -m uvicorn api_gateway:app --host 0.0.0.0 --port 8000
Restart=always
StandardOutput=append:/var/log/ai-gateway.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-gateway.service
systemctl start ai-gateway.service
```

### **Test**:
```bash
# From your Mac
curl -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  http://94.237.55.15:8000/health
```

---

## **3️⃣ ChatGPT Action** (15 minutes)

### **Steps**:
1. Export schema: ✅ **Already done!** → `chatgpt-action-schema.json`
2. Go to: https://chatgpt.com/ → Profile → Customize ChatGPT → Actions
3. Click "Create new action"

### **Configuration**:
```
Name: GB Power Market API
Description: Access UK electricity data and server management

Schema: [Paste contents of chatgpt-action-schema.json]

Authentication: API Key
  - Type: API Key
  - Header Name: Authorization
  - Format: Bearer {api_key}
  - Key: 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af

Base URL: 
  - Local: http://localhost:8000 (needs ngrok)
  - Production: http://94.237.55.15:8000
```

### **Test Prompts**:
```
"What were UK electricity prices yesterday?"
"Show me wind generation for the past week"
"Check the status of my UpCloud server"
```

---

## **Files Created**

✅ `SLACK_SETUP.md` - Complete Slack webhook guide  
✅ `UPCLOUD_API_GATEWAY_DEPLOY.md` - Deployment instructions  
✅ `CHATGPT_ACTION_SETUP.md` - Action configuration guide  
✅ `chatgpt-action-schema.json` - OpenAPI schema for ChatGPT  
✅ `QUICK_SETUP_REFERENCE.md` - This file!

---

## **API Key** (Keep Secure!)

```
33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af
```

---

## **Useful Commands**

```bash
# Start server locally
./start_gateway.sh

# Stop server
pkill -f api_gateway.py

# View logs
tail -f /tmp/ai-gateway-audit.log

# Test endpoint
curl -H "Authorization: Bearer 33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af" \
  http://localhost:8000/health

# Check server status
ps aux | grep api_gateway
```

---

## **Next Steps**

- [ ] Set up Slack webhook (10 min)
- [ ] Deploy to UpCloud (45 min) - optional
- [ ] Configure ChatGPT Action (15 min)
- [ ] Test end-to-end with ChatGPT
- [ ] Review audit logs

---

**Total Time**: 40-70 minutes depending on which components you set up.

**Status**: All guides ready! Pick the features you want to enable.
