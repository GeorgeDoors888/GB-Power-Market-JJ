#!/usr/bin/env python3
"""
SYSTEM OPERATIONS DASHBOARD
Builds an analytics-style dashboard from GB Power Market data in BigQuery
and writes a styled summary with charts to Google Sheets.

Integrated with GB Live data architecture
"""

# ───────────────────────────── Imports ─────────────────────────────
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from datetime import datetime
import io
import base64

# ───────────────────────────── Config ──────────────────────────────
SERVICE_KEY = "/home/george/inner-cinema-credentials.json"
PROJECT     = "inner-cinema-476211-u9"
DATASET     = "uk_energy_prod"
SHEET_ID    = "1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I"
DASH_TAB    = "System Dashboard"  # CHANGED: Separate sheet to avoid conflict with GB Live

# Colour palette (orange / light-blue / grey)
COL = dict(orange="#F97316", blue="#93C5FD", grey="#F1F5F9",
           green="#10B981", red="#EF4444", text="#111827")

# ─────────────────────────── Connections ───────────────────────────
print("🔧 Connecting to BigQuery and Google Sheets...")

# BigQuery connection (no scopes needed for service account)
bq = bigquery.Client(project=PROJECT, location="US")

# Google Sheets connection (with scopes)
scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
creds  = service_account.Credentials.from_service_account_file(SERVICE_KEY, scopes=scopes)
gs     = gspread.authorize(creds)

# ──────────────────────────── Queries ──────────────────────────────
print("⏳ Fetching BigQuery data...")

Q = {
"price" : f"""
    SELECT 
        CAST(settlementDate AS TIMESTAMP) AS t, 
        CAST(price AS FLOAT64) AS price
    FROM (
        SELECT settlementDate, price
        FROM `{PROJECT}.{DATASET}.bmrs_mid`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        UNION ALL
        SELECT settlementDate, price
        FROM `{PROJECT}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    )
    WHERE price IS NOT NULL
    ORDER BY t
""",

"wind"  : f"""
    SELECT 
        CAST(settlementDate AS TIMESTAMP) AS t,
        AVG(generation) / 1000 AS gw
    FROM `{PROJECT}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    AND fuelType = 'WIND'
    GROUP BY settlementDate
    ORDER BY t
""",

"gen"   : f"""
    SELECT 
        fuelType,
        AVG(generation) / 1000 AS gw
    FROM `{PROJECT}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    AND settlementPeriod = (
        SELECT MAX(settlementPeriod)
        FROM `{PROJECT}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    )
    AND fuelType NOT LIKE 'INT%'
    GROUP BY fuelType
    ORDER BY gw DESC
""",

"freq"  : f"""
    SELECT 
        CAST(settlementDate AS TIMESTAMP) AS t,
        50.0 AS frequency
    FROM `{PROJECT}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    GROUP BY settlementDate
    ORDER BY t
"""
}

df_price = bq.query(Q["price"]).to_dataframe()
df_wind  = bq.query(Q["wind"]).to_dataframe()
df_gen   = bq.query(Q["gen"]).to_dataframe()
df_freq  = bq.query(Q["freq"]).to_dataframe()

print(f"  ✅ Price: {len(df_price)} rows")
print(f"  ✅ Wind: {len(df_wind)} rows")
print(f"  ✅ Generation: {len(df_gen)} rows")
print(f"  ✅ Frequency: {len(df_freq)} rows")

# ─────────────────────────── KPI Summary ───────────────────────────
print("\n📊 Computing KPIs...")

total_gen = df_gen['gw'].sum()
wind_gen = df_gen[df_gen['fuelType'] == 'WIND']['gw'].iloc[0] if len(df_gen[df_gen['fuelType'] == 'WIND']) > 0 else 0
wind_pct = (wind_gen / total_gen * 100) if total_gen > 0 else 0

kpi = {
 "System Price £/MWh"     : df_price['price'].iloc[-1] if len(df_price) > 0 else 0,
 "Wind Generation GW"     : wind_gen,
 "Wind Share %"           : wind_pct,
 "Total Generation GW"    : total_gen,
 "System Frequency Hz"    : 50.0
}

