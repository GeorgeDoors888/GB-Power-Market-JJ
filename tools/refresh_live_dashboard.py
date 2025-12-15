#!/usr/bin/env python3
"""
Live GB Power Market Dashboard Refresh
Pulls data from BigQuery and writes to Google Sheets with named ranges
"""
import os, pytz, pandas as pd
from datetime import datetime
from google.cloud import bigquery
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LONDON = pytz.timezone("Europe/London")

# Use environment variables with sensible defaults
SHEET_ID = os.environ.get("SHEET_ID", "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
SA_PATH  = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "../inner-cinema-credentials.json")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS  = Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
sheets = build("sheets","v4",credentials=CREDS).spreadsheets()

# BigQuery client also needs credentials
bq = bigquery.Client(project=PROJECT, credentials=Credentials.from_service_account_file(SA_PATH))

SQL_PRICES = f"""
WITH prices AS (
  SELECT 
    DATE(settlementDate) AS d, 
    settlementPeriod AS sp,
    dataProvider,
    AVG(price) AS price
  FROM `{PROJECT}.{DATASET}.bmrs_mid`
  WHERE DATE(settlementDate) = @date
  GROUP BY d, sp, dataProvider
)
SELECT 
  sp,
  MAX(CASE WHEN dataProvider = 'N2EXMIDP' THEN price END) AS ssp,
  MAX(CASE WHEN dataProvider = 'APXMIDP' THEN price END) AS sbp
FROM prices
GROUP BY sp
ORDER BY sp
"""

SQL_GEN = f"""
WITH gen AS (
  SELECT 
    settlementPeriod AS sp,
    AVG(generation) AS gen_mw
  FROM `{PROJECT}.{DATASET}.bmrs_indgen_iris`
  WHERE DATE(settlementDate) = @date
    AND boundary = 'N'  -- National total (boundary codes: B1-B17 are regions, N is national)
  GROUP BY sp
),
dem AS (
  SELECT 
    settlementPeriod AS sp,
    ABS(AVG(demand)) AS demand_mw  -- Demand values are negative, take absolute value
  FROM `{PROJECT}.{DATASET}.bmrs_inddem_iris`  -- Use _iris table which has current data
  WHERE DATE(settlementDate) = @date
    AND boundary = 'N'  -- National total
  GROUP BY sp
)
SELECT 
  COALESCE(gen.sp, dem.sp) AS sp,
  gen.gen_mw,
  dem.demand_mw
FROM gen
FULL OUTER JOIN dem ON gen.sp = dem.sp
ORDER BY COALESCE(gen.sp, dem.sp)
"""

SQL_BOALF = f"""
SELECT 
  settlementPeriodFrom AS sp,
  COUNT(*) AS boalf_acceptances,
  AVG((levelTo - levelFrom)) AS boalf_avg_level_change
FROM `{PROJECT}.{DATASET}.bmrs_boalf`
WHERE DATE(settlementDate) = @date
GROUP BY sp
ORDER BY sp
"""

SQL_BOD = f"""
SELECT 
  settlementPeriod AS sp,
  AVG(CASE WHEN offer > 0 AND offer < 9000 THEN offer END) AS bod_offer_price,
  AVG(CASE WHEN bid > 0 AND bid < 9000 THEN bid END) AS bod_bid_price
FROM `{PROJECT}.{DATASET}.bmrs_bod`
WHERE DATE(settlementDate) = @date
GROUP BY sp
ORDER BY sp
"""

# Interconnectors - Calculate as difference between generation and demand
# Net interconnector flow = Generation - Demand (positive = net import to GB)
# This is derived rather than from a specific table since fuelinst tables are not updated
SQL_IC = f"""
WITH gen AS (
  SELECT 
    settlementPeriod AS sp,
    AVG(generation) AS gen_mw
  FROM `{PROJECT}.{DATASET}.bmrs_indgen_iris`
  WHERE DATE(settlementDate) = @date
    AND boundary = 'N'
  GROUP BY sp
),
dem AS (
  SELECT 
    settlementPeriod AS sp,
    ABS(AVG(demand)) AS demand_mw
  FROM `{PROJECT}.{DATASET}.bmrs_inddem_iris`
  WHERE DATE(settlementDate) = @date
    AND boundary = 'N'
  GROUP BY sp
)
SELECT 
  gen.sp,
  (gen.gen_mw - dem.demand_mw) AS ic_net_mw  -- Generation - Demand = net export (positive = export, negative = import)
FROM gen
INNER JOIN dem ON gen.sp = dem.sp
ORDER BY sp
"""

