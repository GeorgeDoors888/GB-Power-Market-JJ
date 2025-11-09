# 📝 GITMORE.md - Git Management for Dashboard Project

**Purpose:** Complete Git workflow guide for managing the GB Power Market dashboard  
**Audience:** Developers, data analysts, and team members  
**Last Updated:** November 9, 2025

---

## 📋 Table of Contents

1. [Git Basics](#git-basics)
2. [Repository Structure](#repository-structure)
3. [Branching Strategy](#branching-strategy)
4. [Commit Guidelines](#commit-guidelines)
5. [Dashboard-Specific Workflows](#dashboard-specific-workflows)
6. [File Management](#file-management)
7. [Collaboration](#collaboration)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Git Basics

### Initial Setup (First Time Only)

```bash
# Clone repository
git clone https://github.com/GeorgeDoors888/GB-Power-Market-JJ.git
cd GB-Power-Market-JJ

# Configure Git
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Verify configuration
git config --list
```

### Daily Workflow

```bash
# 1. Start your day - get latest changes
git pull origin main

# 2. Check status
git status

# 3. Make changes to files
# ... edit files ...

# 4. Check what changed
git diff

# 5. Stage changes
git add dashboard/
git add *.py
# or stage all:
git add -A

# 6. Commit with meaningful message
git commit -m "feat(dashboard): Add real-time chart updates"

# 7. Push to GitHub
git push origin main
```

---

## 📁 Repository Structure

### Dashboard Files Organization

```
GB Power Market JJ/
├── dashboard/                              # 📊 Dashboard sub-project
│   ├── README.md                           # Main dashboard documentation
│   ├── GITMORE.md                          # This file
│   ├── apps-script/                        # Google Apps Script files
│   │   ├── google_sheets_dashboard_v2.gs
│   │   ├── dashboard_charts_v2.gs
│   │   └── Code.gs
│   ├── python-updaters/                    # Python update scripts
│   │   ├── realtime_dashboard_updater.py
│   │   ├── update_analysis_bi_enhanced.py
│   │   └── enhance_dashboard_layout.py
│   └── docs/                               # Dashboard documentation
│       ├── DASHBOARD_QUICKSTART.md
│       └── DASHBOARD_SETUP_COMPLETE.md
│
├── .gitignore                              # Files to exclude
├── .github/                                # GitHub configuration
│   └── copilot-instructions.md             # AI assistant config
├── chat-history/                           # Conversation logs
├── logs/                                   # Runtime logs (not committed)
└── ... (other project files)
```

### What Gets Committed to Git

✅ **Always Commit:**
- Source code (`.py`, `.gs`, `.sql`)
- Documentation (`.md`, `.txt`)
- Configuration templates (`.json.example`)
- Scripts (`deploy_*.sh`, `*.sh`)
- README files

❌ **Never Commit:**
- Credentials (`*credentials*.json`, `*.pickle`)
- API keys (`.env` files with secrets)
- Large data files (`.csv` > 10MB)
- Log files (`logs/*.log`)
- Temporary files (`*.tmp`, `*.bak`)
- Python virtual environments (`venv/`, `.venv/`)

⚠️ **Commit With Caution:**
- Sample data (small datasets OK)
- Configuration files (remove sensitive data first)
- Screenshots (compress first)

---

## 🌲 Branching Strategy

### Branch Types

```
main (production)
  ├── feature/dashboard-improvements
  ├── feature/new-chart-type
  ├── hotfix/data-refresh-bug
  └── release/v2.1.0
```

### Creating Branches

```bash
# Feature branch (new functionality)
git checkout -b feature/add-settlement-period-charts
git checkout -b feature/realtime-price-alerts

# Hotfix branch (urgent bug fix)
git checkout -b hotfix/fix-data-refresh-cron
git checkout -b hotfix/chart-display-issue

# Release branch (version prep)
git checkout -b release/v2.1.0
```

### Working with Branches

```bash
# List all branches
git branch -a

# Switch to existing branch
git checkout feature/dashboard-improvements

# Create and switch in one command
git checkout -b feature/new-feature

# Delete local branch (after merge)
git branch -d feature/completed-feature

# Delete remote branch
git push origin --delete feature/old-feature
```

### Merging Branches

```bash
# 1. Switch to main
git checkout main

# 2. Update main
git pull origin main

# 3. Merge feature branch
git merge feature/dashboard-improvements

# 4. Push merged changes
git push origin main

# 5. Delete feature branch
git branch -d feature/dashboard-improvements
```

---

## 📝 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(dashboard): Add real-time chart updates` |
| `fix` | Bug fix | `fix(updater): Correct settlement period calculation` |
| `docs` | Documentation | `docs(readme): Update installation instructions` |
| `style` | Code style (no logic change) | `style(dashboard): Format chart positioning` |
| `refactor` | Code refactoring | `refactor(updater): Simplify query logic` |
| `test` | Add tests | `test(dashboard): Add chart rendering tests` |
| `chore` | Maintenance | `chore(deps): Update gspread to 5.12.0` |
| `perf` | Performance improvement | `perf(query): Optimize BigQuery joins` |

### Good Commit Messages

```bash
# ✅ Good - Clear and specific
git commit -m "feat(charts): Add pie chart for generation mix"
git commit -m "fix(updater): Handle missing settlement periods gracefully"
git commit -m "docs(dashboard): Add troubleshooting section to README"

# ❌ Bad - Vague or unclear
git commit -m "fix stuff"
git commit -m "update"
git commit -m "changes"
```

### Multi-line Commits

```bash
git commit -m "feat(dashboard): Add real-time settlement period tracking

- Implement SP 0 (00:00) start point
- Add current SP indicator to header
- Update every 30 minutes automatically
- Maintain formatting consistency

Closes #42"
```

### Commit Best Practices

1. **Commit Often:** Small, focused commits
2. **Atomic Commits:** One logical change per commit
3. **Test Before Commit:** Ensure code works
4. **Review Changes:** Check `git diff` before committing
5. **Write Meaningful Messages:** Future you will thank you!

---

## 📊 Dashboard-Specific Workflows

### Workflow 1: Update Python Updater Script

```bash
# 1. Create feature branch
git checkout -b feature/improve-updater

# 2. Edit the updater
vim realtime_dashboard_updater.py

# 3. Test locally
python3 realtime_dashboard_updater.py

# 4. Check what changed
git diff realtime_dashboard_updater.py

# 5. Stage and commit
git add realtime_dashboard_updater.py
git commit -m "feat(updater): Add error handling for missing data"

# 6. Push to remote
git push origin feature/improve-updater

# 7. Merge to main (after testing)
git checkout main
git merge feature/improve-updater
git push origin main
```

### Workflow 2: Deploy New Apps Script

```bash
# 1. Update Apps Script locally
vim dashboard/apps-script/dashboard_charts_v2.gs

# 2. Stage changes
git add dashboard/apps-script/dashboard_charts_v2.gs

# 3. Commit
git commit -m "feat(charts): Add column chart for top generation sources"

# 4. Push to GitHub
git push origin main

# 5. Manually deploy to Google Sheets
# (Open Apps Script editor, paste updated code, save)

# 6. Document deployment
git commit -m "docs(dashboard): Record chart deployment v2.1" --allow-empty
```

### Workflow 3: Fix Production Issue (Hotfix)

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/data-refresh-fix

# 2. Fix the issue
vim realtime_dashboard_updater.py

# 3. Test fix
python3 realtime_dashboard_updater.py

# 4. Commit fix
git add realtime_dashboard_updater.py
git commit -m "fix(updater): Correct timezone handling for settlement periods"

# 5. Push hotfix
git push origin hotfix/data-refresh-fix

# 6. Merge to main IMMEDIATELY
git checkout main
git merge hotfix/data-refresh-fix
git push origin main

# 7. Deploy to production
# (Restart cron job, verify fix)

# 8. Delete hotfix branch
git branch -d hotfix/data-refresh-fix
```

### Workflow 4: Create New Documentation

```bash
# 1. Create docs in dashboard folder
vim dashboard/docs/NEW_FEATURE_GUIDE.md

# 2. Add to Git
git add dashboard/docs/NEW_FEATURE_GUIDE.md

# 3. Commit with docs type
git commit -m "docs(dashboard): Add guide for new chart features"

# 4. Update main README if needed
vim dashboard/README.md
git add dashboard/README.md
git commit -m "docs(dashboard): Link to new feature guide"

# 5. Push
git push origin main
```

---

## 📂 File Management

### Checking File Status

```bash
# See what's changed
git status

# See detailed changes
git diff

# See changes for specific file
git diff realtime_dashboard_updater.py

# See staged changes
git diff --staged
```

### Staging Files

```bash
# Stage specific file
git add dashboard/README.md

# Stage all files in directory
git add dashboard/

# Stage all Python files
git add *.py

# Stage everything
git add -A

# Stage interactively (choose what to stage)
git add -p
```

### Unstaging Files

```bash
# Unstage file
git restore --staged dashboard/README.md

# Unstage all
git restore --staged .
```

### Discarding Changes

```bash
# Discard changes in file (⚠️ DANGEROUS - can't undo!)
git restore dashboard/README.md

# Discard all local changes (⚠️ DANGEROUS!)
git restore .

# Better: Stash changes instead
git stash
git stash list
git stash pop  # Restore later
```

### Moving/Renaming Files

```bash
# Rename file (Git tracks the rename)
git mv old_name.py new_name.py
git commit -m "refactor: Rename updater script for clarity"

# Move file to different directory
git mv script.py dashboard/python-updaters/script.py
git commit -m "chore: Reorganize dashboard scripts"
```

### Deleting Files

```bash
# Delete file
git rm unwanted_file.py
git commit -m "chore: Remove deprecated script"

# Delete directory
git rm -r old_directory/
git commit -m "chore: Remove unused dashboard components"

# Keep file locally but remove from Git
git rm --cached secret_file.json
git commit -m "chore: Remove credentials from Git"
```

---

## 🤝 Collaboration

### Pulling Latest Changes

```bash
# Fetch and merge changes from remote
git pull origin main

# If you have local changes, stash first
git stash
git pull origin main
git stash pop
```

### Handling Merge Conflicts

```bash
# When merge conflict occurs
git pull origin main
# CONFLICT in dashboard/README.md

# 1. Open conflicted file
vim dashboard/README.md

# Look for conflict markers:
# <<<<<<< HEAD
# Your changes
# =======
# Their changes
# >>>>>>> origin/main

# 2. Resolve conflict manually

# 3. Stage resolved file
git add dashboard/README.md

# 4. Complete merge
git commit -m "merge: Resolve README conflict"

# 5. Push
git push origin main
```

### Reviewing Others' Changes

```bash
# See commit history
git log --oneline --graph --all

# See specific commit
git show abc1234

# See who changed what in file
git blame dashboard/README.md

# Compare branches
git diff main feature/new-feature
```

### Pull Requests (GitHub)

```bash
# 1. Create feature branch
git checkout -b feature/new-dashboard-layout

# 2. Make changes and commit
git add .
git commit -m "feat(dashboard): Redesign layout for mobile"

# 3. Push to remote
git push origin feature/new-dashboard-layout

# 4. Go to GitHub.com
# 5. Create Pull Request from feature branch to main
# 6. Request review from team
# 7. Address feedback
# 8. Merge when approved
```

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: "fatal: not a git repository"
```bash
# Solution: Initialize Git or cd into repo
cd ~/GB\ Power\ Market\ JJ
git status
```

#### Issue: "Your branch is behind 'origin/main'"
```bash
# Solution: Pull latest changes
git pull origin main
```

#### Issue: "Merge conflict"
```bash
# Solution: Resolve conflicts manually
git status  # See conflicted files
# Edit files to resolve conflicts
git add <resolved-files>
git commit -m "merge: Resolve conflicts"
```

#### Issue: "Permission denied (publickey)"
```bash
# Solution: Set up SSH keys
ssh-keygen -t ed25519 -C "your.email@example.com"
# Add to GitHub: Settings → SSH Keys
```

#### Issue: "Detached HEAD state"
```bash
# Solution: Return to branch
git checkout main
```

#### Issue: Accidentally committed sensitive file
```bash
# Solution: Remove from history (⚠️ Rewrite history!)
git rm --cached secret_credentials.json
git commit -m "chore: Remove credentials"
git push origin main

# Better: Use .gitignore to prevent in future
echo "secret_credentials.json" >> .gitignore
```

### Useful Commands

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) ⚠️ DANGEROUS
git reset --hard HEAD~1

# View commit history
git log --oneline --graph --all --decorate

# Search commit messages
git log --grep="dashboard"

# Find who changed a line
git blame -L 10,20 dashboard/README.md

# Show file at specific commit
git show abc1234:dashboard/README.md

# List files changed in commit
git diff-tree --no-commit-id --name-only -r abc1234

# Temporarily ignore changes to tracked file
git update-index --assume-unchanged dashboard/local_config.json

# Resume tracking
git update-index --no-assume-unchanged dashboard/local_config.json
```

---

## 📊 Dashboard File Checklist

Before committing dashboard changes, verify:

### Code Files
- [ ] Python scripts tested locally
- [ ] Apps Script code syntax verified
- [ ] No hardcoded credentials in code
- [ ] Comments explain complex logic
- [ ] Error handling implemented

### Documentation
- [ ] README.md updated if needed
- [ ] CHANGELOG.md entry added
- [ ] Code comments clear
- [ ] API documentation current

### Configuration
- [ ] No sensitive data in commits
- [ ] `.gitignore` updated for new file types
- [ ] Example configs provided (`.example` files)

### Testing
- [ ] Dashboard displays correctly
- [ ] Data updates working
- [ ] Charts rendering properly
- [ ] No console errors

---

## 🎓 Git Best Practices Summary

### Do's ✅
1. ✅ Commit often with meaningful messages
2. ✅ Pull before you push
3. ✅ Use branches for features
4. ✅ Review changes before committing (`git diff`)
5. ✅ Keep commits atomic (one change per commit)
6. ✅ Write clear commit messages
7. ✅ Use `.gitignore` properly
8. ✅ Test before committing

### Don'ts ❌
1. ❌ Don't commit credentials or API keys
2. ❌ Don't commit large data files
3. ❌ Don't commit directly to main (use branches)
4. ❌ Don't force push to shared branches
5. ❌ Don't commit broken code
6. ❌ Don't use vague commit messages
7. ❌ Don't commit generated files
8. ❌ Don't rewrite published history

---

## 📚 Additional Resources

### Git Documentation
- [Git Official Docs](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

### Dashboard-Specific Docs
- [dashboard/README.md](README.md) - Dashboard overview
- [DASHBOARD_QUICKSTART.md](../DASHBOARD_QUICKSTART.md) - Quick start guide
- [PROJECT_CONFIGURATION.md](../PROJECT_CONFIGURATION.md) - Project config

### Interactive Learning
- [Learn Git Branching](https://learngitbranching.js.org/)
- [Git Immersion](http://gitimmersion.com/)

---

## 💡 Quick Reference Card

```bash
# Daily workflow
git pull                    # Get latest
git status                  # Check status
git add <files>            # Stage changes
git commit -m "message"    # Commit
git push                   # Push to GitHub

# Branching
git branch                 # List branches
git checkout -b <name>     # Create branch
git checkout <name>        # Switch branch
git merge <branch>         # Merge branch
git branch -d <name>       # Delete branch

# Viewing
git log                    # Commit history
git diff                   # See changes
git show <commit>          # Show commit

# Undoing
git restore <file>         # Discard changes
git restore --staged <file># Unstage
git reset --soft HEAD~1    # Undo commit
git stash                  # Save changes temp
```

---

**Last Updated:** November 9, 2025  
**Maintainer:** GB Power Market JJ Team  
**Status:** ✅ Active Guide