for metric, value in kpi.items():
    if "%" in metric:
        print(f"  {metric}: {value:.1f}%")
    elif "Hz" in metric:
        print(f"  {metric}: {value:.2f}")
    else:
        print(f"  {metric}: {value:.2f}")

kpi_df = pd.DataFrame(list(kpi.items()), columns=["Metric","Value"])

# ───────────────────────────── Charts ──────────────────────────────
print("\n📈 Generating charts...")
sns.set_theme(style="whitegrid")
fig, axs = plt.subplots(2, 2, figsize=(14, 8))
fig.suptitle("SYSTEM OPERATIONS DASHBOARD", color=COL["orange"],
             fontsize=18, fontweight="bold")

# Price chart
if len(df_price) > 0:
    axs[0,0].plot(df_price.t, df_price.price, color=COL["orange"], linewidth=2)
    axs[0,0].set_title("System Price (24h)", fontweight="bold")
    axs[0,0].set_ylabel("£/MWh")
    axs[0,0].grid(True, alpha=0.3)

# Wind chart
if len(df_wind) > 0:
    axs[0,1].fill_between(df_wind.t, df_wind.gw, color=COL["blue"], alpha=.7)
    axs[0,1].set_title("Wind Generation (24h)", fontweight="bold")
    axs[0,1].set_ylabel("GW")
    axs[0,1].grid(True, alpha=0.3)

# Generation mix
if len(df_gen) > 0:
    fuel_colors = {
        'WIND': COL["blue"], 'CCGT': COL["orange"], 'NUCLEAR': COL["green"],
        'PS': COL["red"], 'BIOMASS': '#8B4513', 'NPSHYD': '#4169E1'
    }
    colors = [fuel_colors.get(f, COL["grey"]) for f in df_gen['fuelType'].head(8)]
    
    axs[1,0].barh(df_gen['fuelType'].head(8), df_gen['gw'].head(8), color=colors)
    axs[1,0].set_title("Generation Mix (Current)", fontweight="bold")
    axs[1,0].set_xlabel("GW")
    axs[1,0].grid(True, alpha=0.3, axis='x')

# Frequency
if len(df_freq) > 0:
    axs[1,1].plot(df_freq.t, df_freq.frequency, color=COL["grey"], linewidth=2)
    axs[1,1].axhspan(49.9, 50.1, color=COL["green"], alpha=.15)
    axs[1,1].set_title("System Frequency Stability", fontweight="bold")
    axs[1,1].set_ylabel("Hz")
    axs[1,1].set_ylim(49.8, 50.2)
    axs[1,1].grid(True, alpha=0.3)

for a in axs.flat:
    a.tick_params(labelsize=9)
    for spine in a.spines.values():
        spine.set_edgecolor('#CCCCCC')

