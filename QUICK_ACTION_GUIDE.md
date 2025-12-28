# ⚡ Quick Action Guide - Next Steps
**Date**: 23 December 2025  
**Purpose**: Fast-track execution of audit recommendations

---

## 🎯 WHAT'S DONE ✅

1. ✅ **Code audit complete** - All conflicts documented
2. ✅ **Python fixes deployed** - PYTHON_MANAGED flag, simplified KPIs
3. ✅ **Interconnector sparklines** - Line charts with auto-scaling
4. ✅ **Wind forecast fixed** - Ran build_publication_table_current.py
5. ✅ **Documentation created** - 4 comprehensive guides

---

## 🚀 WHAT'S NEXT (Choose Your Path)

### **Option A: Manual Apps Script Deployment** ⏱️ 10 min

**Quick Steps**:
1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Extensions → Apps Script
3. Open `Data.gs`
4. Find line ~228: `// Display Outages (v2 only)`
5. Wrap entire section in `/* ... */` comments
6. Save (Ctrl+S)
7. Run `addKPISparklinesManual()` from KPISparklines.gs

**Detailed Guide**: `MANUAL_DEPLOYMENT_GUIDE.md`

---

### **Option B: Execute Cleanup Plan** ⏱️ 45 min

**Quick Steps**:
```bash
cd /home/george/GB-Power-Market-JJ

# Safety backup first!
tar -czf ~/GB-Power-Market-JJ-backup-$(date +%Y%m%d_%H%M%S).tar.gz .

# Create archive structure
mkdir -p archive/deprecated_dashboard_scripts_20251223
mkdir -p archive/deprecated_apps_script_20251223
mkdir -p archive/debug_verification_scripts_20251223

# Move deprecated files (see plan for full commands)
find . -maxdepth 1 -name "*dashboard*.py" ! -name "update_live_metrics.py" ! -name "unified_dashboard_refresh.py" -exec mv {} archive/deprecated_dashboard_scripts_20251223/ \;

# Verify
ls archive/deprecated_dashboard_scripts_20251223/ | wc -l
python3 update_live_metrics.py  # Test still works
```

**Detailed Guide**: `DEPRECATED_CODE_CLEANUP_PLAN.md`

---

### **Option C: Fix Wind Forecast Permanently** ⏱️ 15 min

**Option C1 - Add to Cron** (Recommended):
```bash
crontab -e

# Add line (update publication table every 5 min):
*/5 * * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 build_publication_table_current.py >> logs/publication_table.log 2>&1
```

**Option C2 - Migrate to Python**:
- Extract wind forecast code from enhance_dashboard_comprehensive.py (lines 299-371)
- Add to update_live_metrics.py
- Deprecate Charts.gs wind forecast chart

**Option C3 - Remove Chart**:
- Comment out Charts.gs lines 85-120
- Remove wind forecast display entirely

---

### **Option D: Create Architecture Document** ⏱️ 30 min

**Template**:
```markdown
# GB Power Market JJ - System Architecture

## Data Flow
BigQuery IRIS Tables → Python (update_live_metrics.py) → Google Sheets

## Cell Ownership
- A2-A7: Python (system prices, timestamps)
- C4-I4: Apps Script KPISparklines.gs (sparklines)
- C6-K6: Python (KPI values)
- G13:H22: Python (interconnectors with sparklines)
- G25:K41: Python (active outages)
- L12-R67: Python (market metrics, VLP revenue)

## Update Schedule
- Every 5 min: update_live_metrics.py (cron)
- Daily 4am: unified_dashboard_refresh.py (cron)

## Scripts Status
- Active: 7 Python scripts + 6 Apps Script files
- Archived: 200+ deprecated scripts (see archive/)
```

---

## 📋 VERIFICATION CHECKLIST

After any changes, verify:

```bash
# Test Python script
cd /home/george/GB-Power-Market-JJ
python3 update_live_metrics.py

# Check logs
tail -f logs/dashboard_updater.log

# Verify spreadsheet cells
# - AA1 should show: PYTHON_MANAGED
# - C4, E4, G4, I4 should have sparklines
# - G25:K41 should show active outages
# - H13:H22 should show interconnector sparklines (line charts)
```

---

## 🆘 ROLLBACK COMMANDS

**If cleanup causes issues**:
```bash
# Restore specific script
cp archive/deprecated_dashboard_scripts_20251223/script_name.py ./

# Restore from backup
cd ~
tar -xzf GB-Power-Market-JJ-backup-YYYYMMDD_HHMMSS.tar.gz -C /home/george/GB-Power-Market-JJ-restore
```

**If Python changes cause issues**:
```bash
cd /home/george/GB-Power-Market-JJ
git diff update_live_metrics.py  # Review changes
git checkout update_live_metrics.py  # Revert
```

---

## 📞 QUICK REFERENCE

| Document | Purpose | Location |
|----------|---------|----------|
| CODE_AUDIT_REPORT.md | Full conflict analysis | `/home/george/GB-Power-Market-JJ/` |
| MANUAL_DEPLOYMENT_GUIDE.md | Apps Script steps | `/home/george/GB-Power-Market-JJ/` |
| DEPRECATED_CODE_CLEANUP_PLAN.md | File archival plan | `/home/george/GB-Power-Market-JJ/` |
| AUDIT_SUMMARY_REPORT.md | Session overview | `/home/george/GB-Power-Market-JJ/` |
| .github/copilot-instructions.md | Project overview | `/home/george/GB-Power-Market-JJ/.github/` |

---

## ⏰ TIME ESTIMATES

| Task | Time | Difficulty | Impact |
|------|------|------------|--------|
| Apps Script deployment | 10 min | Easy | High |
| Execute cleanup plan | 45 min | Medium | High |
| Fix wind forecast (cron) | 15 min | Easy | Medium |
| Fix wind forecast (migrate) | 2 hours | Hard | High |
| Create ARCHITECTURE.md | 30 min | Easy | Medium |
| Full cleanup + docs | 3 hours | Medium | Very High |

---

## 🎯 RECOMMENDED ORDER

**If you have 1 hour**:
1. Deploy Apps Script (10 min) ✅ Immediate value
2. Add wind forecast to cron (15 min) ✅ Fixes chart
3. Create ARCHITECTURE.md (30 min) ✅ Future reference

**If you have 3 hours**:
1. Deploy Apps Script (10 min)
2. Execute cleanup plan (45 min)
3. Add wind forecast to cron (15 min)
4. Create ARCHITECTURE.md (30 min)
5. Test everything (30 min)
6. Update copilot-instructions.md (30 min)

**If you have 15 minutes**:
1. Deploy Apps Script (10 min)
2. Verify dashboard updates (5 min)
3. Done! ✅

---

*Quick guide created: 23 December 2025*  
*All changes tested and documented*
