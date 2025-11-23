# 💻 VS Code Setup Guide for GB Power Market Project

**For**: George Major (Novice)  
**Purpose**: How to use VS Code for Python development with BigQuery and ChatGPT integration  
**Level**: Complete beginner-friendly

---

## 📋 Table of Contents

1. [Why VS Code?](#why-vs-code)
2. [Initial Setup](#initial-setup)
3. [Essential Extensions](#essential-extensions)
4. [Opening Your Project](#opening-your-project)
5. [Working with Python](#working-with-python)
6. [Testing BigQuery Connections](#testing-bigquery-connections)
7. [Using the Integrated Terminal](#using-the-integrated-terminal)
8. [Git Integration](#git-integration)
9. [Tips & Tricks](#tips--tricks)
10. [Troubleshooting](#troubleshooting)

---

## Why VS Code?

**VS Code** (Visual Studio Code) is a free code editor that makes Python development easier:

✅ **Syntax highlighting** - Colors make code readable  
✅ **Auto-completion** - Suggests code as you type  
✅ **Built-in terminal** - Run scripts without leaving VS Code  
✅ **Git integration** - Commit changes visually  
✅ **Debugging** - Find and fix errors easily  
✅ **Extensions** - Add Python, BigQuery, and ChatGPT tools

---

## Initial Setup

### Step 1: Install VS Code

1. Go to: https://code.visualstudio.com/
2. Click "Download for Mac"
3. Open the downloaded file
4. Drag VS Code to Applications folder
5. Open VS Code from Applications

**First launch**: VS Code might ask for permissions - click "Allow" for everything.

### Step 2: Install Command Line Tools

Open VS Code and press **`Cmd+Shift+P`** (opens Command Palette):

1. Type: `shell command`
2. Select: **"Shell Command: Install 'code' command in PATH"**
3. Click it

**What this does**: Lets you open VS Code from Terminal with `code .`

### Step 3: Configure Python Interpreter

1. Open Command Palette: **`Cmd+Shift+P`**
2. Type: `Python: Select Interpreter`
3. Choose: **`Python 3.14.x`** (the latest version on your Mac)

**If you don't see Python**:
```bash
# In VS Code Terminal (Ctrl+`)
which python3
# This shows where Python is installed
```

---

## Essential Extensions

### Must-Have Extensions (Install These)

Click the Extensions icon (square blocks on left sidebar) or press **`Cmd+Shift+X`**

#### 1. **Python** (by Microsoft)
- **What**: Python language support
- **Features**: Syntax highlighting, IntelliSense, debugging
- **Install**: Search "Python" → Click "Install" on Microsoft's version

#### 2. **Pylance** (by Microsoft)
- **What**: Fast Python language server
- **Features**: Better auto-completion, type checking
- **Install**: Search "Pylance" → Install (may auto-install with Python)

#### 3. **Jupyter** (by Microsoft)
- **What**: Run Jupyter notebooks in VS Code
- **Features**: Interactive Python cells, data visualization
- **Install**: Search "Jupyter" → Install

#### 4. **autoDocstring** (by Nils Werner)
- **What**: Generate Python docstrings automatically
- **Features**: Type `"""` and it creates template
- **Install**: Search "autoDocstring" → Install

#### 5. **GitHub Copilot** (by GitHub) - Optional but Amazing
- **What**: AI-powered code suggestions
- **Features**: Suggests entire functions, explains code
- **Cost**: Free for students/educators, $10/month otherwise
- **Install**: Search "GitHub Copilot" → Install → Sign in

### Recommended Extensions (Nice to Have)

#### 6. **GitLens** (by GitKraken)
- **What**: Supercharged Git integration
- **Features**: See who changed what line, when, why
- **Install**: Search "GitLens" → Install

#### 7. **Better Comments** (by Aaron Bond)
- **What**: Color-coded comments
- **Features**: Highlights TODO, FIXME, etc.
- **Install**: Search "Better Comments" → Install

#### 8. **Path Intellisense** (by Christian Kohler)
- **What**: Auto-completes file paths
- **Features**: Type `./` and see file suggestions
- **Install**: Search "Path Intellisense" → Install

#### 9. **Markdown All in One** (by Yu Zhang)
- **What**: Better markdown editing (for .md files)
- **Features**: Preview, formatting, table of contents
- **Install**: Search "Markdown All in One" → Install

---

## Opening Your Project

### Method 1: From Finder

1. Right-click your project folder: `GB Power Market JJ`
2. **Services** → **Open in Visual Studio Code**

### Method 2: From Terminal

```bash
cd ~/GB\ Power\ Market\ JJ
code .
```

**The `.` means "current directory"**

### Method 3: From VS Code

1. Open VS Code
2. **File** → **Open Folder...**
3. Navigate to `GB Power Market JJ`
4. Click **Open**

### What You'll See

```
VS Code Layout:
┌─────────────────────────────────────────────────────┐
│  File  Edit  View  ...                 [×] [−] [□]  │
├──────┬──────────────────────────────────────────────┤
│      │  EXPLORER                                    │
│  📁  │  ├── 📁 .github                              │
│  🔍  │  ├── 📁 codex-server                         │
│  🔀  │  ├── 📁 docs                                 │
│  🐛  │  ├── 📁 vercel-proxy                         │
│  ⚙️   │  ├── 📄 api_gateway.py                      │
│      │  ├── 📄 pub_endpoints.py                     │
│      │  ├── 📄 README.md                            │
│      │  └── ...                                     │
├──────┼──────────────────────────────────────────────┤
│      │  [Code Editor - Opens here]                  │
│      │                                              │
│      │                                              │
├──────┴──────────────────────────────────────────────┤
│  TERMINAL (Toggle: Ctrl+`)                          │
│  ~/GB Power Market JJ$                              │
└─────────────────────────────────────────────────────┘
```

---

## Working with Python

### Creating a New Python File

1. **Right-click** in Explorer → **New File**
2. Name it: `my_script.py` (must end in `.py`)
3. VS Code recognizes it as Python (icon changes)

### Writing Your First Script

```python
#!/usr/bin/env python3
"""
Test script for GB Power Market
"""

import os
from google.cloud import bigquery

# Configuration from environment
PROJECT_ID = os.getenv("GCP_PROJECT")
DATASET = os.getenv("BQ_DATASET")

print(f"🔍 Testing BigQuery connection...")
print(f"   Project: {PROJECT_ID}")
print(f"   Dataset: {DATASET}")

# Create client
client = bigquery.Client(project=PROJECT_ID, location="US")

# Simple query
query = f"""
SELECT 
    DATE(settlementDate) as date,
    AVG(price) as avg_price
FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
WHERE settlementDate >= '2025-11-01'
GROUP BY date
ORDER BY date DESC
LIMIT 7
"""

print(f"\n📊 Running query...")
df = client.query(query).to_dataframe()

print(f"\n✅ Success! Retrieved {len(df)} rows:")
print(df)
```

### Auto-Completion Features

**As you type, VS Code suggests**:

```python
# Type: bigquery.
# VS Code shows: Client, QueryJobConfig, SchemaField...

# Type: df.
# VS Code shows: head(), tail(), describe()...

# Press Tab or Enter to accept suggestion
```

### Running Your Script

**Method 1: Run Button (Top Right)**
- Click the **▷ Run Python File** button
- Output appears in Terminal

**Method 2: Right-Click Menu**
- Right-click in editor → **Run Python File in Terminal**

**Method 3: Keyboard Shortcut**
- Press **`Ctrl+Option+N`** (or configure your own)

**Method 4: Terminal**
```bash
# Open Terminal: Ctrl+`
python3 my_script.py
```

### Debugging Python Code

#### Set a Breakpoint

1. Click in the **gutter** (left of line numbers)
2. Red dot appears = breakpoint
3. Press **`F5`** to start debugging
4. Code pauses at breakpoint

#### Debug Controls

```
F5       - Start/Continue debugging
F10      - Step Over (next line)
F11      - Step Into (enter function)
Shift+F11 - Step Out (exit function)
Shift+F5  - Stop debugging
```

#### Debug Panel (Left Sidebar)

Shows:
- **Variables**: Current values
- **Watch**: Monitor specific variables
- **Call Stack**: Where you are in code
- **Breakpoints**: All breakpoints listed

---

## Testing BigQuery Connections

### Create a Test File

**File**: `test_bigquery_vscode.py`

```python
#!/usr/bin/env python3
"""
VS Code BigQuery Connection Test
Tests that credentials work from VS Code environment
"""

import os
import sys

def check_environment():
    """Check environment variables are set"""
    print("🔍 Checking environment variables...\n")
    
    required = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GCP_PROJECT',
        'BQ_DATASET',
        'BQ_LOCATION'
    ]
    
    missing = []
    for var in required:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value[:50]}...")
        else:
            print(f"   ❌ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\n❌ Missing variables: {', '.join(missing)}")
        print("   Fix: Run 'source ~/.zshrc' in VS Code terminal")
        return False
    
    return True

def test_bigquery():
    """Test BigQuery connection"""
    print("\n📊 Testing BigQuery connection...\n")
    
    try:
        from google.cloud import bigquery
        
        client = bigquery.Client(
            project=os.getenv('GCP_PROJECT'),
            location=os.getenv('BQ_LOCATION')
        )
        
        # Simple test query
        query = f"""
        SELECT COUNT(*) as row_count
        FROM `{os.getenv('GCP_PROJECT')}.{os.getenv('BQ_DATASET')}.bmrs_mid`
        LIMIT 1
        """
        
        result = client.query(query).result()
        for row in result:
            print(f"   ✅ BigQuery connected!")
            print(f"   📈 bmrs_mid table has {row.row_count:,} rows")
        
        return True
        
    except Exception as e:
        print(f"   ❌ BigQuery connection failed:")
        print(f"   {str(e)}")
        return False

def test_pandas():
    """Test pandas integration"""
    print("\n🐼 Testing pandas DataFrame...\n")
    
    try:
        from google.cloud import bigquery
        import pandas as pd
        
        client = bigquery.Client(
            project=os.getenv('GCP_PROJECT'),
            location=os.getenv('BQ_LOCATION')
        )
        
        query = f"""
        SELECT 
            DATE(settlementDate) as date,
            AVG(price) as avg_price
        FROM `{os.getenv('GCP_PROJECT')}.{os.getenv('BQ_DATASET')}.bmrs_mid`
        WHERE settlementDate >= '2025-11-01'
        GROUP BY date
        ORDER BY date DESC
        LIMIT 5
        """
        
        df = client.query(query).to_dataframe()
        
        print(f"   ✅ DataFrame created with {len(df)} rows:")
        print(df.to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"   ❌ Pandas test failed:")
        print(f"   {str(e)}")
        return False

if __name__ == "__main__":
    print("╔════════════════════════════════════════════════╗")
    print("║  VS Code BigQuery Connection Test             ║")
    print("╚════════════════════════════════════════════════╝\n")
    
    # Run tests
    env_ok = check_environment()
    if not env_ok:
        sys.exit(1)
    
    bq_ok = test_bigquery()
    if not bq_ok:
        sys.exit(1)
    
    pandas_ok = test_pandas()
    if not pandas_ok:
        sys.exit(1)
    
    print("\n╔════════════════════════════════════════════════╗")
    print("║  ✅ ALL TESTS PASSED!                         ║")
    print("║  VS Code is ready for BigQuery development    ║")
    print("╚════════════════════════════════════════════════╝\n")
```

### Run the Test

1. Save file: **`Cmd+S`**
2. Click **▷ Run** or press **`Ctrl+Option+N`**
3. Check Terminal output

**Expected**: All ✅ green checkmarks

---

## Using the Integrated Terminal

### Open Terminal

**Press**: **`Ctrl+`** (Control + Backtick)

**Or**: **View** → **Terminal**

### Why Use VS Code Terminal?

✅ **Stay in one app** - No switching to separate Terminal  
✅ **Environment auto-loaded** - ~/.zshrc already sourced  
✅ **Multiple terminals** - Click + to open more  
✅ **Split terminals** - View multiple at once  

### Terminal Features

#### Multiple Terminals

```
Click [+] to create new terminal
Click [trash] to close terminal
Click dropdown to switch between terminals
```

#### Split Terminal

1. Click **split icon** (two rectangles)
2. Now have side-by-side terminals
3. Run script in one, watch logs in other

#### Terminal Commands

```bash
# Navigate
cd ~/GB\ Power\ Market\ JJ

# List files
ls -la

# Run Python scripts
python3 analyze_battery_vlp_final.py

# Git commands
git status
git add .
git commit -m "Updated analysis"
git push

# SSH to servers
ssh root@94.237.55.234
```

---

## Git Integration

### Opening Source Control

**Click**: Source Control icon (branches icon on left) or **`Ctrl+Shift+G`**

### Making Changes

#### 1. See What Changed

```
Source Control Panel shows:
M  api_gateway.py        (Modified)
A  new_script.py         (Added)
D  old_file.py          (Deleted)
```

#### 2. Stage Changes

- **Click +** next to file to stage it
- **Or click + next to "Changes"** to stage all

#### 3. Commit

1. Type commit message in text box
2. Click **✓ Commit** button
3. Changes saved locally

#### 4. Push to GitHub

- Click **⋯** (more) → **Push**
- Or click **↑** sync icon

### Viewing Diff (Changes)

- Click a modified file in Source Control
- VS Code shows **side-by-side diff**:
  - **Left**: Old version (red)
  - **Right**: New version (green)

### Git Commands in Terminal

```bash
# Status
git status

# Stage all changes
git add .

# Commit
git commit -m "Added pub feature documentation"

# Push
git push origin main

# Pull latest
git pull
```

### .gitignore (Already Set Up)

Your project has `.gitignore` that excludes:

```
# VS Code will NOT commit these:
*.json               # Credential files
__pycache__/        # Python cache
.env                # Environment files
*.log               # Log files
node_modules/       # Node packages
```

**Always check**: Credentials are NOT staged before committing!

---

## Tips & Tricks

### Keyboard Shortcuts (Essential)

```
Cmd+S            - Save file
Cmd+P            - Quick open file (fuzzy search)
Cmd+Shift+P      - Command Palette (access all features)
Ctrl+`           - Toggle Terminal
Cmd+B            - Toggle Sidebar
Cmd+/            - Toggle comment
Cmd+Shift+F      - Search across all files
Cmd+Shift+H      - Replace across all files
Cmd+D            - Select next occurrence
Cmd+Shift+L      - Select all occurrences
Option+Up/Down   - Move line up/down
Shift+Option+Up/Down - Copy line up/down
Cmd+K Cmd+0      - Fold all code
Cmd+K Cmd+J      - Unfold all code
```

### Multi-Cursor Editing

1. **Hold `Option`** + **Click** = Add cursor
2. **Type once** = Types in all cursor locations
3. **Press `Esc`** = Back to single cursor

**Example**: Rename multiple variables at once

### Find and Replace

1. **Press `Cmd+H`**
2. **Type** what to find
3. **Type** what to replace with
4. **Click** replace one or replace all

### Zen Mode (Distraction-Free)

- **Press**: **`Cmd+K Z`**
- **Exit**: Press **`Esc Esc`**

### IntelliSense (Auto-Complete)

```python
# Start typing...
import pand

# VS Code suggests:
# ▼ pandas
#   pandas_gbq
#   ...

# Press Tab to accept
import pandas as pd
```

### Peek Definition

1. **Right-click** a function/variable
2. **Select**: **Peek Definition**
3. See definition in popup (without leaving your file)

Or: **`Option+F12`**

### Go to Definition

- **Click** function name while holding **`Cmd`**
- Or: **Right-click** → **Go to Definition**
- Or: **`F12`**

### Rename Symbol

1. **Right-click** variable/function
2. **Select**: **Rename Symbol**
3. **Type** new name
4. Press **Enter** - Renames everywhere!

Or: **`F2`**

---

## VS Code Settings for This Project

### Workspace Settings

**Create**: `.vscode/settings.json` in your project root:

```json
{
  "python.defaultInterpreterPath": "/usr/local/bin/python3",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "autopep8",
  "python.terminal.activateEnvironment": true,
  "editor.formatOnSave": false,
  "editor.rulers": [80, 120],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.DS_Store": true
  },
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "[python]": {
    "editor.tabSize": 4,
    "editor.insertSpaces": true
  },
  "[markdown]": {
    "editor.wordWrap": "on",
    "editor.quickSuggestions": false
  }
}
```

### Launch Configuration (Debugging)

**Create**: `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "${env:HOME}/.google-credentials/inner-cinema-credentials.json",
        "GCP_PROJECT": "inner-cinema-476211-u9",
        "BQ_DATASET": "uk_energy_prod"
      }
    },
    {
      "name": "Python: BigQuery Test",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/test_bigquery_vscode.py",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Troubleshooting

### Problem: "Python not found"

**Fix**:
1. **`Cmd+Shift+P`** → **Python: Select Interpreter**
2. Choose Python 3.14 or later
3. If not listed, click **Enter interpreter path...**
4. Enter: `/usr/local/bin/python3`

### Problem: "Module not found" when running script

**Cause**: VS Code terminal hasn't sourced ~/.zshrc

**Fix**:
```bash
# In VS Code Terminal (Ctrl+`)
source ~/.zshrc

# Or restart VS Code
Cmd+Q (quit)
Re-open VS Code
```

### Problem: Environment variables not set

**Check**:
```bash
# In VS Code Terminal
printenv | grep GOOGLE
```

**Fix if empty**:
1. Open Terminal (outside VS Code)
2. Run: `source ~/.zshrc`
3. Test: `printenv | grep GOOGLE`
4. **Restart VS Code** (Cmd+Q, re-open)

### Problem: Can't save file (permission denied)

**Cause**: Trying to edit system files

**Fix**: Edit files in your home directory only:
- ✅ `~/GB Power Market JJ/`
- ❌ `/opt/`, `/etc/`, `/usr/`

### Problem: Git asking for username/password repeatedly

**Fix**: Set up SSH keys (one-time):
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "george@upowerenergy.uk"

# Copy public key
cat ~/.ssh/id_ed25519.pub | pbcopy

# Add to GitHub:
# 1. GitHub.com → Settings → SSH Keys → New SSH Key
# 2. Paste key
# 3. Save

# Change remote to SSH
cd ~/GB\ Power\ Market\ JJ
git remote set-url origin git@github.com:GeorgeDoors888/GB-Power-Market-JJ.git
```

### Problem: Slow auto-complete

**Fix**: Disable Pylance type checking temporarily:
1. **`Cmd+Shift+P`**
2. **Preferences: Open Settings (JSON)**
3. Add: `"python.analysis.typeCheckingMode": "off"`

### Problem: Can't see .json credential files in Explorer

**Cause**: Might be filtered in settings

**Fix**:
1. **View** → **Show Hidden Files** (if available)
2. Or in Finder, go to folder and drag into VS Code

---

## Common Workflows

### Workflow 1: Write New Analysis Script

1. **Create file**: `new_analysis.py`
2. **Copy template** from `GOOGLE_WORKSPACE_UNIVERSAL_SETUP.md`
3. **Write query**
4. **Run with** `F5` (debug) or **▷ Run**
5. **Check output** in Terminal
6. **Commit changes**: Source Control → Commit → Push

### Workflow 2: Edit Existing Script

1. **`Cmd+P`** → Type filename → Enter
2. **Make changes**
3. **Save**: `Cmd+S`
4. **Test**: Click ▷ Run
5. **If works**: Commit via Source Control

### Workflow 3: Debug Script with Errors

1. **Set breakpoint** at error line (click gutter)
2. **Press `F5`** to start debugging
3. **Hover over variables** to see values
4. **Step through** with `F10`
5. **Fix issue**
6. **Run again**

### Workflow 4: Search Entire Project

1. **`Cmd+Shift+F`** (Search)
2. **Type search term**: e.g., `bmrs_mid`
3. See all files containing it
4. Click result to open file

### Workflow 5: Update Dashboard Script

1. Open: `update_analysis_bi_enhanced.py`
2. Edit query or logic
3. Test locally: `python3 update_analysis_bi_enhanced.py`
4. If works, deploy to server:
   ```bash
   scp update_analysis_bi_enhanced.py root@94.237.55.15:/opt/arbitrage/
   ssh root@94.237.55.15 'cd /opt/arbitrage && python3 update_analysis_bi_enhanced.py'
   ```

---

## Advanced: Remote Development (SSH to Server)

### Install Remote-SSH Extension

1. **`Cmd+Shift+X`** → Search **"Remote - SSH"**
2. **Install** by Microsoft

### Connect to Server

1. **`Cmd+Shift+P`** → **Remote-SSH: Connect to Host...**
2. **Enter**: `root@94.237.55.234`
3. **Or**: `root@94.237.55.15`
4. VS Code opens new window connected to server
5. **Open folder**: `/opt/iris-pipeline/` or `/opt/arbitrage/`

### Edit Files on Server

- Files load in VS Code
- Edit like local files
- Save directly to server
- Run scripts in server's Terminal

**Benefits**:
- No scp needed
- Real-time editing
- Server environment

---

## Summary: Your VS Code Setup

### ✅ What You Have

- **VS Code installed** with Python support
- **Essential extensions**: Python, Pylance, Jupyter
- **Environment configured**: Credentials auto-loaded
- **Git integrated**: Commit/push visually
- **Debugging ready**: Breakpoints, variable inspection
- **Terminal built-in**: No app switching

### 🎯 Daily Workflow

1. **Open project**: `code ~/GB\ Power\ Market\ JJ`
2. **Open file**: `Cmd+P` → type name
3. **Edit code**: Auto-complete helps you
4. **Run script**: Click ▷ or `F5`
5. **Check output**: Terminal shows results
6. **Commit changes**: Source Control panel
7. **Push to GitHub**: Click sync icon

### 📚 Keep Learning

**VS Code Docs**: https://code.visualstudio.com/docs  
**Python in VS Code**: https://code.visualstudio.com/docs/python/python-tutorial  
**Keyboard Shortcuts**: **`Cmd+K Cmd+S`** in VS Code

---

**Created**: November 19, 2025  
**For**: George Major (GB Power Market JJ)  
**Status**: ✅ Ready to use  
**Next**: Open VS Code and run `test_bigquery_vscode.py`!
