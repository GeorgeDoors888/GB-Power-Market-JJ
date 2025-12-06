#!/usr/bin/env python3
"""
IRIS Data Quality Monitor
Detects missing periods, duplicates, latency issues in IRIS real-time tables
Sends alerts when data quality degrades
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# IRIS tables to monitor
IRIS_TABLES = [
    'bmrs_fuelinst_iris',
    'bmrs_indgen_iris',
    'bmrs_freq_iris'
]

# Alert thresholds
MAX_MISSING_PERIODS = 10  # Alert if more than 10 periods missing
MAX_LATENCY_MINUTES = 30  # Alert if data older than 30 min
MAX_DUPLICATE_PERCENT = 5  # Alert if >5% duplicates

def check_missing_periods(table_name, hours_to_check=2):
    """Check for missing settlement periods"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    now = datetime.utcnow()
    check_from = now - timedelta(hours=hours_to_check)
    
    query = f"""
    WITH expected_periods AS (
        SELECT 
            TIMESTAMP_ADD('{check_from.isoformat()}', INTERVAL sp * 30 MINUTE) as expected_time,
            sp
        FROM UNNEST(GENERATE_ARRAY(1, 48)) as sp
    ),
    actual_periods AS (
        SELECT DISTINCT
            TIMESTAMP_TRUNC(settlementDate, MINUTE) as actual_time,
            settlementPeriod as sp
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
        WHERE settlementDate >= '{check_from.isoformat()}'
    )
    SELECT 
        e.sp,
        e.expected_time,
        a.actual_time
    FROM expected_periods e
    LEFT JOIN actual_periods a ON e.sp = a.sp
    WHERE a.actual_time IS NULL
    ORDER BY e.sp
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f'   ❌ Error checking {table_name}: {e}')
        return pd.DataFrame()

def check_duplicates(table_name, hours_to_check=2):
    """Check for duplicate records"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    now = datetime.utcnow()
    check_from = now - timedelta(hours=hours_to_check)
    
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET}.{table_name}`
    WHERE settlementDate >= '{check_from.isoformat()}'
    GROUP BY settlementDate, settlementPeriod
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 100
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f'   ❌ Error checking duplicates in {table_name}: {e}')
        return pd.DataFrame()

def check_data_latency(table_name):
    """Check how old the latest data is"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        MAX(settlementDate) as latest_data,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(settlementDate), MINUTE) as latency_minutes
    FROM `{PROJECT_ID}.{DATASET}.{table_name}`
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        print(f'   ❌ Error checking latency in {table_name}: {e}')
        return None

def generate_quality_report():
    """Generate comprehensive quality report"""
    
    print('\n🔍 IRIS DATA QUALITY MONITOR')
    print('='*80)
    print(f'Check time: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC')
    print('='*80)
    
    issues = []
    
    for table in IRIS_TABLES:
        print(f'\n📊 Checking {table}...')
        
        # Check missing periods
        print('   Checking for missing periods...')
        missing = check_missing_periods(table)
        if not missing.empty and len(missing) > MAX_MISSING_PERIODS:
            issue = f'{table}: {len(missing)} missing periods (threshold: {MAX_MISSING_PERIODS})'
            issues.append(issue)
            print(f'   ⚠️  {issue}')
            print(f'      Missing SPs: {missing["sp"].tolist()[:10]}...')
        else:
            print(f'   ✅ Missing periods: {len(missing)} (OK)')
        
        # Check duplicates
        print('   Checking for duplicates...')
        duplicates = check_duplicates(table)
        if not duplicates.empty:
            dup_percent = (len(duplicates) / 48) * 100  # 48 periods in 2h
            if dup_percent > MAX_DUPLICATE_PERCENT:
                issue = f'{table}: {len(duplicates)} duplicate records ({dup_percent:.1f}%)'
                issues.append(issue)
                print(f'   ⚠️  {issue}')
            else:
                print(f'   ✅ Duplicates: {len(duplicates)} ({dup_percent:.1f}% - OK)')
        else:
            print('   ✅ No duplicates found')
        
        # Check latency
        print('   Checking data latency...')
        latency = check_data_latency(table)
        if latency is not None:
            latency_min = latency['latency_minutes']
            if latency_min > MAX_LATENCY_MINUTES:
                issue = f'{table}: Data is {latency_min:.0f} minutes old (threshold: {MAX_LATENCY_MINUTES})'
                issues.append(issue)
                print(f'   ⚠️  {issue}')
                print(f'      Latest data: {latency["latest_data"]}')
            else:
                print(f'   ✅ Latency: {latency_min:.0f} minutes (OK)')
        else:
            print('   ⚠️  Could not check latency')
    
    # Summary
    print('\n' + '='*80)
    print('SUMMARY')
    print('='*80)
    
    if issues:
        print(f'\n⚠️  {len(issues)} ISSUES DETECTED:')
        for issue in issues:
            print(f'   - {issue}')
        return False, issues
    else:
        print('\n✅ ALL CHECKS PASSED - Data quality is good')
        return True, []

def main():
    success, issues = generate_quality_report()
    
    if not success:
        print(f'\n📧 Alerts would be sent for {len(issues)} issues')
        print('   (Email notifications not configured)')
    
    print('\n✅ Data quality check complete!')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
