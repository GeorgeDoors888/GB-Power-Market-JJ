# 🔄 Dashboard Apps Script - Quick Reference

## 📋 One-Time Setup (5 minutes)

1. **Open**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
2. **Extensions** → **Apps Script**
3. **Paste** all 246+ lines from `gb_energy_dashboard_apps_script.gs`
4. **Save** (Cmd/Ctrl+S) as "GB Energy Dashboard Manager"
5. **Run** `setupDashboard()` function (dropdown → Run)
6. **Grant** permissions (Review → Advanced → Allow)
7. **Reload** the sheet to see custom menu

---

## 🔄 How to Refresh Data

### **Option 1: Manual Button (Recommended)**
```
Google Sheet → 🔄 Dashboard menu → Refresh Data Now
```
✅ Shows success/error alert

### **Option 2: Auto-Refresh**
```
Runs automatically every 15 minutes
```
✅ Set up by `setupDashboard()` function

### **Option 3: Apps Script Editor**
```
Extensions → Apps Script → Select refreshData → Run
```
✅ Good for debugging

### **Option 4: ChatGPT**
```
Prompt: "Refresh the dashboard"
```
✅ Returns instructions and direct link

---

## 📊 What Gets Updated

- ✅ **Dashboard sheet** synced from Sheet1
- ✅ **Chart** updated with latest data
- ✅ **Flags** fixed (e.g., �🇴 → 🇳🇴)
- ✅ **Last Updated** timestamp

---

## 🎯 Available Functions

| Function | Description |
|----------|-------------|
| `setupDashboard()` | Run once after pasting script |
| `refreshData()` | Auto-triggered every 15 min |
| `manualRefresh()` | Called by menu button |
| `showLogs()` | Show dashboard info |

---

## 🐛 Troubleshooting

**Menu not showing?** → Reload sheet (Cmd/Ctrl+R)  
**Permission error?** → Delete triggers, run setup again  
**Chart missing?** → Check column headers match expected names  
**Trigger not running?** → Apps Script → ⏰ Triggers → Verify exists

---

## 🔗 Useful Links

- **Google Sheet**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
- **API Endpoint**: https://94.237.55.15/sheets/run-apps-script
- **Full Guide**: `APPS_SCRIPT_DEPLOYMENT_GUIDE.md`
- **ChatGPT GPT**: https://chatgpt.com/g/g-690c89d2e338819180a9ab96a71e082f-gb-power-market-api

---

## 🎊 Success Checklist

- [ ] Script pasted in Apps Script
- [ ] `setupDashboard()` run successfully
- [ ] Permissions granted
- [ ] "🔄 Dashboard" menu appears
- [ ] "Refresh Data Now" button works
- [ ] Chart shows "Market Overview"
- [ ] Flags fixed (🇳🇴 🇫🇷 🇧🇪 etc.)
- [ ] Trigger exists (⏰ Triggers)
- [ ] ChatGPT can call endpoint

---

**⏱️ Total Setup Time:** ~5 minutes  
**📚 Full Guide:** See `APPS_SCRIPT_DEPLOYMENT_GUIDE.md`
