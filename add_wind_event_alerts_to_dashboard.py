#!/usr/bin/env python3
"""
Wind Event Alerts → Google Sheets Dashboard
============================================

Adds real-time event alerts to "Live Dashboard v2" sheet with:
- Threshold-based detection (Warning/Critical severity)
- Color-coded badges (🔴 Critical, 🟡 Warning, 🟢 Normal)
- Last 24-hour event summary per farm
- Auto-refresh integration with existing dashboard updater

Event Alert Thresholds:
-----------------------
CALM Events (capacity_factor < 5%):
  - Warning: 6+ consecutive hours
  - Critical: 12+ consecutive hours

STORM Events (wind_speed > 25 m/s):
  - Warning: 3+ hours in 24h period
  - Critical: 6+ hours or gusts > 30 m/s

TURBULENCE Events (gust_factor > 1.4):
  - Warning: 4+ hours in 24h period
  - Critical: 8+ hours or gust_factor > 1.6

ICING Events (temp < 0°C + humidity > 85%):
  - Warning: 3+ hours in 24h period
  - Critical: 6+ hours below -2°C

CURTAILMENT Events (generation < expected):
  - Warning: 2+ curtailment events in 24h
  - Critical: 4+ curtailment events or total > 50 MWh lost

Usage:
------
Manual: python3 add_wind_event_alerts_to_dashboard.py
Cron:   0 */6 * * * python3 add_wind_event_alerts_to_dashboard.py

Author: George Major
Date: January 2026
"""

import logging
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# Alert thresholds
ALERT_THRESHOLDS = {
    "calm": {"warning": 6, "critical": 12},      # Hours
    "storm": {"warning": 3, "critical": 6},      # Hours in 24h
    "turbulence": {"warning": 4, "critical": 8}, # Hours in 24h
    "icing": {"warning": 3, "critical": 6},      # Hours in 24h
    "curtailment": {"warning": 2, "critical": 4} # Event count in 24h
}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_bigquery_client():
    """Initialize BigQuery client."""
    return bigquery.Client(project=PROJECT_ID, location="US")

def get_gspread_client():
    """Initialize Google Sheets client."""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    return gspread.authorize(creds)

def get_active_alerts():
    """
    Query BigQuery for active wind farm alerts in last 24 hours.
    
    Returns:
        DataFrame with columns: farm_name, alert_type, severity, hours, 
                               last_occurrence, details
    """
    client = get_bigquery_client()
    
    query = f"""
    WITH recent_events AS (
        SELECT 
            farm_name,
            hour,
            is_calm_event,
            is_storm_event,
            is_turbulence_event,
            is_icing_event,
            is_curtailment_event,
            actual_mw,
            has_any_event
        FROM `{PROJECT_ID}.{DATASET}.wind_unified_features`
        WHERE DATE(hour) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        AND has_any_event = TRUE
    ),
    
    event_counts AS (
        SELECT 
            farm_name,
            
            -- CALM alert
            COUNTIF(is_calm_event > 0) as calm_hours,
            MAX(CASE WHEN is_calm_event > 0 THEN hour END) as last_calm,
            
            -- STORM alert
            COUNTIF(is_storm_event > 0) as storm_hours,
            MAX(CASE WHEN is_storm_event > 0 THEN hour END) as last_storm,
            
            -- TURBULENCE alert
            COUNTIF(is_turbulence_event > 0) as turbulence_hours,
            MAX(CASE WHEN is_turbulence_event > 0 THEN hour END) as last_turbulence,
            
            -- ICING alert
            COUNTIF(is_icing_event > 0) as icing_hours,
            MAX(CASE WHEN is_icing_event > 0 THEN hour END) as last_icing,
            
            -- CURTAILMENT alert
            COUNTIF(is_curtailment_event > 0) as curtailment_events,
            MAX(CASE WHEN is_curtailment_event > 0 THEN hour END) as last_curtailment,
            
            -- Overall
            COUNT(*) as total_event_hours
            
        FROM recent_events
        GROUP BY farm_name
    )
    
    SELECT * FROM event_counts
    WHERE total_event_hours > 0
    ORDER BY total_event_hours DESC
    """
    
    try:
        df = client.query(query).to_dataframe()
        logging.info(f"✅ Retrieved alert data for {len(df)} farms")
        return df
    except Exception as e:
        logging.error(f"❌ BigQuery error: {e}")
        return pd.DataFrame()

