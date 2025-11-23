# VS Code Multi-Machine Setup Guide
**Sync VS Code Settings Between iMac & Dell Server**

## Quick Answer to Your Questions

### Q1: Will this be included in all VS Code folders/repos (current and new)?

**Answer**: The `setup_vscode.py` script creates **workspace-specific** settings in `.vscode/` folder:

```
GB Power Market JJ/
├── .vscode/
│   ├── settings.json      ← Project-specific settings
│   └── launch.json         ← Debug configs for THIS project
```

**What gets created:**
- ✅ **Per-project** settings in `.vscode/` folder (tracked in Git)
- ✅ Extensions are installed **globally** (all projects use them)
- ✅ Test script `test_bigquery_vscode.py` in THIS project only

**For new repos:**
- Extensions: Already installed (available everywhere)
- Settings: Need to run script again OR copy `.vscode/` folder OR use Settings Sync (see below)

---

## Setup Architecture: What Goes Where

### 🏢 Global (All Projects - Installed Once)

**Extensions** (installed by script Step 3):
```bash
# These are available to ALL projects after installation:
- ms-python.python            # Python extension
- ms-python.vscode-pylance     # IntelliSense
- ms-toolsai.jupyter           # Jupyter notebooks
- eamodio.gitlens              # Git integration
- njpwerner.autodocstring      # Docstring generator
```

**Location**: `~/.vscode/extensions/` (Mac) or `~/.vscode-server/extensions/` (SSH)

### 📁 Per-Project (This Repo Only)

**Workspace Settings** (created by script Steps 4-5):
```
.vscode/settings.json   # Python interpreter, linting, formatting
.vscode/launch.json     # Debug configurations with BigQuery env vars
test_bigquery_vscode.py # Test script for this project
```

**Location**: `GB Power Market JJ/.vscode/`

**Git Tracking**: ✅ Committed to repo (tracked in `.gitignore` as allowed)

---

## Your Specific Setup: iMac → Dell Server

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Your iMac (Local)                     │
│  - Development machine                                   │
│  - VS Code installed locally                             │
│  - Extensions installed locally                          │
│  - Edit files, commit to Git                             │
└───────────────────────────┬─────────────────────────────┘
                            │
                            │ SSH Connection
                            │
┌───────────────────────────▼─────────────────────────────┐
│              Dell Server (94.237.55.234)                 │
│  - AlmaLinux                                             │
│  - IRIS pipeline runs here                               │
│  - VS Code connects via Remote-SSH                       │
│  - Extensions auto-install on server                     │
└──────────────────────────────────────────────────────────┘
```

### Option 1: Remote-SSH (Recommended for Server Work)

**What it does**: Your iMac's VS Code connects to Dell server, edits files remotely

**Setup Steps:**

#### Step 1: Install Remote-SSH Extension (iMac)
```bash
# On your iMac, run:
code --install-extension ms-vscode-remote.remote-ssh
```

#### Step 2: Configure SSH Connection
```bash
# On iMac, edit SSH config:
nano ~/.ssh/config
```

Add this configuration:
```ssh-config
Host dell-iris
    HostName 94.237.55.234
    User root
    IdentityFile ~/.ssh/id_rsa
    ForwardAgent yes
