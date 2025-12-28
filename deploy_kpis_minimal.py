#!/usr/bin/env python3
"""
Minimal BM KPI Deployment - Smaller batches to avoid timeout
"""
import time
from datetime import date, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SA_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def get_data():
    """Get latest complete BOALF data"""
    print("📊 Querying BigQuery...")
    credentials = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=['https://www.googleapis.com/auth/bigquery']
    )
    client = bigquery.Client(credentials=credentials, project=PROJECT_ID, location='US')

    # Find complete date
    check = """
    SELECT CAST(settlementDate AS DATE) as date,
           COUNT(DISTINCT settlementPeriod) as periods
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE() - 7
      AND validation_flag = 'Valid'
    GROUP BY date
    HAVING COUNT(DISTINCT settlementPeriod) >= 40
    ORDER BY date DESC LIMIT 1
    """
    result = client.query(check).to_dataframe()
    use_date = result.iloc[0]['date']
    print(f"✅ Using data from {use_date} ({result.iloc[0]['periods']} periods)")

    # Get KPI data
    query = f"""
    WITH boalf AS (
      SELECT settlementPeriod as p,
             AVG(acceptancePrice) as avg_accept,
             SUM(acceptanceVolume * acceptancePrice)/NULLIF(SUM(acceptanceVolume),0) as vol_wtd
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{use_date}'
        AND validation_flag = 'Valid'
      GROUP BY p
    )
    SELECT p, COALESCE(avg_accept,0) as avg_accept, COALESCE(vol_wtd,0) as vol_wtd
    FROM UNNEST(GENERATE_ARRAY(1,48)) as p
    LEFT JOIN boalf USING(p)
    ORDER BY p
    """
    df = client.query(query).to_dataframe()
    df.attrs['date'] = use_date
    print(f"✅ Got {len(df)} periods, Avg: £{df['avg_accept'].mean():.2f}/MWh")
    return df

def deploy(df):
    """Deploy to sheets in small batches"""
    print("📝 Connecting to Google Sheets...")
    gc = gspread.service_account(filename=SA_FILE)

    print("📂 Opening spreadsheet...")
    ss = gc.open_by_key(SPREADSHEET_ID)
    sheet = ss.worksheet('Live Dashboard v2')
    print("✅ Connected!")

    data_date = df.attrs['date']
    avg = df['avg_accept'].mean()
    vol = df['vol_wtd'].mean()

    # Update just 4 KPIs for now
    updates = [
        {'range': 'M13', 'values': [['Avg Accept']]},
        {'range': 'M14', 'values': [[f'£{avg:.2f}']]},
        {'range': 'Q13', 'values': [['Vol-Wtd']]},
        {'range': 'Q14', 'values': [[f'£{vol:.2f}']]},
        {'range': 'L13', 'values': [[f'⚡ BM KPIs (Data: {data_date})']]},
    ]

    print("💾 Writing to sheet...")
    sheet.batch_update(updates, value_input_option='USER_ENTERED')
    time.sleep(1)

    # Data_Hidden
    try:
        data_hidden = ss.worksheet('Data_Hidden')
    except:
        data_hidden = ss.add_worksheet('Data_Hidden', 100, 50)

    print("📊 Writing timeseries...")
    row1 = ['avg_accept'] + df['avg_accept'].tolist()
    row2 = ['vol_wtd'] + df['vol_wtd'].tolist()
    data_hidden.update(values=[row1, row2], range_name='A27:AW28')

    # Sparklines
    sparklines = [
        {'range': 'N14', 'values': [['=SPARKLINE(Data_Hidden!$B$27:$AW$27,{"charttype","line";"color","#3498db"})']]},
        {'range': 'R14', 'values': [['=SPARKLINE(Data_Hidden!$B$28:$AW$28,{"charttype","line";"color","#3498db"})']]},
    ]
    sheet.batch_update(sparklines, value_input_option='USER_ENTERED')

    print(f"✅ DONE! M14=£{avg:.2f}, Q14=£{vol:.2f}")

if __name__ == '__main__':
    print("⚡ Minimal BM KPI Deployment\n")
    df = get_data()
    deploy(df)
    print("\n✅ Complete! Check dashboard.")
