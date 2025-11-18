# 📚 Quick Documentation Reference Card

**Last Updated**: November 10, 2025, 16:45 GMT

---

## 🚨 **Need Help? Start Here:**

| I need... | Go to... |
|-----------|----------|
| **Quick overview** | [README.md](README.md) |
| **Configuration settings** | [PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md) |
| **All documentation** | [DOCUMENTATION_MASTER_INDEX.md](DOCUMENTATION_MASTER_INDEX.md) |
| **Today's changes** | [SESSION_SUMMARY_NOV_10_2025.md](SESSION_SUMMARY_NOV_10_2025.md) |

---

## 🎯 **By Task**

### **Dashboard**
- Fix flags: `python3 fix_interconnector_flags_permanent.py` (or wait for auto-fix)
- Update Dashboard: `python3 update_dashboard_preserve_layout.py`
- Check flags: `python3 verify_flags.py`
- **Docs**: [COMPREHENSIVE_REDESIGN_COMPLETE.md](COMPREHENSIVE_REDESIGN_COMPLETE.md)

### **BigQuery Queries**
- Dataset reference: [BIGQUERY_DATASET_REFERENCE.md](BIGQUERY_DATASET_REFERENCE.md) ⭐ NEW
- Schema gotchas: [STOP_DATA_ARCHITECTURE_REFERENCE.md](STOP_DATA_ARCHITECTURE_REFERENCE.md)
- VLP analysis: See BIGQUERY_DATASET_REFERENCE.md → VLP sections

### **Flag Issues**
- Technical guide: [FLAG_FIX_TECHNICAL_GUIDE.md](FLAG_FIX_TECHNICAL_GUIDE.md)
- Auto-verification: [AUTO_FLAG_VERIFICATION_COMPLETE.md](AUTO_FLAG_VERIFICATION_COMPLETE.md)
- **Good news**: Flags auto-fix on every update now! ✅

### **Deployment**
- IRIS pipeline: [IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md](IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md)
- ChatGPT setup: [CHATGPT_INSTRUCTIONS.md](CHATGPT_INSTRUCTIONS.md)
- Complete deployment: [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md)

### **Battery Analysis**
- BESS/VLP guide: [BESS_VLP_COMPLETE_GUIDE.md](BESS_VLP_COMPLETE_GUIDE.md)
- Data sources: [NESO_ELEXON_BATTERY_VLP_DATA_GUIDE.md](NESO_ELEXON_BATTERY_VLP_DATA_GUIDE.md)

---

## 📊 **Critical Information**

### **BigQuery**
- **Project**: `inner-cinema-476211-u9` (NOT jibber-jabber-knowledge!)
- **Dataset**: `uk_energy_prod`
- **Location**: `US` (NOT europe-west2!)

### **Dashboard**
- **URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
- **Update Script**: `update_dashboard_preserve_layout.py`
- **Flags**: Auto-verified every update ✅

### **Scripts**
- **Python**: Use `python3` (not `python` on macOS)
- **Credentials**: `inner-cinema-credentials.json`
- **BigQuery key**: `arbitrage-bq-key.json`

---

## 🆕 **What's New (November 10, 2025)**

✅ **Automatic Flag Verification**
- Built into all update scripts
- No manual intervention needed
- Self-healing system

✅ **BigQuery Dataset Reference**
- Complete 185-table guide
- BOD/VLP query examples
- Units & conventions documented

✅ **Documentation Organization**
- Master index of 331 files
- Categorized structure
- Automation script ready

---

## 🔧 **Common Commands**

```bash
# Update Dashboard (with auto flag-fix)
python3 update_dashboard_preserve_layout.py

# Update outages (with auto flag-fix)
python3 auto_refresh_outages.py

# Verify flags manually (optional)
python3 verify_flags.py

# Organize documentation
./organize_docs.sh

# Check table coverage
./check_table_coverage.sh TABLE_NAME
```

---

## 📁 **File Organization**

### **Current State**: 331 .md files in root
### **Recommended**: Organized into docs/ folders

**To organize**:
```bash
./organize_docs.sh
```

**Result**:
```
docs/
├── 00-START-HERE/    (Core)
├── 01-DASHBOARD/     (Dashboard)
├── 02-BIGQUERY/      (Data)
├── 03-IRIS-PIPELINE/ (Real-time)
├── 04-CHATGPT/       (AI)
├── 05-BESS-VLP/      (Batteries)
├── 06-MAPS/          (Maps)
├── 07-ANALYSIS/      (Analytics)
├── 08-API-DEPLOYMENT/(APIs)
├── 09-ARCHITECTURE/  (Design)
└── 10-ARCHIVE/       (Old)
```

---

## 🎯 **Priority Reading Order**

1. **MUST READ FIRST**:
   - README.md
   - PROJECT_CONFIGURATION.md

2. **Core References**:
   - COMPLETE_REFERENCE_GUIDE.md
   - STOP_DATA_ARCHITECTURE_REFERENCE.md

3. **Current Work**:
   - COMPREHENSIVE_REDESIGN_COMPLETE.md
   - BIGQUERY_DATASET_REFERENCE.md
   - AUTO_FLAG_VERIFICATION_COMPLETE.md

4. **As Needed**:
   - Everything else in DOCUMENTATION_MASTER_INDEX.md

---

## 📞 **Support**

- **Maintainer**: George Major
- **Email**: george@upowerenergy.uk
- **GitHub**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

---

## 💡 **Pro Tips**

✅ **Flags never break**: Auto-fixed on every update  
✅ **Use master index**: Find any doc in seconds  
✅ **Check session summaries**: See what changed when  
✅ **Run organize_docs.sh**: Clean up file structure  
✅ **Read BigQuery reference**: Everything you need for queries  

---

**Print this card** for quick access to all documentation!

**Last updated**: November 10, 2025, 16:45 GMT
