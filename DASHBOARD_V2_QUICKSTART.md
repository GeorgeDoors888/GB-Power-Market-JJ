# 🎯 Dashboard v2 Quick Start

**Status:** ✅ Deployed  
**Script ID:** 19d9ooPFGTrzRERacvirLsL-LLWzAwGbUfc7WV-4SFhfF59pefOj8vvkA

---

## 🚀 Quick Start (3 Steps)

### 1. Open Google Sheet
https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit

### 2. Reload Page
Press **Cmd+R** (Mac) or **Ctrl+R** (Windows)

### 3. Run Setup
Click: **Dashboard → Setup (rename+sync+chart+trigger)**

✅ **Done!** Your dashboard will now auto-refresh every 15 minutes.

---

## 📋 Dashboard Menu

| Action | What It Does | When to Use |
|--------|-------------|-------------|
| **Setup** | Full initialization | First time / Reset |
| **Refresh data now** | Manual refresh | Immediate update needed |
| **Fix flags/labels** | Repair interconnector flags | Flags look broken |
| **Rebuild chart** | Recreate Market Overview chart | Chart missing/wrong |
| **Health check** | System diagnostics | Troubleshooting |

---

## 📊 What You Get

✅ **Market Overview Chart** - 5 series:
- System Sell Price (£/MWh)
- Demand (GW)
- Total Generation (GW)
- Wind Generation (GW)
- Expected Wind Generation (GW)

✅ **Auto-Refresh** - Every 15 minutes  
✅ **Data Normalization** - Clean formatting  
✅ **Flag Fixing** - 🇳🇴 🇫🇷 🇧🇪 🇳🇱 🇮🇪  
✅ **Audit Logging** - Full activity trail

---

## 🔍 Check It Worked

After running Setup:
- [x] "Dashboard" sheet exists
- [x] Chart visible on right side (row 2, col 8)
- [x] "Last Updated" in columns B/C
- [x] Audit_Log shows "setupDashboard | ok"

Wait 15 minutes:
- [x] Chart updates automatically
- [x] Audit_Log shows "refreshData | ok"

---

## 🆘 Quick Fixes

**Chart missing?**  
→ Dashboard → Rebuild Market Overview chart

**Flags broken?**  
→ Dashboard → Fix flags/labels

**Not auto-refreshing?**  
→ Dashboard → Setup (run again)

**Need diagnostics?**  
→ Dashboard → Health check → Check Audit_Log

---

## 📚 Full Documentation

See: `DASHBOARD_V2_GUIDE.md` for complete details

---

**Deployed:** 2025-11-08  
**Auto-Refresh:** Every 15 minutes  
**Status:** 🟢 Ready to use
