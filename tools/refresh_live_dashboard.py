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

SHEET_ID = os.environ["SHEET_ID"]
SA_PATH  = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS  = Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
sheets = build("sheets","v4",credentials=CREDS).spreadsheets()
bq     = bigquery.Client(project=PROJECT)

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

def q(sql, date_str):
    """Execute BigQuery with date parameter"""
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("date","DATE",date_str)]
    )
    return bq.query(sql, job_config=cfg).to_dataframe()

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

def set_named_range(name, sheet, r1, c1, r2, c2):
    """Set/update named range for chart binding"""
    meta = sheets.get(spreadsheetId=SHEET_ID, includeGridData=False).execute()
    # delete if exists
    dels = [{"deleteNamedRange":{"namedRangeId":nr["namedRangeId"]}}
            for nr in meta.get("namedRanges",[]) if nr["name"] == name]
    if dels:
        sheets.batchUpdate(spreadsheetId=SHEET_ID, body={"requests":dels}).execute()
    # add
    req = {"addNamedRange":{"namedRange":{"name":name,"range":{
        "sheetId": get_sheet_id(sheet),
        "startRowIndex": r1-1, "endRowIndex": r2,
        "startColumnIndex": c1-1, "endColumnIndex": c2
    }}}}
    sheets.batchUpdate(spreadsheetId=SHEET_ID, body={"requests":[req]}).execute()

def ensure_tabs():
    """Ensure all required tabs exist"""
    for t in ["Live Dashboard","Live_Raw_Prices","Live_Raw_Gen",
              "Live_Raw_BOA","Live_Raw_Interconnectors"]:
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

    # write raw tabs
    print("💾 Writing raw data tabs...")
    write_df("Live_Raw_Prices","A1",prices)
    write_df("Live_Raw_Gen","A1",gen)
    write_df("Live_Raw_BOA","A1",boalf)
    write_df("Live_Raw_Interconnectors","A1",ic)

    # assemble tidy table for chart
    print("🔗 Assembling tidy table...")
    base = pd.DataFrame({"sp": range(1,51)})
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
    print("🏷️  Setting named range NR_TODAY_TABLE...")
    num_cols = len(tidy.columns)
    set_named_range("NR_TODAY_TABLE","Live Dashboard",1,1,51,num_cols)
    
    print(f"✅ OK: wrote {len(tidy)} rows for {date_str}")
    print(f"📊 Chart data available at named range: NR_TODAY_TABLE")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default: today Europe/London)")
    args = ap.parse_args()
    main(args.date)
