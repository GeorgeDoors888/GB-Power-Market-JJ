#!/usr/bin/env python3
"""Fix EBOCF query to use totalCashflow column"""

import sys
import os

file_path = "parallel_bm_kpi_pipeline.py"

if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} not found")
    sys.exit(1)

with open(file_path, 'r') as f:
    content = f.read()

# Old query pattern (broken)
old_query = """SELECT
                settlementDate as date,
                settlementPeriod,
                bmUnit,
                _direction,
                SUM(totalCashflow) as net_cashflow
            FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
            WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY settlementDate, settlementPeriod, bmUnit, _direction"""

# New query pattern (fixed)
new_query = """SELECT
                settlementDate as date,
                bmUnit,
                SUM(CASE WHEN _direction = 'offer' THEN totalCashflow ELSE 0 END) as offer_cashflow,
                SUM(CASE WHEN _direction = 'bid' THEN totalCashflow ELSE 0 END) as bid_cashflow,
                SUM(totalCashflow) as net_cashflow
            FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
            WHERE settlementDate BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY settlementDate, bmUnit"""

if old_query in content:
    with open(file_path + '.backup_before_ebocf_fix', 'w') as f:
        f.write(content)
    
    content = content.replace(old_query, new_query)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ EBOCF query fixed!")
    print("   Backup saved: parallel_bm_kpi_pipeline.py.backup_before_ebocf_fix")
else:
    if "SUM(CASE WHEN _direction = 'offer' THEN totalCashflow" in content:
        print("✅ EBOCF query is already fixed!")
    else:
        print("⚠️  Query pattern not found - manual check needed")
