#!/usr/bin/env python3
"""
Enhanced Wind Analysis Dashboard with Comprehensive Analytics
Extends existing dashboard with:
- Per-farm forecast error tracking (identify worst performers)
- Imbalance price correlation and revenue impact
- Hour-of-day accuracy heatmap
- Weather pattern analysis
- Enhanced visualizations

Dashboard Layout:
- A25-26: Weather Alerts (enhanced with pressure/trends)
- A27-30: System-wide KPIs (WAPE, Bias, Deviation, Ramps)
- A31-42: Time-Series (48h actual vs forecast)
- A43-52: Weather Stations (farm-by-farm wind changes)
- A53-62: Per-Farm Error Analysis (NEW)
- A63-72: Imbalance Price Impact (NEW)
- A73-82: Hour-of-Day Accuracy Heatmap (NEW)
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_per_farm_forecast_errors(bq_client):
    """
    Calculate forecast error metrics per wind farm
    Identifies which farms NESO forecasts worst
    """
    try:
        query = f"""
        WITH farm_generation AS (
            SELECT
                DATE(pn.settlementDate) as settlement_date,
                pn.settlementPeriod,
                wfm.farm_name,
                wfm.bm_unit_id,
                SUM(pn.levelTo) as actual_generation_mw
            FROM `{PROJECT_ID}.{DATASET}.bmrs_pn` pn
            JOIN `{PROJECT_ID}.{DATASET}.wind_farm_to_bmu` wfm
                ON pn.bmUnit = wfm.bm_unit_id
            WHERE DATE(pn.settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                AND pn.levelTo > 0
            GROUP BY settlement_date, settlementPeriod, farm_name, bm_unit_id
        ),
        forecast_data AS (
            SELECT
                settlement_date,
                settlement_period,
                forecast_mw as total_forecast_mw
            FROM `{PROJECT_ID}.{DATASET}.wind_forecast_sp`
            WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        ),
        farm_totals AS (
            SELECT
                settlement_date,
                settlementPeriod,
                farm_name,
                SUM(actual_generation_mw) as farm_actual_mw
            FROM farm_generation
            GROUP BY settlement_date, settlementPeriod, farm_name
        ),
        system_totals AS (
            SELECT
                settlement_date,
                settlementPeriod,
                SUM(actual_generation_mw) as system_actual_mw
            FROM farm_generation
            GROUP BY settlement_date, settlementPeriod
        ),
        farm_with_forecast AS (
            SELECT
                ft.farm_name,
                ft.settlement_date,
                ft.settlementPeriod,
                ft.farm_actual_mw,
                st.system_actual_mw,
                fd.total_forecast_mw,
                -- Proportional forecast allocation
                fd.total_forecast_mw * (ft.farm_actual_mw / st.system_actual_mw) as farm_forecast_mw
            FROM farm_totals ft
            JOIN system_totals st
                ON ft.settlement_date = st.settlement_date
                AND ft.settlementPeriod = st.settlementPeriod
            LEFT JOIN forecast_data fd
                ON ft.settlement_date = fd.settlement_date
                AND ft.settlementPeriod = fd.settlement_period
            WHERE st.system_actual_mw > 0
        )
        SELECT
            farm_name,
            COUNT(*) as num_periods,
            AVG(farm_actual_mw) as avg_actual_mw,
            AVG(farm_forecast_mw) as avg_forecast_mw,
            AVG(farm_forecast_mw - farm_actual_mw) as bias_mw,
            SUM(ABS(farm_forecast_mw - farm_actual_mw)) / NULLIF(SUM(farm_actual_mw), 0) * 100 as wape_percent,
            SQRT(AVG(POW(farm_forecast_mw - farm_actual_mw, 2))) as rmse_mw
        FROM farm_with_forecast
        WHERE farm_forecast_mw IS NOT NULL
        GROUP BY farm_name
        HAVING COUNT(*) >= 100  -- Minimum data requirement
        ORDER BY wape_percent DESC
        LIMIT 15
        """

        df = bq_client.query(query).to_dataframe()

        if df.empty:
            logging.warning("No per-farm forecast data available")
            return pd.DataFrame()

        # Add ranking
        df['rank'] = range(1, len(df) + 1)
        df['performance'] = df['wape_percent'].apply(
            lambda x: '🔴 Poor' if x > 30 else ('🟡 Fair' if x > 20 else '🟢 Good')
        )

        logging.info(f"Retrieved per-farm errors for {len(df)} farms")
        return df

    except Exception as e:
        logging.error(f"Per-farm forecast error query failed: {e}")
        return pd.DataFrame()


def get_imbalance_price_correlation(bq_client):
    """
    Correlate wind forecast errors with imbalance prices
    Calculate revenue impact of forecast misses
    """
    try:
        query = f"""
        WITH forecast_errors AS (
            SELECT
                settlement_date,
                settlement_period,
                actual_mw_total,
                forecast_mw,
                error_mw,
                abs_error_mw,
                abs_percentage_error
            FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_sp`
            WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        ),
        imbalance_prices AS (
            SELECT
                CAST(settlementDate AS DATE) as settlement_date,
                settlementPeriod as settlement_period,
                systemSellPrice as ssp,
                systemBuyPrice as sbp,
                -- Since P305, SSP = SBP (single imbalance price)
                systemSellPrice as imbalance_price
            FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
            WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        )
        SELECT
            fe.settlement_date,
            fe.settlement_period,
            fe.abs_error_mw,
            fe.abs_percentage_error,
            fe.error_mw,
            ip.imbalance_price,
            -- Revenue impact: error volume × price
            fe.abs_error_mw * ip.imbalance_price / 2 as revenue_impact_gbp,
            -- Classify error severity
            CASE
                WHEN fe.abs_percentage_error > 30 THEN 'High'
                WHEN fe.abs_percentage_error > 15 THEN 'Medium'
                ELSE 'Low'
            END as error_severity,
            -- Classify price severity
            CASE
                WHEN ip.imbalance_price > 100 THEN 'High'
                WHEN ip.imbalance_price > 50 THEN 'Medium'
                ELSE 'Low'
            END as price_severity
        FROM forecast_errors fe
        INNER JOIN imbalance_prices ip
            ON fe.settlement_date = ip.settlement_date
            AND fe.settlement_period = ip.settlement_period
        WHERE fe.abs_error_mw > 500  -- Significant errors only
        ORDER BY revenue_impact_gbp DESC
        """

        df = bq_client.query(query).to_dataframe()

        if df.empty:
            logging.warning("No imbalance price correlation data available")
            return {
                'correlation_df': pd.DataFrame(),
                'total_impact_7d': 0,
                'avg_impact_per_error': 0,
                'worst_period': None
            }

        # Calculate aggregates
        total_impact = df['revenue_impact_gbp'].sum()
        avg_impact = df['revenue_impact_gbp'].mean()
        worst_period = df.iloc[0] if len(df) > 0 else None

        # Calculate correlation coefficient
        if len(df) > 2:
            correlation = df['abs_error_mw'].corr(df['imbalance_price'])
        else:
            correlation = 0

        logging.info(f"Calculated imbalance impact: £{total_impact:,.0f} over 7 days")

        return {
            'correlation_df': df.head(20),  # Top 20 worst impacts
            'total_impact_7d': total_impact,
            'avg_impact_per_error': avg_impact,
            'worst_period': worst_period,
            'correlation_coef': correlation
        }

    except Exception as e:
        logging.error(f"Imbalance price correlation query failed: {e}")
        return {
            'correlation_df': pd.DataFrame(),
            'total_impact_7d': 0,
            'avg_impact_per_error': 0,
            'worst_period': None,
            'correlation_coef': 0
        }


def get_hour_of_day_accuracy(bq_client):
    """
    Calculate forecast accuracy patterns by hour of day and day of week
    Identifies worst forecasting periods
    """
    try:
        query = f"""
        SELECT
            hour_of_day,
            day_of_week,
            COUNT(*) as num_periods,
            AVG(abs_percentage_error) as avg_error_pct,
            AVG(abs_error_mw) as avg_error_mw,
            SUM(CASE WHEN large_ramp_miss_flag = 1 THEN 1 ELSE 0 END) as ramp_misses
        FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_sp`
        WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY hour_of_day, day_of_week
        HAVING COUNT(*) >= 4  -- Minimum 4 observations
        ORDER BY hour_of_day, day_of_week
        """

        df = bq_client.query(query).to_dataframe()

        if df.empty:
            logging.warning("No hour-of-day accuracy data available")
            return pd.DataFrame()

        # Create heatmap matrix (7 days × 24 hours)
        heatmap = df.pivot(index='day_of_week', columns='hour_of_day', values='avg_error_pct')

        # Fill missing values with NaN
        heatmap = heatmap.reindex(index=range(7), columns=range(24))

        # Identify worst periods
        worst_hours = df.nlargest(5, 'avg_error_pct')[['hour_of_day', 'day_of_week', 'avg_error_pct']]

        logging.info(f"Calculated hour-of-day accuracy for {len(df)} time periods")

        return {
            'raw_data': df,
            'heatmap': heatmap,
            'worst_hours': worst_hours
        }

    except Exception as e:
        logging.error(f"Hour-of-day accuracy query failed: {e}")
        return {
            'raw_data': pd.DataFrame(),
            'heatmap': pd.DataFrame(),
            'worst_hours': pd.DataFrame()
        }


def create_enhanced_dashboard_sections(sheets_service, bq_client):
    """
    Create new enhanced sections in the dashboard
    """
    try:
        batch_data = []

        # ==================================================
        # SECTION 5: PER-FARM ERROR ANALYSIS (A53:N62)
        # ==================================================

        logging.info("Fetching per-farm forecast errors...")
        farm_errors = get_per_farm_forecast_errors(bq_client)

        # Row 53: Section header
        batch_data.append({
            'range': f'{SHEET_NAME}!A53:N53',
            'values': [['🎯 PER-FARM FORECAST ACCURACY (Worst Performers)', '', '', '', '', '', '', '', '', '', '', '', '', '']]
        })

        # Row 54: Column headers
        batch_data.append({
            'range': f'{SHEET_NAME}!A54:G54',
            'values': [['Rank', 'Farm Name', 'WAPE %', 'Bias (MW)', 'RMSE (MW)', 'Avg Actual (MW)', 'Performance']]
        })

        # Rows 55-62: Farm data
        farm_rows = []
        if not farm_errors.empty:
            for idx, row in farm_errors.head(8).iterrows():
                farm_rows.append([
                    int(row['rank']),
                    row['farm_name'],
                    f"{row['wape_percent']:.1f}%",
                    f"{row['bias_mw']:.0f}",
                    f"{row['rmse_mw']:.0f}",
                    f"{row['avg_actual_mw']:.0f}",
                    row['performance']
                ])
        else:
            farm_rows = [['No data available', '', '', '', '', '', '']] * 8

        batch_data.append({
            'range': f'{SHEET_NAME}!A55:G62',
            'values': farm_rows
        })

        # ==================================================
        # SECTION 6: IMBALANCE PRICE IMPACT (A63:N72)
        # ==================================================

        logging.info("Calculating imbalance price correlation...")
        price_impact = get_imbalance_price_correlation(bq_client)

        # Row 63: Section header
        batch_data.append({
            'range': f'{SHEET_NAME}!A63:N63',
            'values': [['💰 FORECAST ERROR REVENUE IMPACT (Last 7 Days)', '', '', '', '', '', '', '', '', '', '', '', '', '']]
        })

        # Row 64: Summary KPIs
        total_impact = price_impact['total_impact_7d']
        avg_impact = price_impact['avg_impact_per_error']
        correlation = price_impact.get('correlation_coef', 0)

        batch_data.append({
            'range': f'{SHEET_NAME}!A64:F64',
            'values': [[
                f"Total Lost Revenue: £{total_impact:,.0f}",
                f"Avg Impact/Error: £{avg_impact:,.0f}",
                f"Correlation: {correlation:.2f}",
                '', '', ''
            ]]
        })

        # Row 65: Column headers
        batch_data.append({
            'range': f'{SHEET_NAME}!A65:G65',
            'values': [['Date', 'SP', 'Error (MW)', 'Error %', 'Price (£/MWh)', 'Impact (£)', 'Severity']]
        })

        # Rows 66-72: Top impact periods
        impact_rows = []
        correlation_df = price_impact['correlation_df']
        if not correlation_df.empty:
            for idx, row in correlation_df.head(7).iterrows():
                impact_rows.append([
                    row['settlement_date'].strftime('%Y-%m-%d') if pd.notna(row['settlement_date']) else '',
                    int(row['settlement_period']) if pd.notna(row['settlement_period']) else '',
                    f"{row['abs_error_mw']:.0f}",
                    f"{row['abs_percentage_error']:.1f}%",
                    f"£{row['imbalance_price']:.2f}",
                    f"£{row['revenue_impact_gbp']:,.0f}",
                    f"{row['error_severity']} / {row['price_severity']}"
                ])
        else:
            impact_rows = [['No significant errors', '', '', '', '', '', '']] * 7

        batch_data.append({
            'range': f'{SHEET_NAME}!A66:G72',
            'values': impact_rows
        })

        # ==================================================
        # SECTION 7: HOUR-OF-DAY ACCURACY HEATMAP (A73:N82)
        # ==================================================

        logging.info("Calculating hour-of-day accuracy patterns...")
        hour_data = get_hour_of_day_accuracy(bq_client)

        # Row 73: Section header
        batch_data.append({
            'range': f'{SHEET_NAME}!A73:N73',
            'values': [['📅 FORECAST ACCURACY BY TIME (30-Day Pattern)', '', '', '', '', '', '', '', '', '', '', '', '', '']]
        })

        # Row 74: Worst hours summary
        worst_hours = hour_data.get('worst_hours', pd.DataFrame())
        if not worst_hours.empty:
            worst_summary = "Worst: " + ", ".join([
                f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][int(row['day_of_week'])]} {int(row['hour_of_day']):02d}:00 ({row['avg_error_pct']:.1f}%)"
                for _, row in worst_hours.head(3).iterrows()
            ])
        else:
            worst_summary = "No pattern data available"

        batch_data.append({
            'range': f'{SHEET_NAME}!A74:N74',
            'values': [[worst_summary, '', '', '', '', '', '', '', '', '', '', '', '', '']]
        })

        # Rows 75-82: Hour-of-day data table
        raw_data = hour_data.get('raw_data', pd.DataFrame())
        if not raw_data.empty:
            # Row 75: Headers
            batch_data.append({
                'range': f'{SHEET_NAME}!A75:E75',
                'values': [['Hour', 'Day', 'Avg Error %', 'Avg Error MW', 'Ramp Misses']]
            })

            # Rows 76-82: Sample data (show subset)
            hour_rows = []
            sample_data = raw_data.nsmallest(7, 'avg_error_pct')  # Best 7 periods
            for _, row in sample_data.iterrows():
                day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][int(row['day_of_week'])]
                hour_rows.append([
                    f"{int(row['hour_of_day']):02d}:00",
                    day_name,
                    f"{row['avg_error_pct']:.1f}%",
                    f"{row['avg_error_mw']:.0f}",
                    int(row['ramp_misses'])
                ])

            batch_data.append({
                'range': f'{SHEET_NAME}!A76:E82',
                'values': hour_rows
            })
        else:
            batch_data.append({
                'range': f'{SHEET_NAME}!A75:E82',
                'values': [['No hour-of-day data available', '', '', '', '']] * 8
            })

        # ==================================================
        # BATCH UPDATE TO GOOGLE SHEETS
        # ==================================================

        logging.info(f"Updating {len(batch_data)} ranges in Google Sheets...")

        body = {'data': batch_data, 'valueInputOption': 'USER_ENTERED'}
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()

        logging.info("✅ Enhanced dashboard sections created successfully")

        # Apply formatting
        apply_enhanced_formatting(sheets_service)

        return True

    except Exception as e:
        logging.error(f"Failed to create enhanced dashboard sections: {e}")
        return False


def apply_enhanced_formatting(sheets_service):
    """
    Apply formatting to new dashboard sections
    """
    try:
        requests = []

        # Section headers (rows 53, 63, 73)
        for row_index in [52, 62, 72]:  # 0-indexed
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,  # Adjust if needed
                        'startRowIndex': row_index,
                        'endRowIndex': row_index + 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 14
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                            'textFormat': {
                                'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                                'fontSize': 12,
                                'bold': True
                            },
                            'horizontalAlignment': 'LEFT'
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            })

        # Column headers (rows 54, 65, 75)
        for row_index in [53, 64, 74]:  # 0-indexed
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': row_index,
                        'endRowIndex': row_index + 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 7
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                            'textFormat': {
                                'bold': True,
                                'fontSize': 10
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            })

        # Apply all formatting
        body = {'requests': requests}
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()

        logging.info("✅ Enhanced formatting applied")

    except Exception as e:
        logging.error(f"Failed to apply enhanced formatting: {e}")


def main():
    """
    Main execution function
    """
    logging.info("="*80)
    logging.info("ENHANCED WIND ANALYSIS DASHBOARD")
    logging.info("="*80)

    # Initialize BigQuery client
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')

    # Initialize Google Sheets client
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=creds)

    # Create enhanced sections
    success = create_enhanced_dashboard_sections(sheets_service, bq_client)

    if success:
        logging.info("\n" + "="*80)
        logging.info("✅ ENHANCED DASHBOARD DEPLOYMENT COMPLETE")
        logging.info("="*80)
        logging.info(f"\nNew Sections Added:")
        logging.info(f"  📍 A53-62: Per-Farm Forecast Accuracy (Top 8 worst performers)")
        logging.info(f"  📍 A63-72: Imbalance Price Revenue Impact (Last 7 days)")
        logging.info(f"  📍 A73-82: Hour-of-Day Accuracy Pattern (30-day analysis)")
        logging.info(f"\nDashboard URL:")
        logging.info(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    else:
        logging.error("\n❌ Enhanced dashboard deployment failed")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
