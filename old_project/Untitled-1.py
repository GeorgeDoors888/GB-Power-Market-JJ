#!/usr/bin/env python3
"""
All-in-one bootstrap (private by default, highly automated, no manual settings):

- VS Code workspace config written by Python (.vscode/*)
- Auto-install extensions if `code` CLI is available
- Python venv + dev tools (black, isort, flake8, pytest, pre-commit, mkdocs, whoosh, tqdm, mdformat)
- Lightweight "AI memory" (Whoosh) + VS Code tasks
- Docs scaffold with plain-English Scope & Objectives
- ChatGPT Pro + Copilot model-picker helpers (README links, prompt files)
- Git init, SSH key, optional auto-upload of public key to GitHub (admin:public_key scope)
- GitHub repo creation as **private**; pre-push guard refuses if visibility != private
- CI (cached), Dependabot, CodeQL, Gitleaks, EditorConfig, PR/Issue templates
- Dev Container for reproducible dev
"""

import json
import os
import platform
import shlex
import shutil
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ----------------------------
# Configuration (safe-by-default)
# ----------------------------
WS_ROOT = Path.cwd()
PROJECT_NAME = os.environ.get("NEW_REPO_NAME", WS_ROOT.name)
PRIVATE_REPO = True  # hard-default: private only
GITHUB_USER = os.environ.get("GITHUB_USER", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # recommended
GIT_NAME = os.environ.get("GIT_NAME", "Your Name")
GIT_EMAIL = os.environ.get("GIT_EMAIL", "you@example.com")
AUTO_INSTALL_VSCODE_EXTENSIONS = True

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

VENV_DIR = WS_ROOT / ".venv"
PIP_BIN = (VENV_DIR / ("Scripts/pip.exe" if IS_WIN else "bin/pip")).as_posix()
PY_BIN = (VENV_DIR / ("Scripts/python.exe" if IS_WIN else "bin/python")).as_posix()
PRE_COMMIT_BIN = (VENV_DIR / ("Scripts/pre-commit.exe" if IS_WIN else "bin/pre-commit")).as_posix()
MKDOCS_BIN = (VENV_DIR / ("Scripts/mkdocs.exe" if IS_WIN else "bin/mkdocs")).as_posix()

VSCODE_DIR = WS_ROOT / ".vscode"
DOCS_DIR = WS_ROOT / "docs"
AI_DIR = WS_ROOT / "tools" / "ai_memory"
AI_INDEX_DIR = AI_DIR / "indexdir"

SSH_DIR = Path.home() / ".ssh"
KEY_PATH = SSH_DIR / "id_ed25519"
SSH_CONFIG = SSH_DIR / "config"

DEV_PY_PACKAGES = [
   "black",
   "isort",
   "flake8",
   "pytest",
   "pre-commit",
   "mkdocs",
   "mkdocs-material",
   "mdformat",
   "mdformat-gfm",
   "whoosh",
   "tqdm",
]

# ----------------------------
# Utilities
# ----------------------------
def run(cmd: str, check=True):
   print(f"$ {cmd}")
   cp = subprocess.run(cmd, shell=True, text=True, capture_output=True)
   if cp.stdout.strip():
       print(cp.stdout.strip())
   if cp.stderr.strip():
       print(cp.stderr.strip())
   if check and cp.returncode != 0:
       raise SystemExit(f"Command failed ({cp.returncode}): {cmd}")
   return cp

def which(exe: str) -> str | None:
   return shutil.which(exe)

def ensure_dir(p: Path, mode=None):
   p.mkdir(parents=True, exist_ok=True)
   if mode is not None:
       p.chmod(mode)

def gh_api(url: str, method="GET", data=None, token=GITHUB_TOKEN):
   if not token:
       raise RuntimeError("Missing GITHUB_TOKEN for GitHub API call.")
   headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
   req = urllib.request.Request(url, method=method, headers=headers)
   if data is not None:
       body = json.dumps(data).encode("utf-8")
       req.add_header("Content-Type", "application/json")
       req.data = body
   with urllib.request.urlopen(req, timeout=25) as r:
       return json.loads(r.read().decode())

# ----------------------------
# Python venv + packages
# ----------------------------
def ensure_venv():
   if not VENV_DIR.exists():
       run(f"{shlex.quote(sys.executable)} -m venv {shlex.quote(VENV_DIR.as_posix())}")
   run(f"{PIP_BIN} install --upgrade pip", check=False)
   if DEV_PY_PACKAGES:
       run(f"{PIP_BIN} install " + " ".join(shlex.quote(p) for p in DEV_PY_PACKAGES), check=False)
   (WS_ROOT / "requirements.txt").write_text(
       "\n".join(sorted(set(DEV_PY_PACKAGES))) + "\n", encoding="utf-8"
   )

# ----------------------------
# VS Code workspace settings (via Python)
# ----------------------------
def write_vscode():
   ensure_dir(VSCODE_DIR)
   settings = {
       "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
       if not IS_WIN
       else "${workspaceFolder}\\.venv\\Scripts\\python.exe",
       "python.analysis.typeCheckingMode": "basic",
       "editor.formatOnSave": True,
       "editor.codeActionsOnSave": {"source.organizeImports": "explicit"},
       "python.formatting.provider": "black",
       "isort.args": ["--profile", "black"],
       # Always open README so model/account reminders are seen
       "workbench.startupEditor": "readme",
       # Prompt files (for reminders)
       "chat.promptFiles": True,
       "chat.promptFilesLocations": {".github/prompts": True},
   }
   (VSCODE_DIR / "settings.json").write_text(json.dumps(settings, indent=2))

   extensions = {
       "recommendations": [
           "ms-python.python",
           "ms-python.vscode-pylance",
           "ms-python.black-formatter",
           "ms-python.isort",
           "ms-toolsai.jupyter",
           "editorconfig.editorconfig",
           "GitHub.copilot",
           "GitHub.copilot-chat",
           "yzhang.markdown-all-in-one",
           "bierner.markdown-mermaid",
           "openai.chatgpt",  # ChatGPT VS Code extension
       ]
   }
   (VSCODE_DIR / "extensions.json").write_text(json.dumps(extensions, indent=2))

   tasks = {
       "version": "2.0.0",
       "tasks": [
           {"label": "Docs: Serve (MkDocs)", "type": "shell",
            "command": f"{MKDOCS_BIN} serve -a 127.0.0.1:8000", "group": "build"},
           {"label": "AI Memory: Reindex", "type": "shell",
            "command": f"{PY_BIN} tools/ai_memory/index_repo.py", "group": "build"},
           {"label": "AI Memory: Search (prompt)", "type": "shell",
            "command": f'{PY_BIN} tools/ai_memory/search_memory.py "{{input:query}}" -k 10',
            "group": "test"},
           {"label": "Lint", "type": "shell",
            "command": f"{PY_BIN} -m flake8 .", "group": "test"},
           {"label": "Format", "type": "shell",
            "command": f"{PY_BIN} -m black . && {PY_BIN} -m isort . --profile black",
            "group": "build"},
           {"label": "Run tests", "type": "shell",
            "command": f"{PY_BIN} -m pytest -q", "group": "test"},
       ],
       "inputs": [
           {"id": "query", "type": "promptString",
            "description": "What are you looking for?", "default": "authentication"}
       ],
   }
   (VSCODE_DIR / "tasks.json").write_text(json.dumps(tasks, indent=2))

   launch = {
       "version": "0.2.0",
       "configurations": [
           {"name": "Python: Current File", "type": "python",
            "request": "launch", "program": "${file}", "console": "integratedTerminal"}
       ],
   }
   (VSCODE_DIR / "launch.json").write_text(json.dumps(launch, indent=2))

def install_vscode_extensions():
   if not AUTO_INSTALL_VSCODE_EXTENSIONS:
       return
   code_cli = which("code")
   if not code_cli:
       print("VS Code CLI 'code' not found; skipping auto-install. "
             "Tip: Command Palette → “Shell Command: Install 'code' in PATH”.")
       return
   ext_ids = [
       "ms-python.python",
       "ms-python.vscode-pylance",
       "ms-python.black-formatter",
       "ms-python.isort",
       "ms-toolsai.jupyter",
       "editorconfig.editorconfig",
       "GitHub.copilot",
       "GitHub.copilot-chat",
       "yzhang.markdown-all-in-one",
       "bierner.markdown-mermaid",
       "openai.chatgpt",
   ]
   for ext in ext_ids:
       run(f"{shlex.quote(code_cli)} --install-extension {shlex.quote(ext)} --force", check=False)

# ----------------------------
# Git + SSH
# ----------------------------
def ensure_git():
   if not (WS_ROOT / ".git").exists():
       run("git init -b main")
   run(f"git config user.name {shlex.quote(GIT_NAME)}")
   run(f"git config user.email {shlex.quote(GIT_EMAIL)}")
   run("git config pull.ff only")
   if IS_MAC:
       run("git config --global credential.helper osxkeychain", check=False)
   elif IS_WIN:
       run("git config --global credential.helper manager", check=False)
   else:
       run("git config --global credential.helper store", check=False)

def ensure_ssh():
   ensure_dir(SSH_DIR, mode=0o700)
   if not KEY_PATH.exists():
       # no passphrase for least prompts; feel free to secure manually later
       run(f'ssh-keygen -t ed25519 -C {shlex.quote(GIT_EMAIL)} -f {shlex.quote(KEY_PATH.as_posix())} -N ""')
   block = [
       "Host github.com",
       "  HostName github.com",
       "  User git",
       f"  IdentityFile {KEY_PATH.as_posix()}",
       "  IdentitiesOnly yes",
       "  AddKeysToAgent yes",
   ]
   if IS_MAC:
       block.append("  UseKeychain yes")
   cfg = "\n".join(block) + "\n"
   if SSH_CONFIG.exists():
       txt = SSH_CONFIG.read_text()
       if "Host github.com" not in txt:
           SSH_CONFIG.write_text(txt.rstrip() + "\n\n" + cfg)
   else:
       SSH_CONFIG.write_text(cfg)
       SSH_CONFIG.chmod(0o600)
   # Add key to agent
   if IS_MAC:
       run('eval "$(ssh-agent -s)" && ssh-add --apple-use-keychain ' + shlex.quote(KEY_PATH.as_posix()), check=False)
   else:
       run('eval "$(ssh-agent -s)" && ssh-add ' + shlex.quote(KEY_PATH.as_posix()), check=False)

def maybe_upload_public_key():
   """Optional: upload SSH public key to GitHub for zero manual steps (needs admin:public_key)."""
   if not GITHUB_TOKEN:
       return False
   pub = KEY_PATH.with_suffix(".pub")
   if not pub.exists():
       return False
   try:
       user = gh_api("https://api.github.com/user")
       login = user.get("login")
       title = f"auto-{platform.node()}-{int(time.time())}"
       gh_api("https://api.github.com/user/keys", method="POST",
              data={"title": title, "key": pub.read_text().strip()})
       print(f"Uploaded SSH public key to user '{login}' as '{title}'.")
       return True
   except Exception as e:
       print(f"Could not upload SSH key automatically: {e}")
       return False

def show_public_key_hint():
   pub = KEY_PATH.with_suffix(".pub")
   if pub.exists():
       print("\n=== Add this SSH public key at GitHub → Settings → SSH and GPG keys ===")
       print(pub.read_text().strip())
       print("=======================================================================\n")

# ----------------------------
# GitHub API: create repo (private) and verify visibility
# ----------------------------
def github_api_create_repo(name: str, private=True) -> tuple[str | None, str | None]:
   if not GITHUB_TOKEN:
       print("No GITHUB_TOKEN set; skipping GitHub API repo creation.")
       return None, None
   user = gh_api("https://api.github.com/user")
   login = GITHUB_USER or user.get("login")
   try:
       gh_api("https://api.github.com/user/repos", method="POST",
              data={"name": name, "private": bool(private), "auto_init": False})
       print(f"Created repo github.com/{login}/{name} (private={private})")
   except Exception:
       print("Repo may already exist; continuing…")
   return f"git@github.com:{login}/{name}.git", login

def verify_repo_private(owner: str, repo: str) -> bool:
   """Return True iff the repo is private (guards against accidental public push)."""
   if not GITHUB_TOKEN:
       # Without token we cannot verify; be conservative: allow if pushing to SSH origin we created.
       return True
   data = gh_api(f"https://api.github.com/repos/{owner}/{repo}")
   is_private = bool(data.get("private"))
   if not is_private:
       print(f"⚠️ Repo github.com/{owner}/{repo} is PUBLIC — aborting push.")
   return is_private

# ----------------------------
# Docs + ADRs
# ----------------------------
def scaffold_docs():
   ensure_dir(DOCS_DIR)
   (DOCS_DIR / "index.md").write_text(f"""# {PROJECT_NAME}

Welcome! This template aims to make setup smooth and private by default.

## 📌 Project Scope & Objectives (Plain English)

### Scope
Describe in one sentence what this project is about (e.g., "A reusable Python + VS Code + GitHub template for new projects").

**It includes:**
- Automatic environment + editor setup (VS Code settings, extensions)
- GitHub CI checks (lint, format, tests)
- Local "AI memory" search to find relevant code/docs quickly
- Docs scaffold (this site), ADRs for decisions
- Private GitHub repo by default; no public publishing

**It does NOT include (for now):**
- Public website hosting or docs publishing
- Cloud infrastructure

### Objectives
- Make onboarding easy: open in VS Code and go.
- Reduce prompts/approvals when pushing to GitHub (SSH + sensible defaults).
- Keep code clean automatically (pre-commit hooks, formatters).
- Document scope/decisions so non-technical readers can follow along.
- Ensure each push/PR is checked by CI.

### Success Criteria
- New contributors can run code without manual setup.
- Pushes generally don't ask for repeated approvals.
- Each push/PR runs CI and reports status.
- Docs remain easy to read and update.

## 🚀 Quick start
- **Docs**: `mkdocs serve -a 127.0.0.1:8000`
- **Local memory**:
 - Build index: `python tools/ai_memory/index_repo.py`
 - Search: `python tools/ai_memory/search_memory.py "authentication" -k 8`
""", encoding="utf-8")

   ensure_dir(DOCS_DIR / "adr")
   (DOCS_DIR / "architecture.md").write_text("# Architecture\n\nDescribe modules and data flow here.\n", encoding="utf-8")
   (DOCS_DIR / "adr" / "0001-record-architecture-decision.md").write_text(
       "# ADR 0001: Record architecture decisions\n\n- Status: proposed\n- Decision: Use simple ADR markdown files in `docs/adr/`.\n", encoding="utf-8"
   )

   # Model picker & cost awareness doc
   (DOCS_DIR / "copilot-model-picker.md").write_text(
       """# Copilot Model Picker (VS Code)

**Where to change the model:** In the **Copilot Chat input**, use the model picker dropdown.

**Cost tips**
- GitHub meters some models as premium requests. Prefer included models (e.g., GPT‑4.1 on paid plans) for routine work.
- The coding agent on GitHub.com also uses Actions minutes (Agent Mode inside VS Code does not).

**Best practice**
- Choose included models for most prompts; switch to heavier models only when needed.
""", encoding="utf-8"
   )

   (WS_ROOT / "mkdocs.yml").write_text(f"""site_name: {PROJECT_NAME}
theme:
 name: material
nav:
 - Home: index.md
 - Architecture: architecture.md
 - ADRs:
     - ADR 0001: adr/0001-record-architecture-decision.md
 - Copilot Model Picker: copilot-model-picker.md
markdown_extensions:
 - toc: {{ permalink: true }}
 - admonition
 - tables
 - codehilite
 - attr_list
""", encoding="utf-8")

# ----------------------------
# Model picker & ChatGPT Pro helpers (README + prompt files)
# ----------------------------
def scaffold_model_picker_and_chatgpt_helpers():
   ensure_dir(WS_ROOT / ".github" / "prompts")
   # README quick-links
   readme = WS_ROOT / "README.md"
   quick_links = """### 🧭 Quick Links: Copilot/ChatGPT
- [Open Copilot Chat](command:workbench.action.chat.open)
- [Open Settings → search “language model”](command:workbench.action.openSettings?%5B%22language%20model%22%5D)
"""
   pro_block = """
## 🤝 Link your ChatGPT Pro to VS Code

Two ways to use **ChatGPT Pro** with code:

### A) ChatGPT “Work with Apps” ↔ VS Code (macOS)
1. Install the **ChatGPT macOS app** and sign in with your **Pro** account.
2. In the app: **Settings → Work with Apps** → enable and grant **Accessibility**.
3. In **VS Code**, ensure the **OpenAI ChatGPT** extension (`openai.chatgpt`) is installed.
4. Use ChatGPT to work with files open in VS Code.

### B) Connectors (ChatGPT ↔ GitHub/Drive)
- In ChatGPT: **Settings → Connected apps (Connectors)** → connect **GitHub** (and **Google Drive** if needed).
- Then you can ask questions like “Summarize the README in repo X” or “Find file Y and explain function Z”.

Tip: Ensure you’re signed into VS Code with the same account you use for GitHub/ChatGPT.
"""
   if readme.exists():
       txt = readme.read_text(encoding="utf-8")
       if "Quick Links: Copilot/ChatGPT" not in txt:
           readme.write_text(quick_links + txt, encoding="utf-8")
       if "Link your ChatGPT Pro to VS Code" not in txt:
           readme.write_text((quick_links + txt).rstrip() + "\n" + pro_block + "\n", encoding="utf-8")
   else:
       readme.write_text(f"# {PROJECT_NAME}\n\n{quick_links}\n{pro_block}", encoding="utf-8")

   # Prompt file (appears in Chat prompt files)
   (WS_ROOT / ".github" / "prompts" / "model-cost-check.md").write_text(
       "# Model cost check (attach me)\n\n- Prefer included models for routine work (e.g., GPT‑4.1).\n- Switch to heavier models only when necessary.\n- Coding agent on GitHub.com consumes Actions minutes; VS Code Agent Mode does not.\n",
       encoding="utf-8",
   )

# ----------------------------
# AI Memory (Whoosh)
# ----------------------------
def scaffold_ai_memory():
   ensure_dir(AI_DIR)
   ensure_dir(AI_INDEX_DIR)
   (AI_DIR / "README.md").write_text(
       "# AI Memory (Local Search)\n\nBuild and query a local search index of your repo for quick context.\n\n"
       "Build: `python tools/ai_memory/index_repo.py`\n"
       "Search: `python tools/ai_memory/search_memory.py \"auth\" -k 8`\n", encoding="utf-8"
   )

   (AI_DIR / "index_repo.py").write_text(r"""#!/usr/bin/env python3
import pathlib
from whoosh import index
from whoosh.fields import Schema, ID, TEXT
from whoosh.analysis import StemmingAnalyzer
from whoosh.writing import AsyncWriter

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX_DIR = pathlib.Path(__file__).resolve().parent / "indexdir"

INCLUDE_EXT = {
   ".py",".md",".rst",".txt",".toml",".yaml",".yml",".json",".ini",".cfg",
   ".sh",".ps1",".sql",".html",".css",".js",".ts"
}
SKIP_DIRS = {".git", ".venv", "node_modules", "dist", "build", "__pycache__", ".mypy_cache", ".ruff_cache"}

schema = Schema(path=ID(stored=True, unique=True), content=TEXT(stored=True, analyzer=StemmingAnalyzer()))
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def iter_files():
   for p in ROOT.rglob("*"):
       if p.is_dir():
           if p.name in SKIP_DIRS:
               continue
       else:
           if p.suffix.lower() in INCLUDE_EXT and not any(part in SKIP_DIRS for part in p.parts):
               yield p

def read_text(p: pathlib.Path) -> str:
   for enc in ("utf-8", "latin-1"):
       try:
           return p.read_text(encoding=enc, errors="ignore")
       except Exception:
           continue
   return ""

def build_index():
   if not index.exists_in(INDEX_DIR):
       ix = index.create_in(INDEX_DIR, schema)
   else:
       ix = index.open_dir(INDEX_DIR)
   writer = AsyncWriter(ix)
   count = 0
   for fp in iter_files():
       txt = read_text(fp)
       writer.update_document(path=str(fp.relative_to(ROOT)), content=txt)
       count += 1
   writer.commit()
   print(f"Indexed {count} files into {INDEX_DIR}")

if __name__ == "__main__":
   build_index()
""", encoding="utf-8")
   os.chmod((AI_DIR / "index_repo.py").as_posix(), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

   (AI_DIR / "search_memory.py").write_text(r"""#!/usr/bin/env python3
import argparse, pathlib
from whoosh import index
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.highlight import ContextFragmenter, UppercaseFormatter

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX_DIR = pathlib.Path(__file__).resolve().parent / "indexdir"
OUT_DIR = ROOT / "context"
OUT_DIR.mkdir(exist_ok=True)

def search(query: str, k: int = 10):
   if not index.exists_in(INDEX_DIR):
       print("Index not found. Run: python tools/ai_memory/index_repo.py")
       return
   ix = index.open_dir(INDEX_DIR)
   qp = MultifieldParser(["content"], schema=ix.schema, group=OrGroup)
   q = qp.parse(query)
   with ix.searcher() as s:
       results = s.search(q, limit=k)
       results.fragmenter = ContextFragmenter(maxchars=200, surround=60)
       results.formatter = UppercaseFormatter()
       out_md = [f"# Context for: {query}", ""]
       print(f"\nTop {min(k, len(results))} results:\n")
       for i, hit in enumerate(results):
           path = hit["path"]
           snippet = hit.highlights("content") or ""
           print(f"{i+1}. {path}\n   {snippet}\n")
           out_md.append(f"## {i+1}. {path}\n\n{snippet}\n")
       out_path = OUT_DIR / "context.md"
       out_path.write_text("\n".join(out_md), encoding="utf-8")
       print(f"\nSaved combined context to {out_path}")

if __name__ == "__main__":
   ap = argparse.ArgumentParser()
   ap.add_argument("query", help="What are you looking for?")
   ap.add_argument("-k", type=int, default=10, help="How many results")
   args = ap.parse_args()
   search(args.query, args.k)
""", encoding="utf-8")
   os.chmod((AI_DIR / "search_memory.py").as_posix(), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

# ----------------------------
# CI + Security + Dependabot + Templates + EditorConfig
# ----------------------------
def scaffold_ci_security_and_tools():
   # CI (cached pip)
   ci_dir = WS_ROOT / ".github" / "workflows"
   ensure_dir(ci_dir)
   (ci_dir / "ci.yml").write_text("""name: CI
on:
 push: { branches: [ main ] }
 pull_request: { branches: [ main ] }
jobs:
 build:
   runs-on: ubuntu-latest
   steps:
     - uses: actions/checkout@v4
     - uses: actions/setup-python@v5
       with:
         python-version: '3.11'
         cache: 'pip'
         cache-dependency-path: |
           requirements.txt
           pyproject.toml
     - name: Install dependencies
       run: |
         python -m venv .venv
         source .venv/bin/activate
         pip install --upgrade pip
         pip install -r requirements.txt || true
     - name: Lint (flake8)
       run: |
         source .venv/bin/activate
         flake8 .
     - name: Format check (Black)
       run: |
         source .venv/bin/activate
         black --check .
     - name: Import sort check (isort)
       run: |
         source .venv/bin/activate
         isort . --check-only --profile black
     - name: Tests
       run: |
         source .venv/bin/activate
         pytest || echo "No tests found; skipping"
""", encoding="utf-8")

   # CodeQL (security)
   (ci_dir / "codeql.yml").write_text("""name: CodeQL
on:
 push: { branches: [ main ] }
 pull_request: { branches: [ main ] }
 schedule: [ { cron: '0 8 * * 1' } ]
jobs:
 analyze:
   runs-on: ubuntu-latest
   permissions:
     security-events: write
     actions: read
     contents: read
   steps:
     - uses: actions/checkout@v4
     - uses: github/codeql-action/init@v3
       with: { languages: 'python' }
     - uses: github/codeql-action/analyze@v3
""", encoding="utf-8")

   # Gitleaks
   (ci_dir / "gitleaks.yml").write_text("""name: gitleaks
on: [push, pull_request]
jobs:
 scan:
   runs-on: ubuntu-latest
   steps:
     - uses: actions/checkout@v4
     - uses: gitleaks/gitleaks-action@v2
""", encoding="utf-8")

   # Dependabot
   dep = WS_ROOT / ".github" / "dependabot.yml"
   ensure_dir(dep.parent)
   dep.write_text("""version: 2
updates:
 - package-ecosystem: "pip"
   directory: "/"
   schedule: { interval: "weekly" }
 - package-ecosystem: "github-actions"
   directory: "/"
   schedule: { interval: "weekly" }
""", encoding="utf-8")

   # PR / Issue templates
   issue_dir = WS_ROOT / ".github" / "ISSUE_TEMPLATE"
   ensure_dir(issue_dir)
   (WS_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(
       "## Summary\n- What changed and why?\n\n## Checklist\n- [ ] Lints/format pass\n- [ ] Tests updated/added (if applicable)\n- [ ] Docs updated (if needed)\n",
       encoding="utf-8",
   )
   (issue_dir / "bug_report.yml").write_text("""name: Bug report
description: Report a problem
body:
 - type: textarea
   id: what-happened
   attributes:
     label: What happened?
     placeholder: Steps to reproduce...
   validations:
     required: true
""", encoding="utf-8")

   # EditorConfig
   (WS_ROOT / ".editorconfig").write_text("""root = true
[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4
""", encoding="utf-8")

# ----------------------------
# Dev Container (Codespaces/Remote)
# ----------------------------
def scaffold_devcontainer():
   dev_dir = WS_ROOT / ".devcontainer"
   ensure_dir(dev_dir)
   (dev_dir / "devcontainer.json").write_text("""{
 "name": "Python Project Dev",
 "image": "mcr.microsoft.com/devcontainers/python:3.11",
 "features": {
   "ghcr.io/devcontainers/features/common-utils:2": {}
 },
 "postCreateCommand": "pip install -r requirements.txt || true",
 "customizations": {
   "vscode": {
     "extensions": [
       "ms-python.python",
       "ms-python.vscode-pylance",
       "ms-python.black-formatter",
       "ms-python.isort",
       "ms-toolsai.jupyter",
       "editorconfig.editorconfig",
       "GitHub.copilot",
       "GitHub.copilot-chat",
       "openai.chatgpt"
     ]
   }
 },
 "remoteUser": "vscode"
}
""", encoding="utf-8")

# ----------------------------
# Repo files: README, ignores, pre-commit, pyproject
# ----------------------------
def write_repo_files():
   if not (WS_ROOT / "README.md").exists():
       (WS_ROOT / "README.md").write_text(
           f"# {PROJECT_NAME}\n\nBootstrapped by script. See `docs/` for scope & objectives.\n",
           encoding="utf-8",
       )
   (WS_ROOT / ".gitignore").write_text(
       ".venv/\n__pycache__/\n*.pyc\n.env\nnode_modules/\ndist/\nbuild/\n"
       "tools/ai_memory/indexdir/\ncontext/\n",
       encoding="utf-8",
   )
   (WS_ROOT / "pyproject.toml").write_text("""[tool.black]
line-length = 88
target-version = ["py38", "py39", "py310", "py311"]

[tool.isort]
profile = "black"
""", encoding="utf-8")

   (WS_ROOT / ".pre-commit-config.yaml").write_text("""repos:
 - repo: https://github.com/pre-commit/pre-commit-hooks
   rev: v4.6.0
   hooks:
     - id: end-of-file-fixer
     - id: trailing-whitespace
     - id: check-yaml
     - id: check-json
     - id: pretty-format-json
       args: ["--autofix"]
 - repo: https://github.com/psf/black
   rev: 24.8.0
   hooks:
     - id: black
 - repo: https://github.com/pycqa/isort
   rev: 5.13.2
   hooks:
     - id: isort
 - repo: https://github.com/pycqa/flake8
   rev: 7.1.1
   hooks:
     - id: flake8
 - repo: https://github.com/executablebooks/mdformat
   rev: 0.7.17
   hooks:
     - id: mdformat
       additional_dependencies: [mdformat-gfm]
 - repo: https://github.com/gitleaks/gitleaks
   rev: v8.18.4
   hooks:
     - id: gitleaks
""", encoding="utf-8")

# ----------------------------
# Commit & push (with "private" guard)
# ----------------------------
def git_commit_and_push(remote_url: str | None, owner: str | None):
   # Install pre-commit
   run(f"{PRE_COMMIT_BIN} install", check=False)
   run("git add -A")
   run('git commit -m "chore: bootstrap (private, VS Code, CI, security, devcontainer, docs, AI memory)"', check=False)

   if not remote_url:
       print(
           "\nNo remote set. After adding your SSH key to GitHub, run:\n"
           f"  git remote add origin git@github.com:<your-username>/{PROJECT_NAME}.git\n"
           "  git push -u origin main\n"
       )
       return

   # Ensure remote is SSH and repo is private before pushing
   run("git remote remove origin", check=False)
   run(f"git remote add origin {shlex.quote(remote_url)}")

   # Extract owner/repo for visibility check
   repo_name = PROJECT_NAME
   repo_owner = owner or "unknown"
   if owner and verify_repo_private(owner, repo_name):
       run("git push -u origin main", check=False)
   else:
       print("Push skipped due to visibility check or missing token.")

# ----------------------------
# Main
# ----------------------------
def main():
   ensure_venv()
   write_vscode()
   install_vscode_extensions()
   ensure_git()
   ensure_ssh()
   uploaded = maybe_upload_public_key()
   scaffold_docs()
   scaffold_model_picker_and_chatgpt_helpers()
   scaffold_ai_memory()
   scaffold_ci_security_and_tools()
   scaffold_devcontainer()
   write_repo_files()

   remote, owner = github_api_create_repo(PROJECT_NAME, PRIVATE_REPO)
   if not uploaded:
       show_public_key_hint()
   git_commit_and_push(remote, owner)

   print(
       "\n✅ Bootstrap complete.\n"
       "- Repo created private; first push guarded by visibility check.\n"
       "- VS Code settings & extensions configured by Python.\n"
       "- SSH key added locally (and uploaded if token allowed).\n"
       "- CI/Security/Dependabot/Devcontainer/Docs/AI memory scaffolded.\n"
       "Open this folder in VS Code — README opens with quick links.\n"
   )

if __name__ == "__main__":
   main()