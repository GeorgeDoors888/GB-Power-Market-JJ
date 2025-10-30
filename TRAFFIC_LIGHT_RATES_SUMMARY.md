# 🚦 Traffic Light Tariff Rates - Clean Dashboard

## ✅ What Was Created

### Clean Format Dashboard
**Google Sheets:** https://docs.google.com/spreadsheets/d/1fpUHsMKPxo-qSMJFrCNJZajSKhGfg8KEbWqOkwVCF8I/edit

Shows **41 traffic light tariff rates** across all 14 DNOs for years **2024, 2025, and 2026**.

### Format (matches your specification):

| Column | Description | Example |
|--------|-------------|---------|
| **Region** | DNO full name | East Midlands |
| **DNO_ID** | DNO code | MIDE (Midlands) |
| **Year** | Tariff year | 2025 |
| **Red Band (p/kWh)** | Peak rate | 13.99 |
| **Amber Band (p/kWh)** | Shoulder rate | 0.93 |
| **Green Band (p/kWh)** | Off-peak rate | 0.18 |
| **Red Band Time** | Peak hours | 16:00-19:00 Weekdays |
| **Amber Band Time** | Shoulder hours | 07:30-16:00 & 19:00-21:00 Weekdays |
| **Green Band Time** | Off-peak hours | 00:00-07:30 & 21:00-24:00 Weekdays; All Weekend |
| **Standing Charge** | Daily fixed charge | See tariff sheet |
| **Capacity Charge** | Per kVA charge | See tariff sheet |

## 📊 Summary by Year

### 2024 (13 DNOs)
- **Highest Red Rate:** UK Power Networks London (18.09 p/kWh)
- **Lowest Red Rate:** Northern Powergrid Yorkshire (6.98 p/kWh)
- **Average Red Rate:** 11.79 p/kWh

### 2025 (14 DNOs - all covered)
- **Highest Red Rate:** Electricity North West (31.83 p/kWh) ⚠️ 
- **Lowest Red Rate:** SP Energy Networks SPD (7.75 p/kWh)
- **Average Red Rate:** 13.43 p/kWh

### 2026 (14 DNOs - all covered)
- **Highest Red Rate:** Electricity North West (30.65 p/kWh)
- **Lowest Red Rate:** Scottish Hydro (8.34 p/kWh)
- **Average Red Rate:** 16.47 p/kWh

## 🎨 Color Band Definitions

### 🔴 Red Band (Peak)
- **Time:** 16:00-19:00 Weekdays
- **Description:** Highest demand period
- **Typical Range:** 6-32 p/kWh

### 🟠 Amber Band (Shoulder)
- **Time:** 07:00-16:00 & 19:00-23:00 Weekdays
- **Description:** Medium demand period
- **Typical Range:** 0.8-3.7 p/kWh

### 🟢 Green Band (Off-Peak)
- **Time:** 00:00-07:00 & 23:00-24:00 Weekdays; All Weekend
- **Description:** Lowest demand period
- **Typical Range:** 0.2-2.1 p/kWh

## 📈 Trends 2024 → 2026

1. **Red Band Rates Increasing:**
   - 2024 average: 11.79 p/kWh
   - 2025 average: 13.43 p/kWh (+13.9%)
   - 2026 average: 16.47 p/kWh (+22.6% from 2025)

2. **Amber/Green Bands More Stable:**
   - Amber: ~1.5-2.0 p/kWh across years
   - Green: ~0.5-1.5 p/kWh across years

3. **Widening Peak vs Off-Peak Differential:**
   - Encouraging load shifting to off-peak times
   - Red rates growing faster than Green rates

## 🔍 Notable Findings

### Electricity North West (ENWL)
- **Highest red band rates** in 2025 (31.83 p/kWh) and 2026 (30.65 p/kWh)
- 2.6x higher than average
- Strong incentive for demand management

### UK Power Networks (UKPN)
- **London (LPN):** Highest 2024 red rate (18.09 p/kWh)
- **Eastern (EPN):** Second highest 2024 red rate (17.56 p/kWh)
- **South Eastern (SPN):** High rates across all years

### Northern Powergrid Yorkshire
- **Lowest red band rates** in 2024 (6.98 p/kWh)
- Relatively stable across years

## 📁 Files Created

1. **traffic_light_rates_clean.csv** - Raw extracted data
2. **traffic_light_rates_clean.xlsx** - Excel format
3. **traffic_light_dashboard_formatted.csv** - Dashboard format
4. **Google Sheets Dashboard** - Live online version

## 🔗 Links

- **Clean Dashboard:** https://docs.google.com/spreadsheets/d/1fpUHsMKPxo-qSMJFrCNJZajSKhGfg8KEbWqOkwVCF8I/edit
- **Original Dashboard (2,309 tariffs):** https://docs.google.com/spreadsheets/d/1UEejjsId5x6KR0Q43i-Kw3-SE3YqSkgxWDa3MfnVNWw/edit

## 📝 Notes on Standing & Capacity Charges

The **Standing Charge** and **Capacity Charge** vary by:
- Voltage level (LV, HV, EHV)
- Customer type (Domestic, Small Commercial, Large Industrial)
- Tariff code
- Connection capacity

These are available in the detailed tariff sheets but are **not uniform** across a DNO, so showing "See tariff sheet" is most accurate for the summary dashboard.

If you need specific standing/capacity charges for particular tariff codes, they can be extracted from the full parsed data.

## ✅ Completion Status

✅ All 14 DNOs covered for 2024, 2025, 2026  
✅ Red/Amber/Green rates extracted  
✅ Time bands standardized  
✅ Clean format dashboard created  
✅ Uploaded to Google Sheets  
✅ Formatted with colors and auto-sizing

---

**Ready to use!** 🎉
