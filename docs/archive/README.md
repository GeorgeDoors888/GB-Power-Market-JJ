# 📦 Documentation Archive

This directory contains **367 historical documentation files** that have been archived to keep the project root clean and organized.

**Archive Date**: November 18, 2025  
**Archived From**: Project root (reduced from 402 → 35 active docs)

---

## 📁 Archive Structure

### `/historical/` (185+ files)
**Purpose**: Completed features, old implementations, superseded guides

**Contains**:
- Old deployment guides (pre-Nov 2025)
- Completed projects (CVA/SVA/DNO maps, BESS/VLP features)
- Historical IRIS pipeline docs
- Completed integrations (Apps Script, Workspace)
- Old analysis sheet implementations
- Success reports and completion summaries

**Examples**:
- `ACTION_PLAN.md` - Original project action plan
- `CVA_*.md` - CVA/SVA implementation docs (completed)
- `DNO_*.md` - DNO map project (completed)
- `BESS_VLP*.md` - Battery VLP analysis guides (superseded)
- `IRIS_*.md` - Old IRIS pipeline docs (replaced)

### `/issues/` (30+ files)
**Purpose**: Resolved problems, bugs, and troubleshooting guides

**Contains**:
- Specific fix documentation
- Error resolution guides
- Problem-solving documentation
- Menu/UI issues (resolved)

**Examples**:
- `FIX_*.md` - Various fixes applied
- `*_PROBLEM*.md` - Problems that were solved
- `MENU_NOT_APPEARING_SOLUTION.md` - Resolved UI issue

### `/process/` (40+ files)
**Purpose**: Development sessions, migrations, setup documentation

**Contains**:
- Session summaries (historical)
- Migration guides (completed)
- Setup documentation (superseded)
- Status reports (old)
- Recovery plans (completed)

**Examples**:
- `SESSION_*.md` - Development session notes
- `*_MIGRATION*.md` - Data/code migrations
- `*_STATUS*.md` - System status reports
- `RECOVERY_*.md` - Recovery procedures

### `/references/` (60+ files)
**Purpose**: API documentation, old architectures, supplementary guides

**Contains**:
- API documentation (outdated/superseded)
- Old architecture docs
- Reference implementations
- Analysis guides (supplementary)
- BigQuery schemas (historical)

**Examples**:
- `API_*.md` - API documentation
- `BIGQUERY_*.md` - BigQuery references
- `GOOGLE_*.md` - Google services guides
- `VLP_*.md` - VLP analysis references

### `/dashboard-old/` (30+ files)
**Purpose**: Old dashboard implementations and guides

**Contains**:
- Pre-Nov 2025 dashboard docs
- Old layout designs
- Superseded refresh guides
- Historical dashboard fixes

**Keep in Root**: Only 4-5 current dashboard docs remain active

### `/chatgpt-old/` (25+ files)
**Purpose**: Historical ChatGPT integration documentation

**Contains**:
- Old ChatGPT setup guides
- Superseded instructions
- OAuth/authentication fixes (resolved)
- Custom GPT setup (old versions)

**Keep in Root**: Only 3-4 current ChatGPT docs remain active

### `/deployment-old/` (20+ files)
**Purpose**: Old deployment guides and procedures

**Contains**:
- Pre-Nov 2025 deployment docs
- AlmaLinux deployment (superseded)
- AWS setup guides (not used)
- UpCloud deployments (old)
- Vercel proxy (replaced)

**Keep in Root**: Only current deployment guides remain

---

## 🎯 What Stayed in Root (35 Essential Files)

### Critical Configuration (5 files)
- `README.md` - Project overview
- `PROJECT_CONFIGURATION.md` - Essential settings
- `DOCUMENTATION_INDEX.md` - Master index
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - **READ FIRST**
- `PROJECT_IDS.md` - Google Cloud projects

### Authentication & Backend (4 files)
- `AUTHENTICATION_ARCHITECTURE.md` - Complete auth guide
- `RAILWAY_DEPLOYMENT_GUIDE.md` - Backend deployment
- `WORKSPACE_DELEGATION_COMPLETE.md` - Domain delegation
- `RAILWAY_CHATGPT_PHASE_BY_PHASE.md` - Integration guide

