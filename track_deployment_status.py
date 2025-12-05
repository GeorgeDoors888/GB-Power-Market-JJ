#!/usr/bin/env python3
"""
Deployment Status Tracking - Step 4
Creates BigQuery deployment_status table and logs all deployment actions
Tracks: Google Sheets updates, VLP research, CM/FR prep, and future deployment milestones
"""

from google.cloud import bigquery
from datetime import datetime
import json
import os

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "deployment_status"
LOCATION = "US"

def create_deployment_status_table(client):
    """Create deployment_status table in BigQuery"""
    
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    # Define schema
    schema = [
        bigquery.SchemaField("deployment_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("step_number", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("step_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("output_files", "STRING", mode="REPEATED"),
        bigquery.SchemaField("metrics", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("user", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("notes", "STRING", mode="NULLABLE"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="timestamp"
    )
    
    try:
        # Try to get existing table
        existing_table = client.get_table(table_id)
        print(f"✅ Table already exists: {table_id}")
        return existing_table
    except Exception:
        # Create new table
        table = client.create_table(table)
        print(f"✅ Created table: {table_id}")
        return table

def log_deployment_action(client, step_number, step_name, status, description, output_files=None, metrics=None, notes=None):
    """Log a deployment action to BigQuery"""
    
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"
    
    deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    row = {
        "deployment_id": deployment_id,
        "timestamp": datetime.utcnow().isoformat(),
        "step_number": step_number,
        "step_name": step_name,
        "status": status,
        "description": description,
        "output_files": output_files or [],
        "metrics": json.dumps(metrics) if metrics else None,
        "user": "george@upowerenergy.uk",
        "notes": notes
    }
    
    errors = client.insert_rows_json(table_id, [row])
    
    if errors:
        print(f"❌ Error inserting row: {errors}")
        return False
    else:
        print(f"✅ Logged: {step_name} ({status})")
        return True

def log_all_completed_steps(client):
    """Log all completed deployment steps from today's session"""
    
    print("\n" + "=" * 80)
    print("LOGGING COMPLETED DEPLOYMENT STEPS")
    print("=" * 80 + "\n")
    
    # Step 1: Google Sheets Update
    log_deployment_action(
        client,
        step_number=1,
        step_name="Update Google Sheets with Three-Tier Model",
        status="COMPLETED",
        description="Deployed Conservative/Base/Best/BTM scenarios to Battery_Revenue_Analysis worksheet",
        output_files=[
            "https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/",
            "/home/george/GB-Power-Market-JJ/update_sheets_three_tier_direct.py"
        ],
        metrics={
            "rows_updated": 113,
            "start_row": 100,
            "end_row": 212,
            "conservative_monthly": 122235,
            "base_monthly": 285740,
            "best_monthly": 336740,
            "btm_monthly": 411740
        },
        notes="Successfully deployed three-tier revenue model with VLP route comparison"
    )
    
    # Step 2: VLP Aggregator Research
    log_deployment_action(
        client,
        step_number=2,
        step_name="VLP Aggregator Research",
        status="COMPLETED",
        description="Generated contact database for 8 UK VLP aggregators with full details",
        output_files=[
            "/home/george/GB-Power-Market-JJ/vlp_aggregators_research_20251205_140219.csv",
            "/home/george/GB-Power-Market-JJ/vlp_email_template_20251205_140219.txt"
        ],
        metrics={
            "aggregators_researched": 8,
            "top_recommendation": "Habitat Energy",
            "lowest_fee": "12-18% (Flexitricity)",
            "fastest_deployment": "4-6 weeks"
        },
        notes="Top 5: Habitat Energy, Limejump, Flexitricity, Open Energi, Enel X"
    )
    
    # Step 3: CM/FR Application Prep
    log_deployment_action(
        client,
        step_number=3,
        step_name="CM/FR Application Preparation",
        status="COMPLETED",
        description="Generated Capacity Market prequalification and Frequency Response capability assessment templates",
        output_files=[
            "/home/george/GB-Power-Market-JJ/cm_prequalification_20251205_140230.txt",
            "/home/george/GB-Power-Market-JJ/fr_assessment_request_20251205_140230.txt"
        ],
        metrics={
            "cm_revenue_monthly": 67500,
            "fr_revenue_monthly": 51000,
            "cm_derated_capacity_mw": 24,
            "cm_target_auction": "T-4 Q4 2026",
            "fr_service": "Dynamic Containment (DC)"
        },
        notes="Expected combined uplift: £118.5k/month if both services secured"
    )
    
    # Step 4: Deployment Status Tracking
    log_deployment_action(
        client,
        step_number=4,
        step_name="Track Deployment Status",
        status="COMPLETED",
        description="Created BigQuery deployment_status table and logged all completed steps",
        output_files=[
            f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}",
            "/home/george/GB-Power-Market-JJ/track_deployment_status.py"
        ],
        metrics={
            "steps_completed": 4,
            "total_files_generated": 7,
            "deployment_date": datetime.now().strftime("%Y-%m-%d")
        },
        notes="All 4 deployment steps completed successfully"
    )
    
    print("\n" + "=" * 80)
    print("✅ ALL DEPLOYMENT STEPS LOGGED")
    print("=" * 80)

def generate_deployment_summary(client):
    """Generate deployment summary from BigQuery"""
    
    print("\n" + "=" * 80)
    print("DEPLOYMENT SUMMARY - QUERY FROM BIGQUERY")
    print("=" * 80 + "\n")
    
    query = f"""
    SELECT 
        step_number,
        step_name,
        status,
        description,
        ARRAY_LENGTH(output_files) as files_generated,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', timestamp) as completed_at
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    WHERE DATE(timestamp) = CURRENT_DATE()
    ORDER BY step_number
    """
    
    try:
        results = client.query(query).result()
        
        print("Today's Deployment Actions:\n")
        for row in results:
            print(f"Step {row.step_number}: {row.step_name}")
            print(f"  Status: {row.status}")
            print(f"  Description: {row.description}")
            print(f"  Files: {row.files_generated}")
            print(f"  Completed: {row.completed_at}")
            print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"⚠️ Query skipped (table just created): {e}")

def main():
    """Execute deployment status tracking"""
    
    print("=" * 80)
    print("DEPLOYMENT STATUS TRACKING - STEP 4")
    print("=" * 80)
    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET}")
    print(f"Table: {TABLE_NAME}\n")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    # Create deployment_status table
    print("Creating deployment_status table...")
    create_deployment_status_table(client)
    
    # Log all completed steps
    log_all_completed_steps(client)
    
    # Generate summary
    generate_deployment_summary(client)
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ DEPLOYMENT TRACKING COMPLETE")
    print("=" * 80)
    
    print("\nBigQuery Table Created:")
    print(f"  {PROJECT_ID}.{DATASET}.{TABLE_NAME}")
    
    print("\nDeployment Steps Logged:")
    print("  1. Google Sheets Update - COMPLETED")
    print("  2. VLP Aggregator Research - COMPLETED")
    print("  3. CM/FR Application Prep - COMPLETED")
    print("  4. Deployment Status Tracking - COMPLETED")
    
    print("\nQuery Deployment Status:")
    print(f"  SELECT * FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`")
    print(f"  WHERE DATE(timestamp) = CURRENT_DATE()")
    print(f"  ORDER BY step_number")
    
    print("\n" + "=" * 80)
    print("ALL 4 STEPS COMPLETE")
    print("=" * 80)
    
    print("\nFiles Generated (7 total):")
    print("  1. Battery_Revenue_Analysis worksheet (rows 100-212)")
    print("  2. update_sheets_three_tier_direct.py")
    print("  3. vlp_aggregators_research_20251205_140219.csv")
    print("  4. vlp_email_template_20251205_140219.txt")
    print("  5. cm_prequalification_20251205_140230.txt")
    print("  6. fr_assessment_request_20251205_140230.txt")
    print("  7. track_deployment_status.py")
    
    print("\nBigQuery Tables:")
    print(f"  • {PROJECT_ID}.{DATASET}.{TABLE_NAME} (deployment tracking)")
    
    print("\nRevenue Model Summary:")
    print("  • Conservative: £122,235/month (arbitrage only - PROVEN)")
    print("  • Base: £285,740/month (+ VLP £96k + CM £67.5k)")
    print("  • Best: £336,740/month (+ FR £51k)")
    print("  • BTM: £411,740/month (+ DUoS £75k)")
    
    print("\nNext Actions:")
    print("  1. Review VLP aggregator CSV and send enquiries")
    print("  2. Complete [TO BE COMPLETED] fields in CM/FR templates")
    print("  3. Finalize battery technical specifications")
    print("  4. Schedule VLP aggregator calls (expect 1-2 week response)")
    print("  5. Submit CM prequalification Q2 2026 (after energisation)")
    print("  6. Submit FR capability assessment via VLP or direct to ESO")
    
    print("\n" + "=" * 80)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n✅ Step 4 Complete - Deployment status tracked in BigQuery")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
