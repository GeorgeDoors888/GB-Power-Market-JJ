# Setup Dell from iMac - Copy & Paste Instructions

**Dell IP:** 100.119.237.107

---

## Step 1: SSH to Dell and Run Setup

Copy and paste this entire block into your iMac terminal:

```bash
ssh YOUR_DELL_USER@100.119.237.107 << 'ENDSSH'

# Navigate to home
cd ~

# Clone or update repository
if [ ! -d "GB-Power-Market-JJ" ]; then
    git clone https://github.com/GeorgeDoors888/GB-Power-Market-JJ.git
else
    cd GB-Power-Market-JJ && git pull && cd ~
fi

# Install code-server
curl -fsSL https://code-server.dev/install.sh | sh

# Configure code-server
mkdir -p ~/.config/code-server
cat > ~/.config/code-server/config.yaml << 'EOF'
bind-addr: 0.0.0.0:8080
auth: password
password: gb-power-2025-secure
cert: false
EOF

# Start and enable code-server
sudo systemctl enable --now code-server@$USER

# Check status
echo ""
echo "✅ Setup complete!"
echo ""
echo "Code-server status:"
sudo systemctl status code-server@$USER --no-pager

echo ""
echo "Access from iPad Safari: http://100.119.237.107:8080"
echo "Password: gb-power-2025-secure"

ENDSSH
```

**⚠️ Replace `YOUR_DELL_USER` with your actual Dell username!**

---

## Step 2: Verify It's Working

```bash
ssh YOUR_DELL_USER@100.119.237.107 'curl -I localhost:8080 2>/dev/null | head -n 1'
```

Should show: `HTTP/1.1 302 Found`

---

## Step 3: Transfer GCP Credentials (Optional)

If you have `inner-cinema-credentials.json` on your iMac:

```bash
scp ~/path/to/inner-cinema-credentials.json YOUR_DELL_USER@100.119.237.107:~/GB-Power-Market-JJ/

ssh YOUR_DELL_USER@100.119.237.107 << 'ENDSSH'
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/GB-Power-Market-JJ/inner-cinema-credentials.json"' >> ~/.bashrc
source ~/.bashrc
echo "✅ Credentials configured"
ENDSSH
```

---

## Step 4: On Your iPad

1. Open Safari
2. Go to: **http://100.119.237.107:8080**
3. Enter password: **gb-power-2025-secure**
4. You'll see VS Code in your browser!
5. Click "Open Folder" → `/home/YOUR_DELL_USER/GB-Power-Market-JJ`

---

## Step 5: Install Python Dependencies (in code-server terminal)

Once you're in VS Code on your iPad, open the terminal and run:

```bash
cd ~/GB-Power-Market-JJ

# Install Python packages
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread google-auth

# Verify BigQuery access
python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("✅ BigQuery connected")'
```

---

## Troubleshooting

### If code-server won't start:
```bash
ssh YOUR_DELL_USER@100.119.237.107
sudo systemctl restart code-server@$USER
sudo journalctl -u code-server@$USER -n 50
```

### If can't access from iPad:
```bash
ssh YOUR_DELL_USER@100.119.237.107
sudo netstat -tlnp | grep 8080
```

**Firewall check:**
```bash
ssh YOUR_DELL_USER@100.119.237.107
sudo ufw status
# If blocked, allow port 8080:
sudo ufw allow 8080/tcp
```

### Stop code-server:
```bash
ssh YOUR_DELL_USER@100.119.237.107 'sudo systemctl stop code-server@$USER'
```

### Start code-server:
```bash
ssh YOUR_DELL_USER@100.119.237.107 'sudo systemctl start code-server@$USER'
```

### Check logs:
```bash
ssh YOUR_DELL_USER@100.119.237.107 'tail -f ~/.local/share/code-server/coder-logs/*.log'
```

---

## Advanced: Auto-start on Dell Boot

Code-server is already configured to auto-start via systemd. To disable:

```bash
ssh YOUR_DELL_USER@100.119.237.107 'sudo systemctl disable code-server@$USER'
```

To re-enable:

```bash
ssh YOUR_DELL_USER@100.119.237.107 'sudo systemctl enable code-server@$USER'
```

---

## Security Notes

- **Password:** `gb-power-2025-secure` (change in `~/.config/code-server/config.yaml`)
- **Network:** Only accessible on your local network (100.119.x.x)
- **HTTPS:** Not configured (cert: false). For production, use reverse proxy with SSL.
- **Firewall:** Ensure port 8080 is not exposed to internet

---

## Quick Reference Commands

### From iMac:

```bash
# Check if code-server is running
ssh YOUR_DELL_USER@100.119.237.107 'systemctl is-active code-server@$USER'

# Restart code-server
ssh YOUR_DELL_USER@100.119.237.107 'sudo systemctl restart code-server@$USER'

# View code-server password
ssh YOUR_DELL_USER@100.119.237.107 'cat ~/.config/code-server/config.yaml | grep password'

# Update repository
ssh YOUR_DELL_USER@100.119.237.107 'cd ~/GB-Power-Market-JJ && git pull'
```

---

## iPad Safari Tips

1. **Add to Home Screen:** Tap Share → "Add to Home Screen" for quick access
2. **Full Screen:** Tap the "⊞" icon in Safari toolbar
3. **Keyboard:** Connect Bluetooth keyboard for better experience
4. **Terminal:** Use built-in VS Code terminal (Ctrl+` or View → Terminal)
5. **File Explorer:** Left sidebar shows all project files

---

## What You Can Do on iPad

✅ Edit Python scripts  
✅ Run BigQuery queries  
✅ View JSON schemas  
✅ Git commits and pushes  
✅ Run terminal commands  
✅ Install Python packages  
✅ Debug scripts  
✅ Access all 227 BigQuery tables  

---

**Last Updated:** December 16, 2025  
**Status:** Production Ready ✅