```

#### Step 3: Connect to Dell via VS Code

1. **Open VS Code on iMac**
2. Press `Cmd+Shift+P`
3. Type: `Remote-SSH: Connect to Host`
4. Select: `dell-iris`
5. VS Code opens new window connected to Dell server

#### Step 4: Install Extensions on Remote (First Time Only)

When connected via Remote-SSH, VS Code shows:
```
SSH: dell-iris (bottom-left corner)
```

Extensions need to be installed on remote:
```bash
# In VS Code terminal (connected to Dell):
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-toolsai.jupyter
```

Or use the Extensions panel: Click "Install in SSH: dell-iris"

#### Step 5: Open Project on Dell
```bash
# In VS Code (connected to Dell):
File → Open Folder → /opt/iris-pipeline/
# Or wherever your project lives on Dell
```

**Benefits:**
- ✅ Edit Dell files directly from iMac
- ✅ Run commands on Dell server
- ✅ Debug Python scripts on Dell
- ✅ Access Dell's file system
- ✅ Extensions run on Dell (have access to Dell's Python, credentials)

---

### Option 2: Settings Sync (For Local Projects)

**What it does**: Sync VS Code settings, extensions, keybindings between machines

**Setup Steps:**

#### Step 1: Enable Settings Sync (iMac)
1. Open VS Code
2. Press `Cmd+Shift+P`
3. Type: `Settings Sync: Turn On`
4. Choose: **Sign in with GitHub**
5. Select what to sync:
   - ✅ Settings
   - ✅ Extensions
   - ✅ Keyboard Shortcuts
   - ✅ User Snippets
   - ❌ UI State (optional)

#### Step 2: Enable on Other Machines
On any other machine (including Dell if you install VS Code there):
1. Open VS Code
2. `Cmd+Shift+P` → `Settings Sync: Turn On`
3. Sign in with same GitHub account
4. All settings/extensions download automatically

**What Gets Synced:**
- ✅ **User settings** (`~/.config/Code/User/settings.json`)
- ✅ **Extensions list** (auto-installs everywhere)
- ✅ **Keybindings**
- ❌ **NOT workspace settings** (`.vscode/settings.json` - use Git instead)

---

### Option 3: Git-Based Sync (For Workspace Settings)

**What it does**: Track `.vscode/` folder in Git, pull on other machines

**Already Done by Script:**
The `setup_vscode.py` script updates `.gitignore`:
```gitignore
# VS Code
.vscode/*
!.vscode/settings.json    # ← Track this
!.vscode/launch.json      # ← Track this
!.vscode/extensions.json  # ← Track this
```

**Usage:**

On iMac (after running script):
```bash
cd "GB Power Market JJ"
git add .vscode/settings.json .vscode/launch.json
git commit -m "Add VS Code workspace settings"
git push origin main
```

On Dell (or any other machine):
```bash
cd /path/to/project
git pull origin main
# Now you have .vscode/ settings!
```

---

## Complete Setup: iMac + Dell Workflow

### Phase 1: Setup iMac (Local Development)

**Step 1: Run Setup Script (Current Project)**
```bash
# In "GB Power Market JJ" folder on iMac:
python3 setup_vscode.py
# Answer 'y' to install VS Code, extensions, etc.
```

**Step 2: Commit Workspace Settings to Git**
```bash
git add .vscode/ test_bigquery_vscode.py .gitignore
git commit -m "Add VS Code workspace configuration"
git push origin main
```

**Step 3: Enable Settings Sync (Optional - for user preferences)**
```bash
# In VS Code:
Cmd+Shift+P → "Settings Sync: Turn On" → Sign in with GitHub
```

### Phase 2: Setup Dell Server (Remote Development)

**Option A: Remote-SSH (Recommended)**

**Step 1: Install Remote-SSH on iMac**
```bash
code --install-extension ms-vscode-remote.remote-ssh
```

**Step 2: Configure SSH**
```bash
# On iMac:
nano ~/.ssh/config
```
```ssh-config
Host dell-iris
    HostName 94.237.55.234
    User root
```

**Step 3: Connect**
```bash
# In VS Code on iMac:
Cmd+Shift+P → "Remote-SSH: Connect to Host" → dell-iris
```

**Step 4: Open Project on Dell**
```bash
# In remote VS Code window:
File → Open Folder → /opt/iris-pipeline/GB-Power-Market-JJ/
```

**Step 5: Pull Latest Code (includes .vscode/)**
```bash
# In remote VS Code terminal:
git pull origin main
```

Extensions install automatically on first connection!

---

**Option B: Native VS Code on Dell (If you want GUI on Dell)**

Only if Dell has desktop environment (not typical for servers):
```bash
# On Dell server:
# Install VS Code
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'
sudo dnf install code

# Clone repo
cd /opt/iris-pipeline/
git clone https://github.com/GeorgeDoors888/GB-Power-Market-JJ.git
cd GB-Power-Market-JJ

# Run setup script
python3 setup_vscode.py
```

---

## What Happens When You Run Script on Dell

When you run `setup_vscode.py` on Dell server:

### ✅ Will Work:
- Extension installation (globally available)
- `.vscode/settings.json` creation
- `.vscode/launch.json` creation
- `test_bigquery_vscode.py` creation

### ⚠️ May Need Adjustment:
- VS Code installation (uses Homebrew - Mac/Linux package manager)
  - For AlmaLinux: Use `dnf install code` instead
  - Or skip (use Remote-SSH from iMac instead)

### 📝 Credentials Path:
Script sets paths in `launch.json`:
```json
"env": {
  "GOOGLE_APPLICATION_CREDENTIALS": "/root/.google-credentials/inner-cinema-credentials.json"
}
```

Make sure credentials exist on Dell at that path!

---

## Recommended Setup for Your Use Case

Based on your architecture (iMac + Dell server):

### 🎯 Best Approach: Hybrid

**iMac (Local Development):**
1. ✅ Run `setup_vscode.py` on iMac NOW
2. ✅ Install Remote-SSH extension
3. ✅ Enable Settings Sync for user preferences
4. ✅ Commit `.vscode/` to Git

**Dell Server (Remote Work):**
1. ✅ Use Remote-SSH from iMac (don't install VS Code on Dell)
2. ✅ Extensions auto-install when you connect
3. ✅ Pull Git repo (includes `.vscode/` settings)

**Benefits:**
- Edit Dell files from comfortable iMac setup
- No GUI needed on Dell server
- Same extensions/settings everywhere via Settings Sync
- Project-specific configs via Git (`.vscode/`)

---

## Testing Your Setup

### Test 1: iMac Local Setup
```bash
# On iMac in "GB Power Market JJ" folder:
python3 test_bigquery_vscode.py
# Should show: ✅ BigQuery connected!
```

### Test 2: Remote-SSH to Dell
```bash
# In VS Code on iMac:
1. Cmd+Shift+P → "Remote-SSH: Connect to Host" → dell-iris
2. File → Open Folder → /opt/iris-pipeline/GB-Power-Market-JJ/
3. Open terminal (Ctrl+`): pwd
   # Should show: /opt/iris-pipeline/GB-Power-Market-JJ
4. python3 test_bigquery_vscode.py
   # Should work if credentials are on Dell
```

---

## Syncing New Repos

### When You Create/Clone a New Repo:

**Method 1: Copy .vscode/ from existing project**
```bash
# In new repo:
cp -r "../GB Power Market JJ/.vscode" .
# Edit paths in launch.json if needed
```

**Method 2: Run setup script again**
```bash
# In new repo:
cp "../GB Power Market JJ/setup_vscode.py" .
python3 setup_vscode.py
```

**Method 3: Use template**
```bash
# Create once, reuse everywhere:
~/vscode-template/
  .vscode/
    settings.json
    launch.json

# In new repo:
cp -r ~/vscode-template/.vscode .
```

Extensions are already installed globally - no reinstall needed!

---

## Quick Reference: Connection Methods

| Method | Use Case | Setup Complexity | Best For |
|--------|----------|------------------|----------|
| **Remote-SSH** | Edit Dell files from iMac | Medium | Server work, remote debugging |
| **Settings Sync** | Sync user preferences | Easy | Personal settings across machines |
| **Git (.vscode/)** | Share project settings | Easy | Team collaboration, project configs |
| **Manual Copy** | One-time setup | Easy | Quick project setup |

---

## Troubleshooting

### Issue: Extensions Not Installing on Dell via Remote-SSH

**Solution:**
```bash
# In remote VS Code terminal:
code --install-extension ms-python.python
# Or use Extensions panel: Click "Install in SSH: dell-iris"
```

### Issue: Credentials Not Found on Dell

**Solution:**
```bash
# On Dell server:
mkdir -p ~/.google-credentials
# Copy credentials from iMac:
scp ~/.google-credentials/inner-cinema-credentials.json root@94.237.55.234:~/.google-credentials/

# Verify:
ls -la ~/.google-credentials/
```

### Issue: Python Interpreter Not Found on Dell

**Solution:**
```bash
# Find Python on Dell:
which python3

# Update .vscode/settings.json:
{
  "python.defaultInterpreterPath": "/usr/bin/python3"  # Use Dell's path
}
```

---

## Summary: What Gets Shared How

```
╔══════════════════════════════════════════════════════════╗
║               VS Code Component Sharing                  ║
╠══════════════════════════════════════════════════════════╣
║ Component           │ Sharing Method    │ Scope          ║
╠═════════════════════╪═══════════════════╪════════════════╣
║ Extensions          │ Settings Sync     │ All machines   ║
║ User Settings       │ Settings Sync     │ All machines   ║
║ Workspace Settings  │ Git (.vscode/)    │ Per project    ║
║ Debug Configs       │ Git (.vscode/)    │ Per project    ║
║ Credentials         │ Manual copy       │ Per machine    ║
║ Python Packages     │ pip/requirements  │ Per environment║
╚═════════════════════╧═══════════════════╧════════════════╝
```

---

## Next Steps

**Right Now (iMac):**
```bash
# 1. Run setup script (creates .vscode/ in current project)
python3 setup_vscode.py

# 2. Commit to Git
git add .vscode/ test_bigquery_vscode.py
git commit -m "Add VS Code workspace configuration"
git push origin main

# 3. Install Remote-SSH
code --install-extension ms-vscode-remote.remote-ssh

# 4. Test local
python3 test_bigquery_vscode.py
```

**Then (Dell Connection):**
```bash
# 5. Configure SSH (on iMac)
nano ~/.ssh/config  # Add dell-iris host

# 6. Connect via Remote-SSH
# Cmd+Shift+P → "Remote-SSH: Connect to Host" → dell-iris

# 7. Pull repo on Dell
# File → Open Folder → /opt/iris-pipeline/GB-Power-Market-JJ/
# Terminal: git pull origin main

# 8. Test remote
# python3 test_bigquery_vscode.py
```

---

**Questions? Check:**
- `VSCODE_SETUP_GUIDE.md` - Full VS Code tutorial
- `GOOGLE_WORKSPACE_UNIVERSAL_SETUP.md` - Credentials management
- `BEGINNERS_GUIDE_CHATGPT_BIGQUERY.md` - System overview

**Last Updated**: November 19, 2025
