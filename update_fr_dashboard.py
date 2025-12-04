#!/usr/bin/env python3
"""
FR Optimizer Dashboard Integration
===================================
Updates Google Sheets BESS dashboard with FR revenue optimization results.

Displays:
- Monthly FR revenue summary
- Service mix (DC/DM/DR distribution)
- Daily revenue breakdown
- Comparison vs single-service strategy
- Color-coded service selection per EFA block

Author: George Major
Date: 1 December 2025
"""

import os
import datetime as dt
import pandas as pd
from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class FRDashboardUpdater:
    """Updates Google Sheets with FR optimization results"""
    
    # Service colors for visualization
    SERVICE_COLORS = {
        'DC': {'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1.0}},  # Light blue
        'DM': {'backgroundColor': {'red': 0.9, 'green': 1.0, 'blue': 0.8}},  # Light green
        'DR': {'backgroundColor': {'red': 1.0, 'green': 0.9, 'blue': 0.8}},  # Light orange
        'IDLE': {'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}},  # Light gray
    }
    
    def __init__(
        self,
        spreadsheet_id: str = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc",
        project_id: str = "inner-cinema-476211-u9",
        dataset_id: str = "uk_energy_prod",
    ):
        self.spreadsheet_id = spreadsheet_id
        self.project_id = project_id
        self.dataset_id = dataset_id
        
        # Initialize BigQuery
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
        self.bq_client = bigquery.Client(project=project_id, location="US")
        
        # Initialize Google Sheets
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'inner-cinema-credentials.json', 
            scope
        )
        self.sheets_client = gspread.authorize(creds)
        self.spreadsheet = self.sheets_client.open_by_key(spreadsheet_id)
        
        print(f"✅ FR Dashboard Updater initialized")
        print(f"   Spreadsheet: {spreadsheet_id}")
        print(f"   BigQuery: {project_id}.{dataset_id}")
    
    def get_or_create_sheet(self, sheet_name: str) -> gspread.Worksheet:
        """Get existing sheet or create new one"""
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            print(f"   Found existing sheet: {sheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
            print(f"   Created new sheet: {sheet_name}")
        return sheet
    
    def load_fr_schedule(
        self,
        asset_id: str,
        start_date: dt.date,
        end_date: dt.date,
    ) -> pd.DataFrame:
        """Load FR schedule from BigQuery"""
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.dataset_id}.bess_fr_schedule`
        WHERE asset_id = @asset_id
          AND efa_date BETWEEN @start_date AND @end_date
        ORDER BY efa_date, efa_block
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("asset_id", "STRING", asset_id),
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        
        df = self.bq_client.query(query, job_config=job_config).to_dataframe()
        return df
    
    def update_monthly_summary(
        self,
        sheet: gspread.Worksheet,
        df: pd.DataFrame,
    ):
        """Update monthly summary section"""
        
        # Calculate summary stats
        total_avail = df['availability_revenue_gbp'].sum()
        total_deg = df['degradation_cost_gbp'].sum()
        total_net = df['net_margin_gbp'].sum()
        annual_net = total_net * 12
        
        # Service mix
        service_counts = df['best_service'].value_counts()
        
        # Write header
        sheet.update_acell('A1', '🔋 FR Revenue Optimizer - Monthly Summary')
        sheet.format('A1', {
            'textFormat': {'bold': True, 'fontSize': 14},
            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8}
        })
        
        # Summary stats
        row = 3
        data = [
            ['Month', df['efa_date'].iloc[0].strftime('%B %Y')],
            ['Total Blocks', len(df)],
            ['', ''],
            ['Revenue Summary', ''],
            ['Availability Revenue', f'£{total_avail:,.2f}'],
            ['Degradation Cost', f'£{total_deg:,.2f}'],
            ['Net Margin', f'£{total_net:,.2f}'],
            ['', ''],
            ['Annualized', f'£{annual_net:,.2f}'],
            ['', ''],
            ['Service Mix', ''],
        ]
        
        for label, value in data:
            sheet.update_acell(f'A{row}', label)
            sheet.update_acell(f'B{row}', value)
            if label in ['Net Margin', 'Annualized']:
                sheet.format(f'A{row}:B{row}', {'textFormat': {'bold': True}})
            row += 1
        
        # Service breakdown
        for svc in ['DC', 'DM', 'DR', 'IDLE']:
            count = service_counts.get(svc, 0)
            pct = count / len(df) * 100 if len(df) > 0 else 0
            sheet.update_acell(f'A{row}', f'  {svc}')
            sheet.update_acell(f'B{row}', f'{count} blocks ({pct:.1f}%)')
            row += 1
        
        print(f"✅ Updated monthly summary")
    
    def update_daily_breakdown(
        self,
        sheet: gspread.Worksheet,
        df: pd.DataFrame,
    ):
        """Update daily revenue breakdown"""
        
        # Group by date
        df['date'] = pd.to_datetime(df['efa_date']).dt.date
        daily = df.groupby('date').agg({
            'availability_revenue_gbp': 'sum',
            'degradation_cost_gbp': 'sum',
            'net_margin_gbp': 'sum',
        }).round(2)
        
        # Also get service counts per day
        service_counts = df.groupby(['date', 'best_service']).size().unstack(fill_value=0)
        
        # Combine
        daily = daily.join(service_counts)
        daily = daily.reset_index()
        
        # Write to sheet starting at row 20
        start_row = 20
        
        # Header
        sheet.update_acell(f'A{start_row}', '📅 Daily Revenue Breakdown')
        sheet.format(f'A{start_row}', {'textFormat': {'bold': True, 'fontSize': 12}})
        
        # Column headers
        headers = ['Date', 'Revenue (£)', 'Degradation (£)', 'Net (£)', 'DC', 'DM', 'DR', 'IDLE']
        for col_idx, header in enumerate(headers):
            sheet.update_cell(start_row + 1, col_idx + 1, header)
        
        sheet.format(f'A{start_row+1}:H{start_row+1}', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        # Data rows
        for row_idx, (_, row) in enumerate(daily.iterrows()):
            row_num = start_row + 2 + row_idx
            sheet.update_cell(row_num, 1, str(row['date']))
            sheet.update_cell(row_num, 2, f"{row['availability_revenue_gbp']:.2f}")
            sheet.update_cell(row_num, 3, f"{row['degradation_cost_gbp']:.2f}")
            sheet.update_cell(row_num, 4, f"{row['net_margin_gbp']:.2f}")
            sheet.update_cell(row_num, 5, int(row.get('DC', 0)))
            sheet.update_cell(row_num, 6, int(row.get('DM', 0)))
            sheet.update_cell(row_num, 7, int(row.get('DR', 0)))
            sheet.update_cell(row_num, 8, int(row.get('IDLE', 0)))
        
        print(f"✅ Updated daily breakdown ({len(daily)} days)")
    
    def update_service_schedule(
        self,
        sheet: gspread.Worksheet,
        df: pd.DataFrame,
    ):
        """Update EFA block service schedule with color coding"""
        
        # Start at column K
        start_col = 'K'
        start_row = 3
        
        # Header
        sheet.update_acell(f'{start_col}{start_row}', '🗓️ Service Schedule (EFA Blocks)')
        sheet.format(f'{start_col}{start_row}', {
            'textFormat': {'bold': True, 'fontSize': 12}
        })
        
        # Column headers
        sheet.update_cell(start_row + 1, 11, 'Date')
        for block in range(1, 7):
            sheet.update_cell(start_row + 1, 11 + block, f'Block {block}')
        
        sheet.format(f'K{start_row+1}:Q{start_row+1}', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        # Group by date
        df['date'] = pd.to_datetime(df['efa_date']).dt.date
        dates = df['date'].unique()
        
        # Write data
        for row_idx, date in enumerate(dates):
            row_num = start_row + 2 + row_idx
            sheet.update_cell(row_num, 11, str(date))
            
            # Get blocks for this date
            date_df = df[df['date'] == date].sort_values('efa_block')
            
            for _, block_row in date_df.iterrows():
                block_num = block_row['efa_block']
                service = block_row['best_service']
                col_num = 11 + block_num
                
                # Write service name
                sheet.update_cell(row_num, col_num, service)
                
                # Apply color
                cell_range = gspread.utils.rowcol_to_a1(row_num, col_num)
                sheet.format(cell_range, self.SERVICE_COLORS.get(service, {}))
        
        print(f"✅ Updated service schedule ({len(dates)} days × 6 blocks)")
    
    def update_dashboard(
        self,
        asset_id: str,
        start_date: dt.date,
        end_date: dt.date,
        sheet_name: str = "FR Revenue",
    ):
        """Update complete FR dashboard"""
        
        print(f"\n🔄 Updating FR Revenue Dashboard")
        print(f"   Asset: {asset_id}")
        print(f"   Period: {start_date} to {end_date}")
        
        # Load data
        df = self.load_fr_schedule(asset_id, start_date, end_date)
        
        if df.empty:
            print(f"⚠️  No data found for {asset_id} in date range")
            return
        
        print(f"   Loaded {len(df)} schedule records")
        
        # Get or create sheet
        sheet = self.get_or_create_sheet(sheet_name)
        
        # Clear existing content
        sheet.clear()
        
        # Update sections
        self.update_monthly_summary(sheet, df)
        self.update_daily_breakdown(sheet, df)
        self.update_service_schedule(sheet, df)
        
        print(f"\n✅ Dashboard update complete!")
        print(f"   View: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")


def main():
    """Update dashboard with latest FR optimization results"""
    
    updater = FRDashboardUpdater()
    
    # Update for January 2025
    updater.update_dashboard(
        asset_id="BESS_2P5MW_5MWH",
        start_date=dt.date(2025, 1, 1),
        end_date=dt.date(2025, 1, 31),
        sheet_name="FR Revenue"
    )


if __name__ == "__main__":
    main()
