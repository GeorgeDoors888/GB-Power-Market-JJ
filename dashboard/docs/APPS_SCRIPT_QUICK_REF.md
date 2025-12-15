# Apps Script Quick Reference Card

## 🚀 Installation (30 seconds)

1. Open sheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. **Extensions** → **Apps Script**
3. Copy/paste entire `google_sheets_dashboard.gs` file
4. **Save** (Cmd+S)
5. **Run** → `Setup_Dashboard_AutoRefresh`
6. **Authorize** when prompted
7. Done! Menu **⚡ Power Market** appears

---

## 📊 What It Does

- Pulls live GB power market data from BigQuery
- Updates every 5 minutes automatically
- Creates interactive charts
- Logs all activity to audit tab

---

## 🎛️ Menu Commands

| Command | What it does |
|---------|--------------|
| **🔄 Refresh Now** | Pull latest data (manual) |
| **📊 Rebuild Chart** | Fix/recreate dashboard chart |
| **⏰ Set Auto-Refresh** | Enable 5-min updates |
| **🛑 Stop Auto-Refresh** | Disable automatic updates |
| **🚀 One-Click Setup** | Full setup (first time) |

---

## 📈 Data Tabs Created

| Tab | Content |
|-----|---------|
| **Live Dashboard** | Main view (48 SPs × 10 columns) |
| **Chart Data** | Same as dashboard (for chart binding) |
| **Live_Raw_Prices** | SSP/SBP details |
| **Live_Raw_Gen** | Generation/demand details |
| **Live_Raw_BOA** | BOALF balancing actions |
| **Live_Raw_IC** | Interconnector flows |
| **Audit_Log** | Activity history (last 1000 events) |

---

## 🔧 Configuration

```javascript
VERCEL_PROXY = 'https://gb-power-market-jj.vercel.app/api/proxy-v2'
PROJECT = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TZ = 'Europe/London'
```

**Tables queried:**
- `bmrs_mid` - System prices
- `bmrs_indgen_iris` - Generation (boundary='N')
- `bmrs_inddem_iris` - Demand (boundary='N')
- `bmrs_boalf` - Balancing actions
- `bmrs_bod` - Bid-offer data

---

## 🐛 Quick Troubleshooting

| Problem | Fix |
|---------|-----|
| Menu not showing | Refresh sheet page |
| Authorization error | Re-authorize in Apps Script |
| No data in dashboard | Run **🔄 Refresh Now** first |
| Chart broken | Run **📊 Rebuild Chart** |
| Auto-refresh not working | Re-run **⏰ Set Auto-Refresh** |
| Slow/timeout | Reduce refresh frequency (10 min) |

**Check Audit_Log tab for detailed error messages**

---

## ✅ Verification

After setup, verify:
- [ ] Menu **⚡ Power Market** exists
- [ ] **Live Dashboard** has 48 rows
- [ ] Chart displays on dashboard
- [ ] SSP/SBP prices look realistic (£30-150)
- [ ] Demand/Gen values realistic (20,000-50,000 MW)
- [ ] Audit_Log shows successful refresh

---

## 🧪 Test Functions

Run from Apps Script editor:

**`testHealthCheck()`**
- Pings Vercel proxy
- Shows connection status
- Verifies endpoint is working

**`testSingleQuery()`**
- Runs sample BigQuery query
- Shows first result row
- Validates SQL syntax

---

## 📊 Data Columns

| Column | Description | Unit |
|--------|-------------|------|
| SP | Settlement Period (1-48) | - |
| Time | Clock time (00:00-23:30) | HH:MM |
| SSP £/MWh | System Sell Price | £/MWh |
| SBP £/MWh | System Buy Price | £/MWh |
| Demand MW | National demand | MW |
| Generation MW | National generation | MW |
| BOALF Actions | Balancing action count | count |
| BOD Offer £/MWh | Average offer price | £/MWh |
| BOD Bid £/MWh | Average bid price | £/MWh |
| IC Net MW | Net interconnector flow | MW |

---

## 🔒 Security

- ✅ No credentials in sheet
- ✅ Vercel proxy handles auth
- ✅ Read-only BigQuery access
- ✅ HTTPS only
- ✅ Sheet-scoped permissions

---

## 📝 Key Differences from Python Dashboard

| Feature | Python | Apps Script |
|---------|--------|-------------|
| Data source | Direct BigQuery | Vercel proxy → BigQuery |
| Speed | Fast | Slower (HTTP overhead) |
| Scheduling | GitHub Actions / cron | Apps Script triggers |
| Best for | Bulk updates | Live user dashboard |

**Use both:** Python for batch data loads, Apps Script for real-time dashboard

---

## 🆘 Common Errors

**"HTTP 500: FUNCTION_INVOCATION_FAILED"**
→ Wrong proxy endpoint (check uses `/api/proxy-v2`)

**"Table not found"**
→ Wrong project/dataset (check `inner-cinema-476211-u9.uk_energy_prod`)

**"Column not found"**
→ Schema mismatch (check camelCase: `settlementDate`, `settlementPeriod`)

**"Exceeded maximum execution time"**
→ Query too slow (reduce date range or split queries)

**"Service invoked too many times"**
→ Hit Apps Script quota (reduce refresh frequency)

---

## 📚 Documentation

- Full guide: `GOOGLE_SHEETS_APPS_SCRIPT_GUIDE.md`
- Code review: `APPS_SCRIPT_CODE_REVIEW.md`
- Source code: `google_sheets_dashboard.gs`

---

## ✨ Pro Tips

1. **Chart auto-updates** - Uses named range `NR_DASH_TODAY` (never breaks)
2. **Audit logging** - Check `Audit_Log` to track all activity
3. **Raw data tabs** - Use for debugging SQL queries
4. **Test functions** - Run before enabling auto-refresh
5. **One-click setup** - Fastest way to get started

---

**Last Updated:** 2025-11-07  
**Status:** ✅ Production Ready  
**Support:** Check Audit_Log → Review docs → Test functions
