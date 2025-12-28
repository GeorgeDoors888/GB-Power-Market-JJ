# 🗑️ Deprecated Code Cleanup Plan
**Date**: 23 December 2025  
**Purpose**: Archive redundant/outdated scripts identified in code audit

---

## 📂 ACTIVE SCRIPTS (KEEP)

### **Python - Primary**
- ✅ `update_live_metrics.py` - Main dashboard updater (runs every 5 min)
- ✅ `build_publication_table_current.py` - Publication table builder (needs cron)
- ✅ `unified_dashboard_refresh.py` - Master refresh script (4am daily)

### **Apps Script - Active**
- ✅ `clasp-gb-live-2/src/Code.gs` - Main menu and setup
- ✅ `clasp-gb-live-2/src/Data.gs` - Data display (interconnector names only)
- ✅ `clasp-gb-live-2/src/Charts.gs` - Embedded charts (wind forecast)
- ✅ `clasp-gb-live-2/src/KPISparklines.gs` - Row 4 sparklines
- ✅ `clasp-gb-live-2/src/Dashboard.gs` - Dashboard utilities
- ✅ `clasp-gb-live-2/src/Menu.gs` - Custom menus

### **BESS Scripts - Active**
- ✅ `bess_auto_trigger.gs` - Webhook trigger for DNO lookup
- ✅ `bess_custom_menu.gs` - BESS sheet menu
- ✅ `bess_dno_lookup.gs` - DNO lookup Apps Script
- ✅ `dno_lookup_python.py` - DNO lookup Python backend
- ✅ `dno_webhook_server.py` - Flask webhook receiver

---

## 🗂️ DEPRECATED SCRIPTS TO ARCHIVE

### **Category 1: Old Dashboard Updaters** (157 files!)

**Superseded by**: `update_live_metrics.py`

```bash
# Create archive directory
mkdir -p archive/deprecated_dashboard_scripts_20251223

# Move old dashboard scripts
mv update_iris_dashboard.py archive/deprecated_dashboard_scripts_20251223/
mv update_fr_dashboard.py archive/deprecated_dashboard_scripts_20251223/
mv update_live_dashboard_v2_outages.py archive/deprecated_dashboard_scripts_20251223/
mv update_bess_dashboard.py archive/deprecated_dashboard_scripts_20251223/
mv update_dashboard_*.py archive/deprecated_dashboard_scripts_20251223/
mv enhanced_dashboard_updater.py archive/deprecated_dashboard_scripts_20251223/
mv unified_dashboard_updater.py archive/deprecated_dashboard_scripts_20251223/
mv fix_dashboard_*.py archive/deprecated_dashboard_scripts_20251223/
mv enhance_dashboard_comprehensive.py archive/deprecated_dashboard_scripts_20251223/
mv refresh_dashboard_complete.py archive/deprecated_dashboard_scripts_20251223/
mv redesign_dashboard_complete.py archive/deprecated_dashboard_scripts_20251223/
mv comprehensive_dashboard_update.py archive/deprecated_dashboard_scripts_20251223/
mv complete_dashboard_fix.py archive/deprecated_dashboard_scripts_20251223/
mv add_*_to_dashboard.py archive/deprecated_dashboard_scripts_20251223/
```

**Key Deprecated Scripts**:
- `update_iris_dashboard.py` - Old IRIS updater
- `update_fr_dashboard.py` - Old frequency updater
- `enhanced_dashboard_updater.py` - Superseded by update_live_metrics.py
- `enhance_dashboard_comprehensive.py` - Contains wind forecast code (may need migration)
- `unified_dashboard_updater.py` - Different from unified_dashboard_refresh.py
- `fix_dashboard_*.py` (20+ variants) - One-time fixes
- `add_*_to_dashboard.py` (30+ scripts) - One-time additions

### **Category 2: Old Apps Script Files**

**Superseded by**: `clasp-gb-live-2/src/*.gs`

