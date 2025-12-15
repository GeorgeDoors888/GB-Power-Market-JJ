#!/bin/bash
# Setup script to reduce approval prompts in VS Code agent mode
# Run this once: chmod +x setup_agent_mode.sh && ./setup_agent_mode.sh

set -e

REPO_DIR="$HOME/GB-Power-Market-JJ"
cd "$REPO_DIR"

echo "🔧 Setting up VS Code and Git for Agent Mode..."
echo ""

# ========================================
# 1. VS Code Settings
# ========================================
echo "📝 Creating VS Code settings..."
mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "git.autofetch": true,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "git.postCommitCommand": "push",
  "extensions.ignoreRecommendations": false,
  "terminal.integrated.defaultProfile.linux": "bash",
  "[python]": {
    "editor.tabSize": 4,
    "editor.insertSpaces": true
  },
  "[javascript]": {
    "editor.tabSize": 2,
    "editor.insertSpaces": true
  },
  "[markdown]": {
    "editor.wordWrap": "on"
  }
}
EOF

echo "✅ VS Code settings created (.vscode/settings.json)"

# ========================================
# 2. Git Configuration
# ========================================
echo ""
echo "🔀 Configuring Git..."

git config --local user.name "GeorgeDoors888"
git config --local user.email "george@upowerenergy.uk"
git config --local credential.helper store
git config --local push.default current
git config --local push.autoSetupRemote true
git config --local pull.rebase false
git config --local core.autocrlf input
git config --local core.editor "code --wait"
git config --local fetch.prune true
git config --local init.defaultBranch main
git config --local merge.conflictstyle diff3

# Git aliases
git config --local alias.st status
git config --local alias.co checkout
git config --local alias.br branch
git config --local alias.cm "commit -m"
git config --local alias.amend "commit --amend --no-edit"
git config --local alias.push-f "push --force-with-lease"
git config --local alias.undo "reset HEAD~1 --soft"

echo "✅ Git config updated (.git/config)"

# ========================================
# 3. Git Credentials (for auto-push)
# ========================================
echo ""
echo "🔑 Setting up Git credential storage..."

if [ ! -f "$HOME/.git-credentials" ]; then
    echo "⚠️  Git credentials not found. You'll need to set up a Personal Access Token."
    echo ""
    echo "To avoid approval prompts for git push:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Generate new token (classic) with 'repo' scope"
    echo "3. Run: git config --global credential.helper store"
    echo "4. Run: git push (enter token as password)"
    echo "5. Credentials will be saved to ~/.git-credentials"
else
    echo "✅ Git credentials already configured"
fi

# ========================================
# 4. Python Environment
# ========================================
echo ""
echo "🐍 Checking Python environment..."