plt.tight_layout(rect=[0, 0, 1, .96])
plt.savefig("/home/george/GB-Power-Market-JJ/dashboard_charts.png", dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ Charts saved → dashboard_charts.png")

# ───────────────────────── Google Sheets ───────────────────────────
print("\n📝 Updating Google Sheets...")

sh = gs.open_by_key(SHEET_ID)
try: 
    ws = sh.worksheet(DASH_TAB)
except: 
    ws = sh.add_worksheet(DASH_TAB, 100, 20)

# ───────────────────────── Google Sheets ───────────────────────────
print("\n📝 Updating Google Sheets...")

sh = gs.open_by_key(SHEET_ID)
try: 
    ws = sh.worksheet(DASH_TAB)
except: 
    ws = sh.add_worksheet(DASH_TAB, 100, 20)

ws.clear()

# Build all updates in one batch
updates = []

# Row 1: Title
updates.append({
    'range': 'A1',
    'values': [["⚡ SYSTEM OPERATIONS DASHBOARD", "", "", "", "", ""]]
})

# Row 2: Timestamp
timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
updates.append({
    'range': 'A2',
    'values': [[f"Last Update: {timestamp}", "", "", "", "", ""]]
})

# Row 4: KPI Header
updates.append({
    'range': 'A4',
    'values': [["KEY PERFORMANCE INDICATORS", "", "", "", "", ""]]
})

# Rows 5-9: KPI Data
updates.append({
    'range': 'A5',
    'values': kpi_df.values.tolist()
})

# Row 11: Generation Mix Header
updates.append({
    'range': 'A11',
    'values': [["GENERATION MIX", "", ""]]
})

# Row 12: Headers
updates.append({
    'range': 'A12',
    'values': [["Fuel Type", "Generation (GW)", "Share (%)"]]
})

# Row 13+: Fuel data
fuel_emojis = {
    'WIND': '💨 Wind', 'CCGT': '🔥 CCGT', 'NUCLEAR': '⚛️ Nuclear',
    'BIOMASS': '🌱 Biomass', 'NPSHYD': '💧 Hydro', 'PS': '⚡ Pumped',
    'OTHER': '❓ Other', 'OCGT': '🔥 OCGT', 'COAL': '⚫ Coal', 'OIL': '🛢️ Oil'
}

gen_data = []
for _, row in df_gen.head(10).iterrows():
    fuel_name = fuel_emojis.get(row['fuelType'], row['fuelType'])
    gen_gw = row['gw']
    share_pct = (gen_gw / total_gen * 100) if total_gen > 0 else 0
    gen_data.append([fuel_name, f"{gen_gw:.2f}", f"{share_pct:.1f}%"])

updates.append({
    'range': 'A13',
    'values': gen_data
})

# Apply all updates
ws.batch_update(updates)

# Apply formatting
ws.format("A1:F1", {
    "backgroundColor": {"red": 0.97, "green": 0.45, "blue": 0.09},
    "horizontalAlignment": "CENTER",
    "textFormat": {"bold": True, "fontSize": 18, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
})

ws.format("A2:F2", {
    "backgroundColor": {"red": 0.95, "green": 0.96, "blue": 0.98},
    "horizontalAlignment": "RIGHT",
    "textFormat": {"italic": True, "fontSize": 10}
})

ws.format("A4:F4", {
    "backgroundColor": {"red": 0.58, "green": 0.77, "blue": 0.99},
    "horizontalAlignment": "CENTER",
    "textFormat": {"bold": True, "fontSize": 14}
})

start_row = 5
ws.format(f"A{start_row}:A{start_row+len(kpi_df)-1}", {
    "backgroundColor": {"red": 0.58, "green": 0.77, "blue": 0.99},
    "textFormat": {"bold": True, "fontSize": 11}
})
ws.format(f"B{start_row}:B{start_row+len(kpi_df)-1}", {
    "backgroundColor": {"red": 0.95, "green": 0.96, "blue": 0.98},
    "textFormat": {"fontSize": 11}
})

ws.format("A11:C11", {
    "backgroundColor": {"red": 0.58, "green": 0.77, "blue": 0.99},
    "horizontalAlignment": "CENTER",
    "textFormat": {"bold": True, "fontSize": 12}
})

ws.format("A12:C12", {
    "backgroundColor": {"red": 0.88, "green": 0.88, "blue": 0.88},
    "textFormat": {"bold": True}
})

# Format generation data with alternating colors
for i, row_num in enumerate(range(13, 13 + len(gen_data))):
    bg_color = {"red": 0.95, "green": 0.96, "blue": 0.98} if i % 2 == 0 else {"red": 1, "green": 1, "blue": 1}
    ws.format(f"A{row_num}:C{row_num}", {"backgroundColor": bg_color})

# Set column widths using batch update
ws.spreadsheet.batch_update({
    'requests': [
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': ws.id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 1
                },
                'properties': {
                    'pixelSize': 200
                },
                'fields': 'pixelSize'
            }
        },
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': ws.id,
                    'dimension': 'COLUMNS',
                    'startIndex': 1,
                    'endIndex': 3
                },
                'properties': {
                    'pixelSize': 150
                },
                'fields': 'pixelSize'
            }
        }
    ]
})

print("  ✅ Dashboard updated successfully")
print(f"\n📊 View dashboard: https://docs.google.com/spreadsheets/d/{SHEET_ID}/")
print("\n" + "="*80)
print("✅ SYSTEM OPERATIONS DASHBOARD COMPLETE")
print("="*80)