```bash
mkdir -p archive/deprecated_apps_script_20251223

# Root directory .gs files
mv APPS_SCRIPT_INSTALLATION.gs archive/deprecated_apps_script_20251223/
mv Code_V3_Hybrid.gs archive/deprecated_apps_script_20251223/
mv EMERGENCY_FIX_B3.gs archive/deprecated_apps_script_20251223/
mv apps_script_code.gs archive/deprecated_apps_script_20251223/
mv apps_script_map_updater.gs archive/deprecated_apps_script_20251223/
mv google_sheets_dashboard.gs archive/deprecated_apps_script_20251223/
mv google_sheets_dashboard_v2.gs archive/deprecated_apps_script_20251223/
mv google_sheets_menu.gs archive/deprecated_apps_script_20251223/
mv redesign_live_dashboard.gs archive/deprecated_apps_script_20251223/

# Already archived directories (keep as-is)
# - apps-script-archive/
# - apps-script/
# - appsscript_v3/
# - backups/
# - bess-apps-script/ (duplicates of active bess_*.gs files)
```

### **Category 3: Duplicate Sparkline Generators**

**Analysis Required**:
```bash
grep -r "def.*sparkline" *.py | grep -v "update_live_metrics.py" | grep -v "__pycache__"
```

**Candidates** (need verification):
- Check if any other scripts have `generate_gs_sparkline_*` functions
- If duplicates exist, archive those scripts

### **Category 4: Verification/Debug Scripts**

**One-Time Use** (safe to archive):
```bash
mkdir -p archive/debug_verification_scripts_20251223

mv verify_dashboard_*.py archive/debug_verification_scripts_20251223/
mv check_dashboard*.py archive/debug_verification_scripts_20251223/
mv analyze_dashboard_layout.py archive/debug_verification_scripts_20251223/
mv read_dashboard_full.py archive/debug_verification_scripts_20251223/
mv trigger_dashboard_setup.py archive/debug_verification_scripts_20251223/
mv tools/debug_dashboard_read.py archive/debug_verification_scripts_20251223/
mv tools/fix_dashboard_comprehensive.py archive/debug_verification_scripts_20251223/
mv tools/update_dashboard_display.py archive/debug_verification_scripts_20251223/
mv tools/refresh_live_dashboard.py archive/debug_verification_scripts_20251223/
```

### **Category 5: Lock/Unlock Scripts**

**Superseded**: Dashboard no longer uses protection/locking
```bash
mv lock_dashboard.py archive/debug_verification_scripts_20251223/
```

---

## 🎯 CLEANUP EXECUTION PLAN

### **Phase 1: Safety Checks** (15 min)
```bash
cd /home/george/GB-Power-Market-JJ

# 1. Create backup of entire directory
tar -czf ~/GB-Power-Market-JJ-backup-$(date +%Y%m%d_%H%M%S).tar.gz .

# 2. Verify active script is working
python3 update_live_metrics.py

# 3. Check unified_dashboard_refresh.py
cat unified_dashboard_refresh.py | grep SCRIPTS
```

### **Phase 2: Create Archive Structure** (5 min)
```bash
mkdir -p archive/deprecated_dashboard_scripts_20251223
mkdir -p archive/deprecated_apps_script_20251223
mkdir -p archive/debug_verification_scripts_20251223
```

### **Phase 3: Move Dashboard Scripts** (10 min)
```bash
# Move all update_*dashboard*.py except update_live_metrics.py
find . -maxdepth 1 -name "*dashboard*.py" ! -name "update_live_metrics.py" ! -name "unified_dashboard_refresh.py" -exec mv {} archive/deprecated_dashboard_scripts_20251223/ \;

# Move add_*_to_dashboard.py scripts
find . -maxdepth 1 -name "add_*_to_dashboard.py" -exec mv {} archive/deprecated_dashboard_scripts_20251223/ \;

# Move fix/enhance/redesign scripts
find . -maxdepth 1 -name "fix_dashboard*.py" -exec mv {} archive/deprecated_dashboard_scripts_20251223/ \;
find . -maxdepth 1 -name "enhance_dashboard*.py" -exec mv {} archive/deprecated_dashboard_scripts_20251223/ \;
find . -maxdepth 1 -name "redesign_dashboard*.py" -exec mv {} archive/deprecated_dashboard_scripts_20251223/ \;
```

### **Phase 4: Move Apps Script Files** (5 min)
```bash
# Move root .gs files (except active BESS scripts)
find . -maxdepth 1 -name "*.gs" ! -name "bess_*.gs" -exec mv {} archive/deprecated_apps_script_20251223/ \;
```

