# jibber-jabber 24 august 2025 big bop

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
