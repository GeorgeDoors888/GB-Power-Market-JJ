# VLP Revenue Dashboard - Quick Reference

## 🚀 TL;DR - Get Started in 5 Minutes

```bash
# 1. Run deployment script
./deploy_vlp_dashboard.sh

# 2. Enable BigQuery Advanced Service (when prompted)
# Open Apps Script → Services → Enable "BigQuery API"

# 3. Create dashboard (in Google Sheets)
# Menu: ⚡ Energy Tools → 💰 VLP Revenue → 📊 Create VLP Dashboard

# 4. Enable auto-refresh (in Google Sheets)
# Menu: ⚡ Energy Tools → ⏱ Enable Auto-Refresh

# Done! Dashboard now updates every 5-30 minutes
```

**Dashboard URL**: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit

---

## 📊 What You'll See

### Live Ticker (updates every 5 min)
```
🟢 LIVE: GREEN | Market £72.56 | Revenue £342.07 | Profit £170.25/MWh | Signal: DISCHARGE_HIGH | 15:30:45
```

### 8 Revenue Streams
1. **PPA Discharge**: £150/MWh (base revenue)
2. **DC** (Dynamic Containment): £78.75/MWh (frequency response)
3. **DM** (Dynamic Moderation): £40.29/MWh (frequency support)
4. **DR** (Dynamic Regulation): £60.44/MWh (frequency regulation)
5. **CM** (Capacity Market): £12.59/MWh (capacity payments)
6. **BM** (Balancing Mechanism): £0-20/MWh (grid balancing)
7. **Triad Avoidance**: £40.29/MWh (peak demand reduction, Nov-Feb)
8. **Negative Pricing**: Variable (paid to consume)

### 4 Stacking Strategies
- **Conservative**: £599k/year (DC + CM + PPA) - Low risk
- **Balanced**: £749k/year (DC + DM + CM + PPA + BM) - Medium risk
- **Aggressive**: £999k/year (All 7 services) - High risk
- **Opportunistic**: £624k/year (DC + CM + PPA + Negative) - Event-driven

---

## 🎯 Trading Signals Explained

| Signal | Meaning | Action |
|--------|---------|--------|
| `DISCHARGE_HIGH` | Profit > £150/MWh | ✅ Discharge aggressively |
| `DISCHARGE_MODERATE` | Profit > £100/MWh | ✅ Discharge cautiously |
| `HOLD` | Profit £50-100/MWh | ⏸️ Wait for better opportunity |
| `CHARGE_OPPORTUNISTIC` | Price < £30/MWh | 🔋 Charge if cheap |
| `ARBITRAGE_WINDOW` | High spread expected | 💰 Prepare for next period |

---

## 🟢🟡🔴 DUoS Bands Explained

**GREEN** (00:00-08:00, 22:00-23:59 weekdays + all weekend):
- Cheapest costs (£0.038/kWh)
- Best profit margins (avg £163.65/MWh)
- 🟢 Optimal discharge window

**AMBER** (08:00-16:00, 19:30-22:00 weekdays):
- Moderate costs (£0.457/kWh)
- Good profit margins (avg £150.38/MWh)
- 🟡 Discharge if price high

**RED** (16:00-19:30 weekdays):
- Highest costs (£4.837/kWh for HV)
- Lower profit margins (avg £112.32/MWh)
- 🔴 Avoid discharge unless market price exceptional

---

## ⚙️ Menu Commands

### VLP Revenue Menu
- **📊 Create VLP Dashboard** - Initial sheet setup
- **🔄 Refresh VLP Data** - Manual refresh all sections
- **⚡ Update Live Ticker** - Refresh ticker only (fast)
- **📈 Show Stacking Analysis** - Pop-up with scenarios
- **🔗 Show Compatibility Matrix** - Pop-up with service compatibility

### Auto-Refresh Menu
- **⏱ Enable Auto-Refresh** - Create triggers (5-30 min intervals)
- **⏱ Disable Auto-Refresh** - Remove all triggers

---

## 🐍 Python Commands

```bash
# Manual refresh
python3 refresh_vlp_dashboard.py

# Check BigQuery access
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ OK')"

# Query latest data
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false \
"SELECT settlementDate, settlementPeriod, net_margin_per_mwh 
FROM \`inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs\` 
ORDER BY settlementDate DESC, settlementPeriod DESC LIMIT 1"
```

---

## 🔧 Common Issues

| Issue | Fix |
|-------|-----|
| "BigQuery API not enabled" | Apps Script → Services → Enable BigQuery API |
| "Access Denied" | Check `PROJECT_ID = "inner-cinema-476211-u9"` |
| "ModuleNotFoundError" | `pip3 install gspread google-cloud-bigquery` |
| Ticker shows "⚠️ DATA UNAVAILABLE" | IRIS feed down or auth issue |
| Zero prices | Known issue in Period 47 (investigating) |
| Auto-refresh not working | Re-run Enable Auto-Refresh, check triggers |

---

## 📖 Full Documentation

| File | Purpose |
|------|---------|
| **VLP_DASHBOARD_DEPLOYMENT.md** | Complete deployment guide |
| **PRICING_DATA_ARCHITECTURE.md** | IRIS vs historical pricing |
| **VLP_REVENUE_OUTPUT_SUMMARY.md** | Latest data analysis |
| **energy_dashboard_clasp/README.md** | Apps Script reference |

---

## 🆘 Emergency Contacts

**Zero prices detected**: Check `bmrs_mid_iris` table for NULL/zero entries  
**IRIS feed down**: SSH to AlmaLinux 94.237.55.234, check pipeline  
**BigQuery errors**: Verify project `inner-cinema-476211-u9`, dataset `uk_energy_prod`  
**Apps Script errors**: View → Executions (check error logs)

---

## 💡 Pro Tips

1. **Best discharge times**: GREEN band + DISCHARGE_HIGH signal = £160+/MWh profit
2. **Avoid RED band**: Unless market price > £150/MWh (high DUoS costs eat profit)
3. **Conservative strategy**: DC + CM + PPA = reliable £599k/year
4. **Aggressive strategy**: All 7 services = potential £999k/year (but conflicts possible)
5. **Service conflicts**: DC ✗ DR (can't run both), BM ⚠ DC/DM/DR (dispatch conflicts)

---

## 📊 Key Metrics to Watch

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Net Profit | > £150/MWh | £100-150/MWh | < £100/MWh |
| Active Services | 4-5/8 | 2-3/8 | 0-1/8 |
| Zero Prices | 0% | < 5% | > 5% |
| Data Freshness | < 10 min | 10-30 min | > 1 hour |

---

## 🔄 Update Frequency

| Component | Frequency | Method |
|-----------|-----------|--------|
| Live Ticker | 5 min | Apps Script trigger |
| Full Dashboard | 30 min | Apps Script trigger |
| Python Refresh | 30 min | Cron job (optional) |
| BigQuery View | Real-time | IRIS stream + batch |

---

*Last Updated: December 2, 2025*  
*Version: 1.0.0*
