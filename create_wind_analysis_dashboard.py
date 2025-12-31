#!/usr/bin/env python3
"""
Wind Analysis Dashboard with Weather Change Alerts
Creates comprehensive visual dashboard starting at A25 with:
- Traffic light weather change alerts (🔴🟡🟢)
- KPI cards with sparklines
- Time-series graphs
- Weather station correlation matrix
- Ramp analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"

# Alert thresholds
ALERT_THRESHOLDS = {
    'CRITICAL': {
        'wind_change_pct': 25,  # >25% change in wind speed
        'direction_shift_deg': 60,  # >60° direction change
        'lead_time_hours': 1,  # <1 hour warning
        'color': '#FF4444',
        'emoji': '🔴'
    },
    'WARNING': {
        'wind_change_pct': 10,  # 10-25% change
        'direction_shift_deg': 30,  # 30-60° change
        'lead_time_hours': 2,  # 1-2 hours warning
        'color': '#FFB84D',
        'emoji': '🟡'
    },
    'STABLE': {
        'wind_change_pct': 10,  # <10% change
        'direction_shift_deg': 30,  # <30° change
        'lead_time_hours': float('inf'),
        'color': '#4CAF50',
        'emoji': '🟢'
    }
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_weather_change_alerts(bq_client):
    """
    Analyze GFS forecast data to detect significant weather changes
    Returns alert level (CRITICAL/WARNING/STABLE) with timeframe
    """
    try:
        query = f"""
        WITH current_conditions AS (
            SELECT 
                farm_name,
                wind_speed_100m as current_wind,
                wind_direction_100m as current_direction,
                forecast_time
            FROM `{PROJECT_ID}.{DATASET}.gfs_forecast_weather`
            WHERE CAST(forecast_horizon_hours AS INT64) = 0  -- Current conditions
            AND forecast_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
            QUALIFY ROW_NUMBER() OVER (PARTITION BY farm_name ORDER BY forecast_time DESC) = 1
        ),
        forecast_conditions AS (
            SELECT 
                farm_name,
                CAST(forecast_horizon_hours AS INT64) as forecast_horizon_hours,
                wind_speed_100m as forecast_wind,
                wind_direction_100m as forecast_direction,
                temperature_2m,
                precipitation
            FROM `{PROJECT_ID}.{DATASET}.gfs_forecast_weather`
            WHERE CAST(forecast_horizon_hours AS INT64) BETWEEN 1 AND 6  -- Next 6 hours
            AND forecast_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
            QUALIFY ROW_NUMBER() OVER (PARTITION BY farm_name, CAST(forecast_horizon_hours AS INT64) ORDER BY forecast_time DESC) = 1
        )
        SELECT 
            f.farm_name,
            f.forecast_horizon_hours,
            c.current_wind,
            f.forecast_wind,
            ABS(f.forecast_wind - c.current_wind) / c.current_wind * 100 as wind_change_pct,
            c.current_direction,
            f.forecast_direction,
            ABS(f.forecast_direction - c.current_direction) as direction_shift_deg,
            f.temperature_2m,
            f.precipitation
        FROM forecast_conditions f
        JOIN current_conditions c ON f.farm_name = c.farm_name
        WHERE c.current_wind > 3  -- Only when wind is significant
        ORDER BY wind_change_pct DESC, forecast_horizon_hours ASC
        """
        
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            return {
                'status': 'STABLE',
                'emoji': '🟢',
                'message': 'No significant weather changes detected',
                'timeframe': 'N/A',
                'affected_farms': [],
                'details': {}
            }
        
        # Determine alert level
        max_wind_change = df['wind_change_pct'].max()
        max_direction_shift = df['direction_shift_deg'].max()
        min_lead_time = df.loc[df['wind_change_pct'] > 10, 'forecast_horizon_hours'].min()
        
        if max_wind_change >= ALERT_THRESHOLDS['CRITICAL']['wind_change_pct'] or \
           max_direction_shift >= ALERT_THRESHOLDS['CRITICAL']['direction_shift_deg']:
            alert_level = 'CRITICAL'
        elif max_wind_change >= ALERT_THRESHOLDS['WARNING']['wind_change_pct'] or \
             max_direction_shift >= ALERT_THRESHOLDS['WARNING']['direction_shift_deg']:
            alert_level = 'WARNING'
        else:
            alert_level = 'STABLE'
        
        # Get affected farms
        threshold = ALERT_THRESHOLDS[alert_level]['wind_change_pct']
        affected = df[df['wind_change_pct'] >= threshold]['farm_name'].unique()[:5]  # Top 5
        
        return {
            'status': alert_level,
            'emoji': ALERT_THRESHOLDS[alert_level]['emoji'],
            'message': f"{max_wind_change:.0f}% wind change, {max_direction_shift:.0f}° shift",
            'timeframe': f"{int(min_lead_time)}h" if pd.notna(min_lead_time) else '6h+',
            'affected_farms': list(affected),
            'details': df.head(20).to_dict('records')
        }
        
    except Exception as e:
        logging.error(f"Weather alert query failed: {e}")
        return {
            'status': 'STABLE',
            'emoji': '🟢',
            'message': 'Alert system unavailable',
            'timeframe': 'N/A',
            'affected_farms': [],
            'details': {}
        }


def get_enhanced_wind_metrics(bq_client):
    """
    Get comprehensive wind forecast metrics with additional analysis
    """
    try:
        # Get last 7 days daily metrics
        daily_query = f"""
        SELECT
            settlement_date,
            num_periods,
            avg_actual_mw,
            avg_forecast_mw,
            bias_mw,
            wape_percent,
            rmse_mw,
            num_large_ramp_misses
        FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_daily`
        WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        ORDER BY settlement_date DESC
        """
        daily_df = bq_client.query(daily_query).to_dataframe()
        
        # Get hourly data for ramp analysis (last 48 hours)
        hourly_query = f"""
        SELECT
            settlement_date,
            settlement_period,
            actual_mw_total,
            forecast_mw,
            error_mw,
            abs_error_mw,
            ramp_miss_mw
        FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_sp`
        WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        ORDER BY settlement_date DESC, settlement_period DESC
        """
        hourly_df = bq_client.query(hourly_query).to_dataframe()
        
        # Calculate additional metrics
        if not daily_df.empty:
            latest = daily_df.iloc[0]
            
            # Calculate trend (improving/degrading)
            if len(daily_df) >= 2:
                wape_trend = daily_df.iloc[0]['wape_percent'] - daily_df.iloc[1]['wape_percent']
                trend_emoji = '📉' if wape_trend < 0 else '📈'
            else:
                wape_trend = 0
                trend_emoji = '➡️'
            
            kpis = {
                'wape_percent': latest['wape_percent'],
                'wape_trend': wape_trend,
                'trend_emoji': trend_emoji,
                'bias_mw': latest['bias_mw'],
                'avg_actual_mw': latest['avg_actual_mw'],
                'avg_forecast_mw': latest['avg_forecast_mw'],
                'deviation_pct': abs(latest['bias_mw']) / latest['avg_actual_mw'] * 100 if latest['avg_actual_mw'] > 0 else 0,
                'num_large_ramp_misses': int(latest['num_large_ramp_misses']),
                'date': latest['settlement_date'].strftime('%Y-%m-%d')
            }
        else:
            kpis = {
                'wape_percent': 0,
                'wape_trend': 0,
                'trend_emoji': '➡️',
                'bias_mw': 0,
                'avg_actual_mw': 0,
                'avg_forecast_mw': 0,
                'deviation_pct': 0,
                'num_large_ramp_misses': 0,
                'date': 'N/A'
            }
        
        return {
            'daily_metrics': daily_df,
            'hourly_metrics': hourly_df,
            'kpis': kpis
        }
        
    except Exception as e:
        logging.error(f"Wind metrics query failed: {e}")
        return {
            'daily_metrics': pd.DataFrame(),
            'hourly_metrics': pd.DataFrame(),
            'kpis': {}
        }


def generate_sparkline_formula(data, chart_type='column', color='#2196F3'):
    """Generate Google Sheets SPARKLINE formula"""
    if not data or len(data) == 0:
        return ''
    
    clean_data = [float(x) if pd.notna(x) else 0 for x in data]
    data_str = ','.join(map(str, clean_data))
    
    return f'=SPARKLINE({{{data_str}}},{{"charttype","{chart_type}";"color","{color}"}})'


def create_dashboard_layout(sheets_service, wind_data, alert_data):
    """
    Create comprehensive wind dashboard layout starting at A25
    """
    try:
        batch_data = []
        
        # ==================================================
        # SECTION 1: HEADER & WEATHER ALERT (A25:N26)
        # ==================================================
        
        # Row 25: Section header
        batch_data.append({
            'range': f'{SHEET_NAME}!A25:G25',
            'values': [['💨 WIND FORECAST & WEATHER ALERTS', '', '', '', '', '', '']]
        })
        
        # Row 26: Traffic light alert
        alert_status = f"{alert_data['emoji']} {alert_data['status']}"
        alert_message = alert_data['message']
        alert_timeframe = f"⏰ {alert_data['timeframe']}"
        affected = ', '.join(alert_data['affected_farms'][:3]) if alert_data['affected_farms'] else 'None'
        
        batch_data.append({
            'range': f'{SHEET_NAME}!A26:G26',
            'values': [[alert_status, alert_message, alert_timeframe, f"Affected: {affected}", '', '', '']]
        })
        
        # ==================================================
        # SECTION 2: KPI CARDS (A27:N30)
        # ==================================================
        
        kpis = wind_data['kpis']
        daily_metrics = wind_data['daily_metrics']
        
        # Row 27: Forecast Error (WAPE) - Split into separate cells
        wape_value = f"{kpis.get('wape_percent', 0):.1f}%"
        wape_trend = f"{kpis.get('trend_emoji', '➡️')} {abs(kpis.get('wape_trend', 0)):.1f}%"
        
        batch_data.append({
            'range': f'{SHEET_NAME}!A27:C27',
            'values': [['📊 Forecast Error', wape_value, wape_trend]]
        })
        
        # WAPE sparkline in separate cell D27
        if not daily_metrics.empty and len(daily_metrics) > 0:
            wape_data = daily_metrics.iloc[::-1]['wape_percent'].tolist()
            wape_sparkline = generate_sparkline_formula(wape_data, 'line', '#FF6B6B')
            batch_data.append({
                'range': f'{SHEET_NAME}!D27',
                'values': [[wape_sparkline]]
            })
        
        # Row 28: Forecast Bias - Split into separate cells
        bias_value = f"{abs(kpis.get('bias_mw', 0)):.0f} MW"
        bias_status = 'UNDER-FORECASTING' if kpis.get('bias_mw', 0) < 0 else 'OVER-FORECASTING'
        
        batch_data.append({
            'range': f'{SHEET_NAME}!A28:C28',
            'values': [['📉 Forecast Bias', bias_value, bias_status]]
        })
        
        # Bias sparkline in separate cell D28
        if not daily_metrics.empty and len(daily_metrics) > 0:
            bias_data = daily_metrics.iloc[::-1]['bias_mw'].tolist()
            bias_sparkline = generate_sparkline_formula(bias_data, 'column', '#9C27B0')
            batch_data.append({
                'range': f'{SHEET_NAME}!D28',
                'values': [[bias_sparkline]]
            })
        
        # Row 29: Actual vs Forecast Deviation - Split into separate cells
        actual_value = f"{kpis.get('avg_actual_mw', 0):.0f} MW actual"
        deviation_value = f"{kpis.get('deviation_pct', 0):.1f}% dev"
        
        batch_data.append({
            'range': f'{SHEET_NAME}!A29:C29',
            'values': [['⚡ Actual vs Forecast', actual_value, deviation_value]]
        })
        
        # Actual MW sparkline in separate cell D29
        if not daily_metrics.empty and len(daily_metrics) > 0:
            actual_data = daily_metrics.iloc[::-1]['avg_actual_mw'].tolist()
            actual_sparkline = generate_sparkline_formula(actual_data, 'column', '#2196F3')
            batch_data.append({
                'range': f'{SHEET_NAME}!D29',
                'values': [[actual_sparkline]]
            })
        
        # Row 30: Ramp Misses
        ramp_count = kpis.get('num_large_ramp_misses', 0)
        ramp_status = '🔴 High' if ramp_count > 10 else ('🟡 Medium' if ramp_count > 5 else '🟢 Low')
        
        batch_data.append({
            'range': f'{SHEET_NAME}!A30:C30',
            'values': [['⚠️ Large Ramp Misses', f"{ramp_count} events", f"{ramp_status} (>500MW/30min)"]]
        })
        
        # ==================================================
        # SECTION 3: TIME-SERIES VISUALIZATION (A31:N42)
        # ==================================================
        
        # Row 31: Chart header - Actual vs Forecast (Last 48h)
        batch_data.append({
            'range': f'{SHEET_NAME}!A31:G31',
            'values': [['📈 ACTUAL VS FORECAST (Last 48 Hours)', '', '', '', '', '', '']]
        })
        
        # Rows 32-36: Time series data (will use Apps Script for charts)
        hourly_df = wind_data['hourly_metrics']
        if not hourly_df.empty:
            # Last 48 settlement periods (24 hours)
            recent = hourly_df.head(48).iloc[::-1]  # Chronological order
            
            time_labels = [f"SP{int(sp)}" for sp in recent['settlement_period'].tolist()]
            actual_values = recent['actual_mw_total'].tolist()
            forecast_values = recent['forecast_mw'].tolist()
            
            # Create data table for chart
            chart_data_rows = []
            chart_data_rows.append(['Period', 'Actual MW', 'Forecast MW', '', '', '', ''])
            
            for i in range(min(10, len(time_labels))):  # First 10 periods as sample
                chart_data_rows.append([
                    time_labels[i],
                    actual_values[i],
                    forecast_values[i],
                    '', '', '', ''
                ])
            
            batch_data.append({
                'range': f'{SHEET_NAME}!A32:G42',
                'values': chart_data_rows
            })
        else:
            placeholder = [['No hourly data available', '', '', '', '', '', '']]
            batch_data.append({
                'range': f'{SHEET_NAME}!A32:G42',
                'values': placeholder
            })
        
        # ==================================================
        # SECTION 4: WEATHER STATION CORRELATION (A43:N52)
        # ==================================================
        
        station_header = [[
            '🌍 WEATHER STATION ANALYSIS',
            '', '', '', '', '', ''
        ]]
        batch_data.append({
            'range': f'{SHEET_NAME}!A43:G43',
            'values': station_header
        })
        
        # Weather station data from alert_data['details']
        if alert_data['details']:
            station_rows = [['Farm', 'Current Wind', 'Forecast Wind', 'Change %', 'Direction Δ', 'Lead Time', '']]
            
            for detail in alert_data['details'][:8]:  # Top 8 stations
                station_rows.append([
                    detail.get('farm_name', 'N/A')[:20],
                    f"{detail.get('current_wind', 0):.1f} m/s",
                    f"{detail.get('forecast_wind', 0):.1f} m/s",
                    f"{detail.get('wind_change_pct', 0):.0f}%",
                    f"{detail.get('direction_shift_deg', 0):.0f}°",
                    f"{int(detail.get('forecast_horizon_hours', 0))}h",
                    ''
                ])
            
            batch_data.append({
                'range': f'{SHEET_NAME}!A44:G52',
                'values': station_rows
            })
        else:
            placeholder = [['No weather station data available', '', '', '', '', '', '']]
            batch_data.append({
                'range': f'{SHEET_NAME}!A44:G52',
                'values': placeholder
            })
        
        # ==================================================
        # EXECUTE BATCH UPDATE
        # ==================================================
        
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': batch_data
        }
        
        result = sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        
        logging.info(f"✅ Dashboard updated: {result.get('totalUpdatedCells')} cells")
        
        # Apply formatting
        apply_dashboard_formatting(sheets_service, alert_data['status'])
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Dashboard creation failed: {e}")
        return False


def apply_dashboard_formatting(sheets_service, alert_status):
    """
    Apply colors, borders, and formatting to dashboard
    """
    try:
        # Get sheet ID
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_id = None
        for sheet in sheet_metadata['sheets']:
            if sheet['properties']['title'] == SHEET_NAME:
                sheet_id = sheet['properties']['sheetId']
                break
        
        if not sheet_id:
            logging.error(f"Sheet '{SHEET_NAME}' not found")
            return
        
        # Alert color based on status
        alert_color = ALERT_THRESHOLDS.get(alert_status, ALERT_THRESHOLDS['STABLE'])['color']
        alert_rgb = hex_to_rgb(alert_color)
        
        requests = []
        
        # Format section header (Row 25)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 24,  # Row 25 (0-indexed)
                    'endRowIndex': 25,
                    'startColumnIndex': 0,
                    'endColumnIndex': 7  # Columns A-G
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                        'textFormat': {'bold': True, 'fontSize': 12, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                        'horizontalAlignment': 'LEFT',
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
            }
        })
        
        # Format alert row (Row 26)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 25,  # Row 26
                    'endRowIndex': 26,
                    'startColumnIndex': 0,
                    'endColumnIndex': 7  # Columns A-G
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': alert_rgb,
                        'textFormat': {'bold': True, 'fontSize': 11},
                        'horizontalAlignment': 'LEFT',
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
            }
        })
        
        # Format KPI cards (Rows 27-30)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 26,  # Row 27
                    'endRowIndex': 30,    # Row 30
                    'startColumnIndex': 0,
                    'endColumnIndex': 7   # Columns A-G
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.96, 'green': 0.96, 'blue': 0.96},
                        'textFormat': {'fontSize': 10},
                        'borders': {
                            'top': {'style': 'SOLID', 'width': 1},
                            'bottom': {'style': 'SOLID', 'width': 1},
                            'left': {'style': 'SOLID', 'width': 1},
                            'right': {'style': 'SOLID', 'width': 1}
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,borders)'
            }
        })
        
        # Execute formatting
        body = {'requests': requests}
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        
        logging.info("✅ Dashboard formatting applied")
        
    except Exception as e:
        logging.error(f"❌ Formatting failed: {e}")


def hex_to_rgb(hex_color):
    """Convert hex color to RGB dict for Google Sheets API"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return {'red': r/255, 'green': g/255, 'blue': b/255}


def main():
    """Main execution"""
    print("=" * 70)
    print("💨 WIND ANALYSIS DASHBOARD CREATOR")
    print("=" * 70)
    
    # Initialize clients
    logging.info("🔧 Connecting to BigQuery and Sheets...")
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')
    
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    
    # Get data
    logging.info("📊 Fetching weather alerts...")
    alert_data = get_weather_change_alerts(bq_client)
    logging.info(f"  {alert_data['emoji']} Status: {alert_data['status']} - {alert_data['message']}")
    
    logging.info("📊 Fetching wind forecast metrics...")
    wind_data = get_enhanced_wind_metrics(bq_client)
    logging.info(f"  WAPE: {wind_data['kpis'].get('wape_percent', 0):.1f}%")
    
    # Create dashboard
    logging.info("🎨 Creating dashboard layout...")
    success = create_dashboard_layout(sheets_service, wind_data, alert_data)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ DASHBOARD CREATED SUCCESSFULLY")
        print("=" * 70)
        print(f"View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    else:
        print("\n❌ Dashboard creation failed")


if __name__ == "__main__":
    main()
