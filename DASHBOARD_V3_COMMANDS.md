# Dashboard V3 - Quick Command Reference

## 🚀 Setup (Run Once)

```bash
# Create VLP_Data, Market_Prices sheets + formulas + sparklines
python3 python/setup_dashboard_formulas.py
```

**Creates**:
- VLP_Data sheet (30 days balancing actions)
- Market_Prices sheet (30 days IRIS prices)  
- Dashboard V3 F10:L10 formulas
- Dashboard V3 F11:L11 sparklines

---

## 🔄 Manual Refresh

```bash
# Refresh ALL dashboard sections
python3 python/dashboard_v3_auto_refresh_with_data.py
```

**Updates**:
1. VLP_Data sheet → bmrs_boalf
2. Market_Prices sheet → bmrs_mid_iris
3. Fuel Mix (A10:C21) → bmrs_fuelinst_iris
4. Interconnectors (D10:E18) → bmrs_fuelinst_iris
5. Active Outages (A25:F35) → bmrs_remit_unavailability

---

## ⏰ Auto-Refresh (Cron Job)

```bash
# Install 15-minute auto-refresh
./install_dashboard_v3_cron_final.sh
```

**Cron Schedule**: `*/15 * * * *` (every 15 minutes)

**Monitor logs**:
```bash
tail -f logs/dashboard_v3_auto_refresh.log
```

**Remove cron job**:
```bash
crontab -e
# Delete line with "dashboard_v3_auto_refresh_with_data"
```

---

## 🔍 Verification

```bash
# Check dashboard KPIs (should show formulas)
python3 << 'EOF'
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    '/Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets = build('sheets', 'v4', credentials=creds)

result = sheets.spreadsheets().values().get(
    spreadsheetId='1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc',
    range='Dashboard V3!F10:L11',
    valueRenderOption='FORMULA'
).execute()

print("\n📊 Dashboard KPIs (formulas):")
for i, row in enumerate(result.get('values', []), 10):
    print(f"Row {i}: {row}")
EOF
```

---

## 📊 Expected Results

**KPIs (F10:L10)** should show:
- **F10**: `=IFERROR(AVERAGE(VLP_Data!C2:C31)/1000, 0)` → £0.04k
- **G10**: `=IFERROR(AVERAGE(Market_Prices!B2:B31), 0)` → £39.69/MWh
- **H10**: Volatility formula → 1470.95%
- **K10**: `=IFERROR(SUM(VLP_Data!B2:B31), 0)` → 2370 MWh

**Sparklines (F11:L11)** should show:
- **F11**: `=SPARKLINE(VLP_Data!C2:C31, {"charttype","column"})`
- **G11**: `=SPARKLINE(Market_Prices!B2:B31, {"charttype","line"})`
- **H11**: `=SPARKLINE(Market_Prices!E2:E31, {"charttype","column"})`

**Fuel Mix (A10:C21)** should show:
- CCGT: 15.28 GW (39.60%) - **properly formatted %**
- WIND: 14.74 GW (38.20%)

---

## 🐛 Troubleshooting

### KPIs show #REF! errors
**Cause**: VLP_Data or Market_Prices sheets missing  
**Fix**: Run `python3 python/setup_dashboard_formulas.py`

### KPIs show £0.00 / 0
**Cause**: Data sheets empty  
**Fix**: Run `python3 python/dashboard_v3_auto_refresh_with_data.py`

### Fuel Mix shows numbers without %
**Cause**: Wrong valueInputOption in refresh script  
**Fix**: Check script uses `valueInputOption='USER_ENTERED'` for column C

### Sparklines not showing
**Cause**: Formulas written as RAW values  
**Fix**: Check F11:L11 contains `=SPARKLINE(...)` formulas, not text

### VLP Revenue shows £0.04k (too low)
**Cause**: bmrs_boalf has no recent data (historical gap)  
**Fix**: Wait for IRIS data to populate, or acceptable if no VLP actions occurred

---

## 📁 File Structure

```
GB-Power-Market-JJ/
├── python/
│   ├── setup_dashboard_formulas.py          # One-time setup
│   └── dashboard_v3_auto_refresh_with_data.py  # Auto-refresh
├── install_dashboard_v3_cron_final.sh       # Cron installer
├── logs/
│   └── dashboard_v3_auto_refresh.log        # Cron output
└── DASHBOARD_V3_FINAL_SOLUTION.md           # Full documentation
```

---

## 🔗 Links

**Spreadsheet**: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/

**BigQuery Tables**:
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris` (prices)
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` (VLP actions)
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` (fuel mix)
- `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability` (outages)

---

*Last Updated: December 4, 2025*