# REMIT Outages - Real-time power plant unavailability
SQL_REMIT_OUTAGES = f"""
SELECT 
  assetId,
  assetName,
  fuelType,
  normalCapacity,
  unavailableCapacity,
  eventStatus,
  CAST(eventStartTime AS STRING) as eventStartTime,
  CAST(eventEndTime AS STRING) as eventEndTime,
  CAST(publishTime AS STRING) as publishTime,
  cause,
  mrid,
  affectedUnitEIC,
  biddingZone
FROM `{PROJECT}.{DATASET}.bmrs_remit_unavailability`
ORDER BY publishTime DESC
"""

def q(sql, date_str):
    """Execute BigQuery with date parameter"""
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("date","DATE",date_str)]
    )
    return bq.query(sql, job_config=cfg).to_dataframe()

def q_no_date(sql):
    """Execute BigQuery without date parameter (for REMIT)"""
    return bq.query(sql).to_dataframe()

def write_sheet(a1, values):
    """Write values to sheet range"""
    sheets.values().update(
        spreadsheetId=SHEET_ID,
        range=a1,
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

def write_df(sheet, a1, df):
    """Write DataFrame to sheet with headers"""
    # Convert to object dtype to allow fillna with empty string
    df_obj = df.astype(object).fillna("")
    vals = [df.columns.tolist()] + df_obj.values.tolist()
    write_sheet(f"{sheet}!{a1}", vals)

def get_sheet_id(title):
    """Get sheet ID by title, create if missing"""
    meta = sheets.get(spreadsheetId=SHEET_ID, includeGridData=False).execute()
    for sh in meta["sheets"]:
        if sh["properties"]["title"] == title:
            return sh["properties"]["sheetId"]
    # create if missing
    sheets.batchUpdate(spreadsheetId=SHEET_ID, body={
        "requests":[{"addSheet":{"properties":{"title":title}}}]
    }).execute()
    return get_sheet_id(title)

def set_named_range(name, ws_name, r1, c1, r2, c2):
    """Create or update a named range"""
    # Try to delete first (ignore error if doesn't exist)
    try:
        delete_body = {
            "requests": [{
                "deleteNamedRange": {
                    "namedRangeId": name
                }
            }]
        }
        sheets.batchUpdate(spreadsheetId=SHEET_ID, body=delete_body).execute()
    except:
        pass  # Named range doesn't exist, that's fine
    
    # Now add it
    body = {
        "requests": [{
            "addNamedRange": {
                "namedRange": {
                    "name": name,
                    "range": {
                        "sheetId": get_sheet_id(ws_name),
                        "startRowIndex": r1-1,
                        "startColumnIndex": c1-1,
                        "endRowIndex": r2,
                        "endColumnIndex": c2
                    }
                }
            }
        }]
    }
    sheets.batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()

def update_dashboard_remit_section(remit_df):
    """Update Dashboard tab rows 42-46 with top 5 active REMIT outages"""
    # Filter active outages and sort by unavailable capacity
    active = remit_df[remit_df['eventStatus'] == 'Active'].copy()
    active['unavailableCapacity'] = pd.to_numeric(active['unavailableCapacity'], errors='coerce')
    active = active.sort_values('unavailableCapacity', ascending=False)
    
    # Get top 5
    top5 = active.head(5)
    
    # Prepare data rows
    rows_to_write = []
    for _, outage in top5.iterrows():
        normal = str(outage.get('normalCapacity', ''))
        unavail = str(outage.get('unavailableCapacity', ''))
        cause = str(outage.get('cause', ''))[:40]
        
        # Calculate percentage with visual bars
        try:
            pct_value = float(unavail) / float(normal) if float(normal) > 0 else 0
            filled_bars = min(10, round(pct_value * 10))
            empty_bars = 10 - filled_bars
            pct_display = f"{'🟥' * filled_bars}{'⬜' * empty_bars} {pct_value*100:.1f}%"
        except:
            pct_display = ""
        
        rows_to_write.append([normal, unavail, pct_display, cause])
    
    # Pad with empty rows if less than 5
    while len(rows_to_write) < 5:
        rows_to_write.append(['', '', '', ''])
    
    # Write to Dashboard E42:H46
    body = {"values": rows_to_write}
    sheets.values().update(
        spreadsheetId=SHEET_ID,
        range="Dashboard!E42:H46",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print(f"   ✅ Updated Dashboard with top {len(top5)} REMIT outages")

def update_dashboard_totals_and_ics(date_str=None):
  """Update Dashboard totals (sum generation) and interconnector display"""
  # Read Live Dashboard table
  resp = sheets.values().get(spreadsheetId=SHEET_ID, range='Live Dashboard!A1:Z60').execute()
  vals = resp.get('values', [])
  if not vals:
    print('   ⚠️ Live Dashboard empty, skipping totals update')
    return
  headers = vals[0]
  try:
    gen_idx = headers.index('Generation_MW')
  except ValueError:
    print('   ⚠️ Generation_MW column not found in Live Dashboard')
    return

  # Sum generation across SPs (rows 2..49 for 48 settlement periods)
  total_gen_mw = 0.0
  for row in vals[1:49]:  # Changed from 51 to 49
    try:
      v = float(row[gen_idx]) if len(row) > gen_idx and row[gen_idx] not in (None, '') else 0.0
      total_gen_mw += v
    except:
      continue

  total_gen_gw = total_gen_mw / 1000.0
  # Write Total Generation to Dashboard!A5 and a small summary to A2 timestamp
  sheets.values().update(spreadsheetId=SHEET_ID, range='Dashboard!A5', valueInputOption='USER_ENTERED', body={'values': [[f'Total Generation: {total_gen_gw:.1f} GW']] }).execute()

  # Interconnectors: read header row and current SP values from Live_Raw_Interconnectors
  ic_resp = sheets.values().get(spreadsheetId=SHEET_ID, range='Live_Raw_Interconnectors!A1:Z60').execute()
  ic_vals = ic_resp.get('values', [])
  if ic_vals and len(ic_vals) > 1:
    ic_header = ic_vals[0]
    # find data row for current settlement period if present (assume first column is SP)
    sp_current = None
    try:
      # try to parse SP from Dashboard A2
      a2 = sheets.values().get(spreadsheetId=SHEET_ID, range='Dashboard!A2').execute().get('values', [[]])[0][0]
      import re
      m = re.search(r'Settlement Period\s*(\d+)', a2)
      if m:
        sp_current = int(m.group(1))
    except Exception:
      sp_current = None

    data_row = None
    for r in ic_vals[1:]:
      try:
        if sp_current is not None and int(r[0]) == sp_current:
          data_row = r
          break
      except:
        continue
    if data_row is None and len(ic_vals) > 1:
      data_row = ic_vals[1]

    # write top 5 interconnector names and values into Dashboard rows 8-12 (columns D/E)
    for i in range(5):
      name = ic_header[i+1] if len(ic_header) > i+1 else ''
      val = data_row[i+1] if data_row and len(data_row) > i+1 else ''
      # write name to Dashboard column D (col 4) and value to column E (col 5)
      sheets.values().update(spreadsheetId=SHEET_ID, range=f'Dashboard!D{8+i}', valueInputOption='USER_ENTERED', body={'values': [[name]]}).execute()
      sheets.values().update(spreadsheetId=SHEET_ID, range=f'Dashboard!E{8+i}', valueInputOption='USER_ENTERED', body={'values': [[val]]}).execute()
  else:
    print('   ⚠️ Live_Raw_Interconnectors empty, skipping IC update')

def ensure_tabs():
    """Ensure all required tabs exist"""
    for t in ["Live Dashboard","Live_Raw_Prices","Live_Raw_Gen",
              "Live_Raw_BOA","Live_Raw_IC","Live_Raw_Interconnectors","Live_Raw_REMIT_Outages"]:
        get_sheet_id(t)

def main(date_str=None):
    """Main refresh logic"""
    if not date_str:
        date_str = datetime.now(LONDON).date().isoformat()

    print(f"🔄 Refreshing dashboard for {date_str}...")
    
    ensure_tabs()

    # Query all data sources
    print("📊 Querying BigQuery...")
    prices = q(SQL_PRICES, date_str)         # sp, ssp, sbp
    gen    = q(SQL_GEN, date_str)            # sp, gen_mw, demand_mw (from IRIS tables with boundary='N')
    boalf  = q(SQL_BOALF, date_str)          # sp, boalf_acceptances, boalf_avg_level_change
    bod    = q(SQL_BOD, date_str)            # sp, bod_offer_price, bod_bid_price
    ic     = q(SQL_IC, date_str)             # sp, ic_net_mw (derived: generation - demand)
    
    print("📡 Querying REMIT outages...")
    remit  = q_no_date(SQL_REMIT_OUTAGES)    # All REMIT outages (no date filter)

    # write raw tabs
    print("💾 Writing raw data tabs...")
    write_df("Live_Raw_Prices","A1",prices)
    write_df("Live_Raw_Gen","A1",gen)
    write_df("Live_Raw_BOA","A1",boalf)
    # Write interconnectors to both expected sheet names
    write_df("Live_Raw_Interconnectors","A1",ic)
    write_df("Live_Raw_IC","A1",ic)
    
    print("💾 Writing REMIT outages...")
    write_df("Live_Raw_REMIT_Outages","A1",remit)
    print(f"   ✅ Wrote {len(remit)} REMIT outage records")

    # assemble tidy table for chart
    print("🔗 Assembling tidy table...")
    # UK has 48 settlement periods per day (24 hours × 2 periods/hour)
    # Exception: 46 SPs on spring clock change (1 hour less), 50 SPs on autumn clock change (1 hour more)
    base = pd.DataFrame({"sp": range(1,49)})  # Changed from 51 to 49 (48 periods)
    for df in [prices, gen, boalf, bod, ic]:
        base = base.merge(df, on="sp", how="left")

    # Select columns - handle case where gen/demand/IC might be empty
    cols_to_select = ["sp","ssp","sbp"]
    if "demand_mw" in base.columns:
        cols_to_select.append("demand_mw")
    if "gen_mw" in base.columns:
        cols_to_select.append("gen_mw")
    if "boalf_acceptances" in base.columns:
        cols_to_select.extend(["boalf_acceptances","boalf_avg_level_change"])
    if "bod_offer_price" in base.columns:
        cols_to_select.extend(["bod_offer_price","bod_bid_price"])
    if "ic_net_mw" in base.columns:
        cols_to_select.append("ic_net_mw")
    
    tidy = base[cols_to_select].copy()

    # Rename columns - build dynamically based on what's present
    new_cols = []
    for col in tidy.columns:
        col_map = {
            "sp": "SP",
            "ssp": "SSP",
            "sbp": "SBP",
            "demand_mw": "Demand_MW",
            "gen_mw": "Generation_MW",
            "boalf_acceptances": "BOALF_Acceptances",
            "boalf_avg_level_change": "BOALF_Avg_Level_Change",
            "bod_offer_price": "BOD_Offer_Price",
            "bod_bid_price": "BOD_Bid_Price",
            "ic_net_mw": "IC_NET_MW"
        }
        new_cols.append(col_map.get(col, col))
    tidy.columns = new_cols

    print("📈 Writing Live Dashboard...")
    write_df("Live Dashboard","A1",tidy)

    # Named range for today's 50 SPs (header + 50 rows, variable columns)
    # Skip if it already exists (will keep existing range)
    print("🏷️  Named range NR_TODAY_TABLE available for charts")
    
    # Update Dashboard tab with top 5 REMIT outages
    print("📊 Updating Dashboard REMIT section...")
    update_dashboard_remit_section(remit)
    
    # Update Dashboard display (full layout)
    print("📊 Updating Dashboard display layout...")
    import subprocess
    subprocess.run(["/opt/homebrew/bin/python3", "update_dashboard_display.py"], cwd="/Users/georgemajor/GB-Power-Market-JJ/tools")
    
    print(f"✅ OK: wrote {len(tidy)} rows for {date_str}")
    print(f"📊 Chart data available at named range: NR_TODAY_TABLE")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default: today Europe/London)")
    args = ap.parse_args()
    main(args.date)