### **Phase 5: Move Debug/Verification Scripts** (5 min)
```bash
find . -maxdepth 1 -name "verify_dashboard*.py" -exec mv {} archive/debug_verification_scripts_20251223/ \;
find . -maxdepth 1 -name "check_dashboard*.py" -exec mv {} archive/debug_verification_scripts_20251223/ \;
find . -maxdepth 1 -name "analyze_dashboard*.py" -exec mv {} archive/debug_verification_scripts_20251223/ \;
mv lock_dashboard.py archive/debug_verification_scripts_20251223/ 2>/dev/null || true
mv read_dashboard_full.py archive/debug_verification_scripts_20251223/ 2>/dev/null || true
mv trigger_dashboard_setup.py archive/debug_verification_scripts_20251223/ 2>/dev/null || true
```

### **Phase 6: Verification** (5 min)
```bash
# Count moved files
echo "Dashboard scripts archived: $(ls archive/deprecated_dashboard_scripts_20251223/ | wc -l)"
echo "Apps Script files archived: $(ls archive/deprecated_apps_script_20251223/ | wc -l)"
echo "Debug scripts archived: $(ls archive/debug_verification_scripts_20251223/ | wc -l)"

# Test active script still works
python3 update_live_metrics.py

# List remaining dashboard-related files in root
ls -1 *dashboard*.py
```

---

## 📋 POST-CLEANUP VERIFICATION

### **Expected Active Files Remaining**:
```
update_live_metrics.py          # Main updater
unified_dashboard_refresh.py    # Master refresh
build_publication_table_current.py  # Publication builder
realtime_dashboard_updater.py   # Auto-refresh daemon (if used)
```

### **Apps Script Active Directory**:
```
clasp-gb-live-2/src/
├── Code.gs
├── Data.gs
├── Charts.gs
├── KPISparklines.gs
├── Dashboard.gs
├── Menu.gs
└── appsscript.json
```

### **BESS Active Files**:
```
bess_auto_trigger.gs
bess_custom_menu.gs
bess_dno_lookup.gs
bess_hh_generator.gs
bess_webapp_api.gs
dno_lookup_python.py
dno_webhook_server.py
```

---

## ⚠️ SPECIAL CASES

### **enhance_dashboard_comprehensive.py** - DO NOT DELETE YET
**Reason**: Contains wind forecast code (lines 299-371)
**Action**: Extract wind forecast function before archiving
**Status**: Needs migration to update_live_metrics.py OR add to cron as-is

### **unified_dashboard_updater.py** vs **unified_dashboard_refresh.py**
**Issue**: Similar names, different purposes
**Keep**: `unified_dashboard_refresh.py` (in cron at 4am)
**Archive**: `unified_dashboard_updater.py` (check if it's actually different first)

### **build_publication_table_*.py** Variants
**Check for**:
- `build_publication_table_current.py` ✅ KEEP
- `build_publication_table_fixed.py` - Check if duplicate

---

## 🔄 ROLLBACK PROCEDURE

If cleanup causes issues:
```bash
cd /home/george/GB-Power-Market-JJ

# Restore specific script
cp archive/deprecated_dashboard_scripts_20251223/script_name.py ./

# Or restore entire backup
cd ~
tar -xzf GB-Power-Market-JJ-backup-YYYYMMDD_HHMMSS.tar.gz -C /home/george/GB-Power-Market-JJ-restore
```

---

## 📊 ESTIMATED CLEANUP IMPACT

- **Dashboard scripts**: ~157 files → Archive ~150, Keep ~7
- **Apps Script files**: ~30 root .gs files → Archive ~25, Keep ~5 (BESS)
- **Debug/verification**: ~20 files → Archive all
- **Total disk space saved**: ~50-100 MB
- **Reduced clutter**: ~200 files moved to archive

---

## ✅ SUCCESS CRITERIA

1. `update_live_metrics.py` runs without errors
2. Google Sheets dashboard updates correctly
3. No broken imports/dependencies
4. Cron jobs still function
5. BESS system still works
6. Root directory has <20 Python scripts (down from 200+)

---

*Cleanup plan created: 23 December 2025*  
*Review CODE_AUDIT_REPORT.md for conflict analysis*