if [ ! -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ GOOGLE_APPLICATION_CREDENTIALS set: $GOOGLE_APPLICATION_CREDENTIALS"
else
    echo "⚠️  GOOGLE_APPLICATION_CREDENTIALS not set"
    echo "   Add to ~/.bashrc:"
    echo "   export GOOGLE_APPLICATION_CREDENTIALS=\"/home/george/.config/google-cloud/bigquery-credentials.json\""
fi

# Check Python packages
if python3 -c "import google.cloud.bigquery" 2>/dev/null; then
    echo "✅ google-cloud-bigquery installed"
else
    echo "⚠️  google-cloud-bigquery not installed"
    echo "   Run: pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas"
fi

if python3 -c "import gspread" 2>/dev/null; then
    echo "✅ gspread installed"
else
    echo "⚠️  gspread not installed"
    echo "   Run: pip3 install --user gspread google-auth"
fi

# ========================================
# 5. clasp (Google Apps Script CLI)
# ========================================
echo ""
echo "📜 Checking clasp installation..."

if command -v clasp &> /dev/null; then
    echo "✅ clasp installed ($(clasp --version))"
    
    # Check if clasp is logged in
    if clasp login --status 2>&1 | grep -q "logged in"; then
        echo "✅ clasp authenticated"
    else
        echo "⚠️  clasp not authenticated"
        echo "   Run: clasp login"
    fi
else
    echo "⚠️  clasp not installed"
    echo "   Run: npm install -g @google/clasp"
    echo "   Then: clasp login"
fi

# ========================================
# 6. GitHub CLI (optional but helpful)
# ========================================
echo ""
echo "🐙 Checking GitHub CLI..."

if command -v gh &> /dev/null; then
    echo "✅ gh (GitHub CLI) installed"
    
    if gh auth status &> /dev/null; then
        echo "✅ GitHub CLI authenticated"
    else
        echo "⚠️  GitHub CLI not authenticated"
        echo "   Run: gh auth login"
    fi
else
    echo "⚠️  GitHub CLI not installed (optional)"
    echo "   Install: sudo dnf install gh"
    echo "   Then: gh auth login"
fi

# ========================================
# 7. Create helper scripts
# ========================================
echo ""
echo "📝 Creating helper scripts..."

# Quick commit & push script
cat > quick_commit.sh << 'SCRIPT_EOF'
#!/bin/bash
# Quick commit and push without prompts
set -e

if [ -z "$1" ]; then
    echo "Usage: ./quick_commit.sh \"commit message\""
    exit 1
fi

git add -A
git commit -m "$1"
git push

echo "✅ Committed and pushed: $1"
SCRIPT_EOF

chmod +x quick_commit.sh
echo "✅ Created quick_commit.sh"

# Dashboard update script
cat > update_dashboard.sh << 'SCRIPT_EOF'
#!/bin/bash
# Update dashboard data and refresh
set -e

echo "🔄 Updating BigQuery table..."
python3 build_publication_table_current.py

echo ""
echo "✅ BigQuery table updated!"
echo ""
echo "📊 Now refresh Google Sheets:"
echo "   1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit"
echo "   2. Make sure 'Live Dashboard' tab is active"
echo "   3. Click: GB Live Dashboard → Force Refresh Dashboard"
SCRIPT_EOF

chmod +x update_dashboard.sh
echo "✅ Created update_dashboard.sh"

# Deploy Apps Script
cat > deploy_apps_script.sh << 'SCRIPT_EOF'
#!/bin/bash
# Deploy Apps Script changes
set -e

cd /tmp/gb-live-2-final

echo "📤 Deploying to Apps Script..."
clasp push --force

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Open Apps Script editor:"
echo "   clasp open"
SCRIPT_EOF

chmod +x deploy_apps_script.sh
echo "✅ Created deploy_apps_script.sh"

# ========================================
# 8. Summary
# ========================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Configuration Files Created:"
echo "   ✓ .vscode/settings.json (VS Code settings)"
echo "   ✓ .git/config (Git configuration)"
echo "   ✓ quick_commit.sh (Quick git commit & push)"
echo "   ✓ update_dashboard.sh (Update BigQuery + instructions)"
echo "   ✓ deploy_apps_script.sh (Deploy to Apps Script)"
echo ""
echo "🔧 Manual Steps Needed:"
echo ""
echo "1️⃣  Git Authentication (for auto-push):"
echo "   - Go to: https://github.com/settings/tokens"
echo "   - Generate token with 'repo' scope"
echo "   - Run: git push"
echo "   - Enter token as password (saved to ~/.git-credentials)"
echo ""
echo "2️⃣  clasp Authentication (if not done):"
echo "   - Run: clasp login"
echo "   - Authorize in browser"
echo ""
echo "3️⃣  GitHub CLI (optional, for better git integration):"
echo "   - Run: gh auth login"
echo "   - Follow prompts"
echo ""
echo "💡 Quick Usage:"
echo "   ./quick_commit.sh \"Your commit message\""
echo "   ./update_dashboard.sh"
echo "   ./deploy_apps_script.sh"
echo ""
echo "📖 Full documentation: GB_LIVE_DASHBOARD_COMPLETE.md"
echo ""