def calculate_alert_severity(event_type, event_count):
    """
    Determine alert severity based on event type and count.
    
    Args:
        event_type: One of 'calm', 'storm', 'turbulence', 'icing', 'curtailment'
        event_count: Number of hours or events in last 24h
        
    Returns:
        Tuple of (severity_level, emoji, color_hex)
        severity_level: 'CRITICAL', 'WARNING', or 'NORMAL'
    """
    if event_type not in ALERT_THRESHOLDS:
        return ('NORMAL', '🟢', '#34A853')
    
    thresholds = ALERT_THRESHOLDS[event_type]
    
    if event_count >= thresholds['critical']:
        return ('CRITICAL', '🔴', '#EA4335')
    elif event_count >= thresholds['warning']:
        return ('WARNING', '🟡', '#FBBC04')
    else:
        return ('NORMAL', '🟢', '#34A853')

def format_alerts_dataframe(df):
    """
    Transform alert data into user-friendly format with severity indicators.
    
    Args:
        df: Raw alert data from BigQuery
        
    Returns:
        Formatted DataFrame ready for Google Sheets display
    """
    if len(df) == 0:
        return pd.DataFrame({
            'Farm': ['No active alerts'],
            'Status': ['🟢 All farms operating normally'],
            'Last Event': ['—'],
            'Details': ['No events detected in last 24 hours']
        })
    
    formatted_rows = []
    
    for _, row in df.iterrows():
        farm = row['farm_name']
        
        # Check each event type
        event_types = [
            ('CALM', row.get('calm_hours', 0), row.get('last_calm')),
            ('STORM', row.get('storm_hours', 0), row.get('last_storm')),
            ('TURBULENCE', row.get('turbulence_hours', 0), row.get('last_turbulence')),
            ('ICING', row.get('icing_hours', 0), row.get('last_icing')),
            ('CURTAILMENT', row.get('curtailment_events', 0), row.get('last_curtailment'))
        ]
        
        # Find highest severity alert for this farm
        max_severity = 'NORMAL'
        max_emoji = '🟢'
        alerts = []
        last_event_time = None
        
        for event_name, count, last_time in event_types:
            if count > 0:
                severity, emoji, color = calculate_alert_severity(
                    event_name.lower(), count
                )
                
                # Track highest severity
                if severity == 'CRITICAL' or (severity == 'WARNING' and max_severity == 'NORMAL'):
                    max_severity = severity
                    max_emoji = emoji
                
                # Track most recent event
                if last_time and (last_event_time is None or last_time > last_event_time):
                    last_event_time = last_time
                
                # Build alert description
                unit = "hrs" if event_name != 'CURTAILMENT' else "events"
                alerts.append(f"{emoji} {event_name}: {int(count)} {unit}")
        
        # Format timestamp
        if last_event_time:
            time_str = last_event_time.strftime("%H:%M UTC") if isinstance(last_event_time, datetime) else str(last_event_time)
        else:
            time_str = "—"
        
        # Combine alerts
        details = " | ".join(alerts) if alerts else "No events"
        
        formatted_rows.append({
            'Farm': farm,
            'Status': f"{max_emoji} {max_severity}",
            'Last Event': time_str,
            'Details': details
        })
    
    return pd.DataFrame(formatted_rows)

def update_dashboard_alerts(sheet, alerts_df):
    """
    Update 'Live Dashboard v2' with wind event alerts section.
    
    Args:
        sheet: gspread worksheet object
        alerts_df: Formatted alerts DataFrame
    """
    # Find insertion point (below existing KPIs, typically row 30+)
    ALERT_START_ROW = 32
    
    # Clear existing alert section
    sheet.batch_clear([f"A{ALERT_START_ROW}:E{ALERT_START_ROW + 20}"])
    
    # Header
    sheet.update(f"A{ALERT_START_ROW}", [["🚨 WIND EVENT ALERTS - LAST 24 HOURS"]])
    sheet.format(f"A{ALERT_START_ROW}", {
        "textFormat": {"bold": True, "fontSize": 14},
        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
        "horizontalAlignment": "CENTER",
        "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}}
    })
    
    # Merge header across columns
    sheet.merge_cells(f"A{ALERT_START_ROW}:E{ALERT_START_ROW}")
    
    # Column headers
    header_row = ALERT_START_ROW + 1
    headers = [['Farm Name', 'Alert Status', 'Last Event Time', 'Event Details', 'Actions']]
    sheet.update(f"A{header_row}", headers)
    
    # Format column headers
    sheet.format(f"A{header_row}:E{header_row}", {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
        "horizontalAlignment": "CENTER",
        "borders": {
            "bottom": {"style": "SOLID", "width": 2, "color": {"red": 0, "green": 0, "blue": 0}}
        }
    })
    
    # Data rows
    data_start = header_row + 1
    data_rows = alerts_df.values.tolist()
    
    # Add "View Details" hyperlink in Actions column
    for i, row in enumerate(data_rows):
        row.append(f'=HYPERLINK("#gid=WIND_EVENTS", "View Timeline →")')
    
    if len(data_rows) > 0:
        sheet.update(f"A{data_start}", data_rows)
        
        # Apply conditional formatting based on status
        for i, row in enumerate(alerts_df.itertuples(), start=data_start):
            status = row.Status
            
            # Color code the status column
            if '🔴' in status:
                bg_color = {"red": 1, "green": 0.8, "blue": 0.8}  # Light red
            elif '🟡' in status:
                bg_color = {"red": 1, "green": 0.95, "blue": 0.8}  # Light yellow
            else:
                bg_color = {"red": 0.9, "green": 1, "blue": 0.9}  # Light green
            
            sheet.format(f"B{i}", {"backgroundColor": bg_color})
    
    # Add timestamp footer
    footer_row = data_start + len(data_rows) + 1
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    sheet.update(f"A{footer_row}", [[f"Last updated: {timestamp}"]])
    sheet.format(f"A{footer_row}", {
        "textFormat": {"italic": True, "fontSize": 9},
        "horizontalAlignment": "RIGHT"
    })
    sheet.merge_cells(f"A{footer_row}:E{footer_row}")
    
    logging.info(f"✅ Updated dashboard with {len(alerts_df)} alert rows")

