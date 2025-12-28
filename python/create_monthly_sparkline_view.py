#!/usr/bin/env python3
"""
Create Monthly Sparkline View and Test Output

Creates vlp_revenue_monthly_sparklines view with 12-month aggregates:
- Max, Min, Avg per month for each KPI
- GB total + by DNO breakdowns
- Combines historical + IRIS data for complete coverage
"""

from google.cloud import bigquery
import pandas as pd
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def main():
    print("⚡ Creating Monthly Sparkline View for VLP Revenue")
    print(f"📍 Project: {PROJECT_ID}")
    print(f"📍 Dataset: {DATASET}\n")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID, location="US")
        print("✅ Connected to BigQuery\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return 1
    
    # Read and execute SQL
    sql_file = '/Users/georgemajor/GB-Power-Market-JJ/sql/create_vlp_revenue_monthly_sparklines.sql'
    
    print(f"📄 Reading: {sql_file}")
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    # Remove comments
    lines = [line for line in sql.split('\n') if not line.strip().startswith('--')]
    sql_clean = '\n'.join(lines)
    
    # Stop at usage examples
    if '-- ====' in sql_clean:
        sql_clean = sql_clean.split('-- ====')[0]
    
    print(f"⏳ Creating view...\n")
    
    try:
        job = client.query(sql_clean)
        result = job.result()
        print("✅ View created successfully!\n")
    except Exception as e:
        print(f"❌ Error creating view: {e}")
        return 1
    
    # Test queries
    print("="*80)
    print("📊 Testing View - GB Total Last 12 Months")
    print("="*80)
    
    query_gb = """
    SELECT 
      month_label,
      total_net_revenue_monthly,
      avg_margin,
      max_margin,
      min_margin,
      total_volume_monthly,
      active_units,
      total_acceptances
    FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_monthly_sparklines`
    WHERE breakdown = 'GB_total'
    ORDER BY month_start DESC
    LIMIT 12
    """
    
    try:
        df_gb = client.query(query_gb).to_dataframe()
        
        if len(df_gb) == 0:
            print("⚠️  No data returned - check date ranges")
            return 1
        
        print(f"\n📅 Monthly Revenue Trend (Last {len(df_gb)} months):\n")
        print(df_gb.to_string(index=False))
        
        # Generate sparkline arrays
        print("\n" + "="*80)
        print("✨ Sparkline Data Arrays (for Google Sheets)")
        print("="*80)
        
        # Reverse order for sparklines (oldest to newest, left to right)
        df_sparkline = df_gb.iloc[::-1]
        
        print("\n📈 Net Revenue (£M) - Last 12 months:")
        revenue_array = [f"{v/1e6:.1f}" for v in df_sparkline['total_net_revenue_monthly'].values]
        print(f"   {', '.join(revenue_array)}")
        print(f"   =SPARKLINE({{{', '.join(revenue_array)}}})")
        
        print("\n📈 Net Margin (£/MWh) - Last 12 months:")
        margin_avg = [f"{v:.1f}" for v in df_sparkline['avg_margin'].values if pd.notna(v)]
        margin_max = [f"{v:.1f}" for v in df_sparkline['max_margin'].values if pd.notna(v)]
        margin_min = [f"{v:.1f}" for v in df_sparkline['min_margin'].values if pd.notna(v)]
        
        print(f"   Avg: {', '.join(margin_avg)}")
        print(f"   Max: {', '.join(margin_max)}")
        print(f"   Min: {', '.join(margin_min)}")
        print(f"   =SPARKLINE({{{', '.join(margin_avg)}}})")
        
        print("\n📈 Volume (MWh) - Last 12 months:")
        volume_array = [f"{v:,.0f}" for v in df_sparkline['total_volume_monthly'].values]
        print(f"   {', '.join(volume_array)}")
        
        print("\n📈 Active Units - Last 12 months:")
        units_array = [f"{int(v)}" for v in df_sparkline['active_units'].values]
        print(f"   {', '.join(units_array)}")
        print(f"   =SPARKLINE({{{', '.join(units_array)}}})")
        
        # Summary statistics
        print("\n" + "="*80)
        print("📊 12-Month Summary Statistics")
        print("="*80)
        
        print(f"\n💰 Revenue:")
        print(f"   Total: £{df_gb['total_net_revenue_monthly'].sum()/1e6:.1f}M")
        print(f"   Monthly Avg: £{df_gb['total_net_revenue_monthly'].mean()/1e6:.1f}M")
        print(f"   Best Month: £{df_gb['total_net_revenue_monthly'].max()/1e6:.1f}M ({df_gb.loc[df_gb['total_net_revenue_monthly'].idxmax(), 'month_label']})")
        print(f"   Worst Month: £{df_gb['total_net_revenue_monthly'].min()/1e6:.1f}M ({df_gb.loc[df_gb['total_net_revenue_monthly'].idxmin(), 'month_label']})")
        
        print(f"\n📊 Net Margin:")
        print(f"   Average: £{df_gb['avg_margin'].mean():.2f}/MWh")
        print(f"   Peak: £{df_gb['max_margin'].max():.2f}/MWh ({df_gb.loc[df_gb['max_margin'].idxmax(), 'month_label']})")
        print(f"   Lowest: £{df_gb['min_margin'].min():.2f}/MWh ({df_gb.loc[df_gb['min_margin'].idxmin(), 'month_label']})")
        
        print(f"\n⚡ Activity:")
        print(f"   Total Acceptances: {df_gb['total_acceptances'].sum():,}")
        print(f"   Avg Units/Month: {df_gb['active_units'].mean():.0f}")
        print(f"   Peak Activity: {df_gb['total_acceptances'].max():,} acceptances ({df_gb.loc[df_gb['total_acceptances'].idxmax(), 'month_label']})")
        
    except Exception as e:
        print(f"❌ Error querying view: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test DNO breakdown
    print("\n" + "="*80)
    print("📊 Testing DNO Breakdown (Sample)")
    print("="*80)
    
    query_dno = """
    SELECT 
      dno,
      COUNT(DISTINCT month_start) as months_available,
      SUM(total_net_revenue_monthly) as total_revenue_12m,
      AVG(avg_margin) as avg_margin_12m
    FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_monthly_sparklines`
    WHERE breakdown = 'by_dno'
    GROUP BY dno
    ORDER BY total_revenue_12m DESC
    LIMIT 10
    """
    
    try:
        df_dno = client.query(query_dno).to_dataframe()
        print(f"\nTop 10 DNOs by 12-month revenue:\n")
        print(df_dno.to_string(index=False))
    except Exception as e:
        print(f"⚠️  DNO breakdown query failed: {e}")
    
    print("\n" + "="*80)
    print("✅ Monthly Sparkline View Complete!")
    print("="*80)
    print(f"\n📍 View: {PROJECT_ID}.{DATASET}.vlp_revenue_monthly_sparklines")
    print("\n🎯 Next Steps:")
    print("   1. Add sparklines to Dashboard V3")
    print("   2. Create 'Monthly Trends' sheet with full breakdown")
    print("   3. Add year-over-year comparison")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