### ChatGPT Integration (4 files)
- `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md` - Custom GPT setup
- `CHATGPT_PDF_ACCESS_GUIDE.md` - PDF search
- `CHATGPT_ACTUAL_ACCESS.md` - Access verification
- `CHATGPT_INSTRUCTIONS.md` - Basic instructions

### Dashboard (5 files)
- `DASHBOARD_DATA_REFRESH_GUIDE.md` - Refresh guide
- `DASHBOARD_FIX_SUMMARY_NOV_10.md` - Recent fixes
- `DASHBOARD_COMPLETE_NOV_10_2025.md` - Complete status
- `DASHBOARD_SEPARATE_DATA_COMPLETE.md` - Architecture
- `UPCLOUD_DASHBOARD_DEPLOYMENT_COMPLETE.md` - Deployment

### System Status (3 files)
- `BATCH_SIZE_CONSTRAINT_ANALYSIS.md` - Performance
- `IRIS_PIPELINE_SAFEGUARDS_MANDATORY.md` - Safeguards
- `IRIS_QUICK_REFERENCE.md` - Quick ref

### Analysis (5 files)
- `STATISTICAL_ANALYSIS_GUIDE.md` - Stats guide
- `QUICK_START_ANALYSIS.md` - Quick start
- `CODE_REVIEW_SUMMARY.md` - Code review
- `GOOGLE_DOCS_REPORT_SUMMARY.md` - Reports
- `BIGQUERY_SHEETS_AUTOMATION.md` - Automation

### Other Essential (9 files)
- `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` - Architecture
- `AUTO_REFRESH_COMPLETE.md` - Auto-refresh
- `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md` - IRIS deployment
- `WORKSPACE_API_MASTER_REFERENCE.md` - API reference
- `PRICE_DEMAND_CORRELATION_FIX.md` - Key fix
- `SCHEMA_FIX_SUMMARY.md` - Schema fixes
- `CLOCK_CHANGE_ANALYSIS_NOTE.md` - DST handling
- `FINAL_SUMMARY.md` - Project summary
- `CHANGELOG.md` - Change log

---

## 🔍 Finding Archived Documentation

### Quick Search
```bash
# Search all archived docs
grep -r "search term" docs/archive/

# Find files by name
find docs/archive/ -name "*keyword*.md"

# List all archived docs
find docs/archive/ -name "*.md" | sort
```

### By Category
```bash
# Historical features
ls docs/archive/historical/

# Resolved issues
ls docs/archive/issues/

# Process/session docs
ls docs/archive/process/

# References
ls docs/archive/references/
```

---

## 📋 Archive Statistics

- **Total Archived**: 367 markdown files
- **Remaining Active**: 35 markdown files
- **Reduction**: 91% cleanup (402 → 35)
- **Archive Date**: November 18, 2025

### By Category
| Category | Files | Purpose |
|----------|-------|---------|
| Historical | 185+ | Completed features |
| References | 60+ | Supplementary docs |
| Process | 40+ | Development sessions |
| Issues | 30+ | Resolved problems |
| Dashboard-old | 30+ | Old dashboards |
| ChatGPT-old | 25+ | Old ChatGPT docs |
| Deployment-old | 20+ | Old deployments |

---

## ⚠️ Important Notes

1. **Don't Delete**: These docs contain valuable historical context
2. **Reference Only**: Use for understanding past decisions/implementations
3. **Not Current**: Information may be outdated - refer to root docs for current info
4. **Searchable**: All content remains searchable via grep/find
5. **Git History**: Full history preserved in git commits

---

## 🔄 Restoration

If you need to restore a file to root:

```bash
# Find the file
find docs/archive/ -name "FILENAME.md"

# Move back to root
mv docs/archive/category/FILENAME.md .
```

---

## 📚 Related Documentation

- **Active Docs**: See root directory (35 files)
- **Master Index**: `/DOCUMENTATION_INDEX.md` in root
- **Configuration**: `/PROJECT_CONFIGURATION.md` in root

---

*Archive Created: November 18, 2025*  
*Maintained By: George Major*  
*Purpose: Keep project organized and navigable*