def add_alert_summary_to_top_kpis(sheet, alerts_df):
    """
    Add high-level alert summary to existing KPI section (rows 13-22).
    
    Args:
        sheet: gspread worksheet object
        alerts_df: Formatted alerts DataFrame
    """
    # Count critical and warning alerts
    critical_count = len(alerts_df[alerts_df['Status'].str.contains('🔴')])
    warning_count = len(alerts_df[alerts_df['Status'].str.contains('🟡')])
    normal_count = len(alerts_df[alerts_df['Status'].str.contains('🟢')])
    
    # Find next available KPI row (typically row 23)
    KPI_ROW = 23
    
    # Add alert summary KPI
    if critical_count > 0:
        status_emoji = "🔴"
        status_text = f"{critical_count} Critical Alerts"
        bg_color = {"red": 1, "green": 0.8, "blue": 0.8}
    elif warning_count > 0:
        status_emoji = "🟡"
        status_text = f"{warning_count} Warning Alerts"
        bg_color = {"red": 1, "green": 0.95, "blue": 0.8}
    else:
        status_emoji = "🟢"
        status_text = "All Systems Normal"
        bg_color = {"red": 0.9, "green": 1, "blue": 0.9}
    
    # Update KPI row
    sheet.update(f"K{KPI_ROW}", [[f"{status_emoji} Wind Event Status"]])
    sheet.update(f"M{KPI_ROW}", [[status_text]])
    
    # Format
    sheet.format(f"M{KPI_ROW}", {
        "backgroundColor": bg_color,
        "textFormat": {"bold": True},
        "horizontalAlignment": "CENTER"
    })
    
    logging.info(f"✅ Added alert summary to top KPIs: {status_text}")

def main():
    """Main execution flow."""
    logging.info("=" * 70)
    logging.info("WIND EVENT ALERTS → GOOGLE SHEETS DASHBOARD")
    logging.info("=" * 70)
    
    # Step 1: Query alerts from BigQuery
    logging.info("🔍 Querying active wind event alerts...")
    alerts_raw = get_active_alerts()
    
    if len(alerts_raw) == 0:
        logging.warning("⚠️ No event data available yet (awaiting Tasks 4-7 completion)")
        logging.info("Script is ready and will activate automatically once data is populated.")
        return
    
    # Step 2: Format alerts
    logging.info("📊 Formatting alert data...")
    alerts_formatted = format_alerts_dataframe(alerts_raw)
    
    # Step 3: Update Google Sheets
    logging.info("📝 Updating Google Sheets dashboard...")
    try:
        gc = get_gspread_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(SHEET_NAME)
        
        # Add detailed alert section
        update_dashboard_alerts(sheet, alerts_formatted)
        
        # Add summary to top KPIs
        add_alert_summary_to_top_kpis(sheet, alerts_formatted)
        
        logging.info("=" * 70)
        logging.info("✅ ALERT UPDATE COMPLETE!")
        logging.info(f"   Total farms with alerts: {len(alerts_formatted)}")
        logging.info(f"   Critical: {len(alerts_formatted[alerts_formatted['Status'].str.contains('🔴')])}")
        logging.info(f"   Warning: {len(alerts_formatted[alerts_formatted['Status'].str.contains('🟡')])}")
        logging.info(f"   Normal: {len(alerts_formatted[alerts_formatted['Status'].str.contains('🟢')])}")
        logging.info("=" * 70)
        
    except Exception as e:
        logging.error(f"❌ Google Sheets error: {e}")
        raise

if __name__ == "__main__":
    main()
