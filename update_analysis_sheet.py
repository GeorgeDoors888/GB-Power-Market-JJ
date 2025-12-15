#!/usr/bin/env python3
"""
Update the Analysis sheet with unified historical + real-time data
Queries unified BigQuery views and populates Google Sheets
"""

import pickle
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
import statistics

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Analysis'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'


def get_date_range_from_sheet(sheet):
    """Get date range from user selection in the sheet"""
    try:
        quick_select = sheet.acell('C6').value
        
        if quick_select and quick_select != "Custom":
            # Calculate based on quick select
            end_date = datetime.now()
            
            ranges = {
                "24 Hours": timedelta(hours=24),
                "1 Week": timedelta(days=7),
                "1 Month": timedelta(days=30),
                "6 Months": timedelta(days=180),
                "12 Months": timedelta(days=365),
                "24 Months": timedelta(days=730),
                "3 Years": timedelta(days=1095),
                "4 Years": timedelta(days=1460),
                "All Time": timedelta(days=365*5)  # 5 years max (since 2020)
            }
            
            start_date = end_date - ranges.get(quick_select, timedelta(days=30))
        else:
            # Use custom range
            from_date = sheet.acell('H7').value
            to_date = sheet.acell('H8').value
            
            if from_date and to_date:
                start_date = datetime.strptime(from_date, '%d/%m/%Y')
                end_date = datetime.strptime(to_date, '%d/%m/%Y')
            else:
                # Default to last month
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
        
        return start_date, end_date
        
    except Exception as e:
        print(f"⚠️ Error parsing date range: {e}, using default (last month)")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return start_date, end_date


def query_unified_frequency(bq_client, start_date, end_date):
    """Query unified frequency data from bmrs_freq_unified view"""
    query = f"""
    SELECT 
        timestamp,
        frequency,
        source,
        recordType
    FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_unified`
    WHERE timestamp BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
    ORDER BY timestamp DESC
    LIMIT 50000
    """
    
    print(f"  Querying frequency data...")
    try:
        results = list(bq_client.query(query).result())
        print(f"  ✅ Retrieved {len(results)} frequency records")
        return results
    except Exception as e:
        print(f"  ⚠️ Error querying frequency: {e}")
        return []


def query_unified_market_prices(bq_client, start_date, end_date):
    """Query unified market index data from bmrs_mid_unified view"""
    query = f"""
    SELECT 
        timestamp,
        settlementPeriod,
        systemSellPrice,
        systemBuyPrice,
        source
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_unified`
    WHERE timestamp BETWEEN '{start_date.date().isoformat()}' 
          AND '{end_date.date().isoformat()}'
    ORDER BY timestamp DESC, settlementPeriod DESC
    LIMIT 10000
    """
    
    print(f"  Querying market price data...")
    try:
        results = list(bq_client.query(query).result())
        print(f"  ✅ Retrieved {len(results)} market price records")
        return results
    except Exception as e:
        print(f"  ⚠️ Error querying market prices: {e}")
        return []


def query_unified_generation(bq_client, start_date, end_date):
    """Query unified generation data from bmrs_fuelinst_unified view"""
    query = f"""
    SELECT 
        timestamp,
        fuelType,
        generation,
        source,
        settlementDate,
        settlementPeriod
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_unified`
    WHERE timestamp BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
    ORDER BY timestamp DESC
    LIMIT 50000
    """
    
    print(f"  Querying generation data...")
    try:
        results = list(bq_client.query(query).result())
        print(f"  ✅ Retrieved {len(results)} generation records")
        return results
    except Exception as e:
        print(f"  ⚠️ Error querying generation: {e}")
        return []


def calculate_frequency_metrics(data):
    """Calculate frequency statistics"""
    if not data:
        return {
            'count': 0,
            'avg': 0,
            'min': 0,
            'max': 0,
            'std_dev': 0,
            'below_threshold': 0
        }
    
    frequencies = [row.frequency for row in data if row.frequency is not None]
    
    if not frequencies:
        return {
            'count': 0,
            'avg': 0,
            'min': 0,
            'max': 0,
            'std_dev': 0,
            'below_threshold': 0
        }
    
    return {
        'count': len(frequencies),
        'avg': sum(frequencies) / len(frequencies),
        'min': min(frequencies),
        'max': max(frequencies),
        'std_dev': statistics.stdev(frequencies) if len(frequencies) > 1 else 0,
        'below_threshold': sum(1 for f in frequencies if f < 49.8) / len(frequencies) * 100
    }


def calculate_price_metrics(data):
    """Calculate market price statistics"""
    if not data:
        return {
            'count': 0,
            'avg_sell': 0,
            'avg_buy': 0,
            'max_sell': 0,
            'min_sell': 0,
            'volatility': 0
        }
    
    sell_prices = [row.systemSellPrice for row in data if row.systemSellPrice is not None]
    buy_prices = [row.systemBuyPrice for row in data if row.systemBuyPrice is not None]
    
    if not sell_prices:
        return {
            'count': 0,
            'avg_sell': 0,
            'avg_buy': 0,
            'max_sell': 0,
            'min_sell': 0,
            'volatility': 0
        }
    
    avg_sell = sum(sell_prices) / len(sell_prices)
    
    return {
        'count': len(sell_prices),
        'avg_sell': avg_sell,
        'avg_buy': sum(buy_prices) / len(buy_prices) if buy_prices else 0,
        'max_sell': max(sell_prices),
        'min_sell': min(sell_prices),
        'volatility': (statistics.stdev(sell_prices) / avg_sell * 100) if len(sell_prices) > 1 and avg_sell > 0 else 0
    }


def calculate_generation_metrics(data):
    """Calculate generation statistics by fuel type"""
    if not data:
        return {}
    
    # Group by fuel type
    fuel_totals = {}
    for row in data:
        if row.fuelType and row.generation:
            if row.fuelType not in fuel_totals:
                fuel_totals[row.fuelType] = 0
            fuel_totals[row.fuelType] += row.generation
    
    total_generation = sum(fuel_totals.values())
    
    # Calculate percentages
    fuel_percentages = {
        fuel: (total / total_generation * 100) if total_generation > 0 else 0
        for fuel, total in fuel_totals.items()
    }
    
    return {
        'total': total_generation,
        'by_fuel': fuel_totals,
        'percentages': fuel_percentages
    }


def update_frequency_section(sheet, freq_data, start_date, end_date):
    """Update the System Frequency Analysis section"""
    print("  Updating frequency section...")
    
    metrics = calculate_frequency_metrics(freq_data)
    
    # Update record count and time range
    sheet.update_acell('B20', f"{metrics['count']:,}")
    sheet.update_acell('B21', f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    
    # Update key metrics
    sheet.update_acell('B24', f"{metrics['avg']:.3f} Hz")
    sheet.update_acell('B25', f"{metrics['min']:.3f} Hz")
    sheet.update_acell('B26', f"{metrics['max']:.3f} Hz")
    sheet.update_acell('B27', f"{metrics['std_dev']:.4f} Hz")
    sheet.update_acell('B28', f"{metrics['below_threshold']:.2f}%")
    
    # Find min frequency event
    if freq_data:
        min_row = min(freq_data, key=lambda x: x.frequency if x.frequency else 50)
        if min_row.frequency:
            min_event = f"(⚠️ Low Event on {min_row.timestamp.strftime('%d/%m/%Y %H:%M')})"
            sheet.update_acell('C25', min_event)


def update_market_prices_section(sheet, price_data):
    """Update the Market Prices Analysis section"""
    print("  Updating market prices section...")
    
    metrics = calculate_price_metrics(price_data)
    
    # Update statistics (rows 33-38)
    sheet.update_acell('A33', 'Key Metrics:')
    sheet.update_acell('A34', '• Avg System Sell Price:')
    sheet.update_acell('B34', f"£{metrics['avg_sell']:.2f}/MWh")
    
    sheet.update_acell('A35', '• Avg System Buy Price:')
    sheet.update_acell('B35', f"£{metrics['avg_buy']:.2f}/MWh")
    
    sheet.update_acell('A36', '• Max Price:')
    sheet.update_acell('B36', f"£{metrics['max_sell']:.2f}/MWh")
    
    sheet.update_acell('A37', '• Min Price:')
    sheet.update_acell('B37', f"£{metrics['min_sell']:.2f}/MWh")
    
    sheet.update_acell('A38', '• Price Volatility:')
    sheet.update_acell('B38', f"{metrics['volatility']:.1f}%")


def update_generation_section(sheet, gen_data):
    """Update the Generation Mix Analysis section"""
    print("  Updating generation section...")
    
    metrics = calculate_generation_metrics(gen_data)
    
    if not metrics:
        sheet.update_acell('A47', 'No generation data available for selected period')
        return
    
    # Update total generation
    sheet.update_acell('A47', '• Total Generation:')
    sheet.update_acell('B47', f"{metrics['total']/1000:.0f} GWh")
    
    # Update fuel breakdown (rows 48-52)
    row = 48
    for fuel_type, percentage in sorted(metrics['percentages'].items(), key=lambda x: x[1], reverse=True):
        if row > 55:  # Limit to available rows
            break
        sheet.update_acell(f'A{row}', f'• {fuel_type}:')
        sheet.update_acell(f'B{row}', f"{percentage:.1f}%")
        sheet.update_acell(f'C{row}', f"({metrics['by_fuel'][fuel_type]/1000:.0f} GWh)")
        row += 1


def update_raw_data_table(sheet, freq_data, price_data, gen_data):
    """Update the raw data table at the bottom"""
    print("  Updating raw data table...")
    
    # Combine data sources (simplified - matching by timestamp)
    table_data = [['Timestamp', 'Freq (Hz)', 'SSP (£)', 'SBP (£)', 'Gen (MW)', 'Source', 'Fuel Type', 'Period']]
    
    # Take first 100 rows
    max_rows = min(100, len(freq_data))
    
    for i in range(max_rows):
        freq_row = freq_data[i] if i < len(freq_data) else None
        
        # Find matching price and generation data (simplified)
        price_row = price_data[i] if i < len(price_data) else None
        gen_row = gen_data[i] if i < len(gen_data) else None
        
        table_data.append([
            freq_row.timestamp.strftime('%d/%m/%y %H:%M') if freq_row else '',
            f"{freq_row.frequency:.3f}" if freq_row and freq_row.frequency else '',
            f"£{price_row.systemSellPrice:.2f}" if price_row and price_row.systemSellPrice else '',
            f"£{price_row.systemBuyPrice:.2f}" if price_row and price_row.systemBuyPrice else '',
            f"{gen_row.generation:.0f}" if gen_row and gen_row.generation else '',
            freq_row.source if freq_row else '',
            gen_row.fuelType if gen_row else '',
            f"SP{price_row.settlementPeriod}" if price_row and price_row.settlementPeriod else ''
        ])
    
    # Update table (starting at row 76)
    try:
        sheet.update(f'A76:H{76 + len(table_data) - 1}', table_data, value_input_option='USER_ENTERED')
        print(f"  ✅ Updated {len(table_data)-1} rows in data table")
    except Exception as e:
        print(f"  ⚠️ Error updating table: {e}")


def main():
    """Main execution"""
    print("=" * 70)
    print("📊 UPDATING ANALYSIS SHEET")
    print("=" * 70)
    print()
    
    # Initialize BigQuery
    print("Connecting to BigQuery...")
    bq_client = bigquery.Client(project=PROJECT_ID)
    print("✅ Connected")
    print()
    
    # Initialize Google Sheets
    print("Connecting to Google Sheets...")
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
        print(f"✅ Found sheet: {SHEET_NAME}")
    except gspread.exceptions.WorksheetNotFound:
        print(f"❌ Sheet '{SHEET_NAME}' not found!")
        print("Run create_analysis_sheet.py first to create the sheet.")
        return
    
    print()
    
    # Get date range from sheet
    print("Reading date range from sheet...")
    start_date, end_date = get_date_range_from_sheet(sheet)
    print(f"✅ Date range: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
    print()
    
    # Query unified views
    print("Querying unified BigQuery views...")
    freq_data = query_unified_frequency(bq_client, start_date, end_date)
    price_data = query_unified_market_prices(bq_client, start_date, end_date)
    gen_data = query_unified_generation(bq_client, start_date, end_date)
    print()
    
    # Update sheet sections
    print("Updating sheet sections...")
    update_frequency_section(sheet, freq_data, start_date, end_date)
    update_market_prices_section(sheet, price_data)
    update_generation_section(sheet, gen_data)
    update_raw_data_table(sheet, freq_data, price_data, gen_data)
    print()
    
    # Update last refresh timestamp
    print("Updating metadata...")
    sheet.update_acell('A211', f"Last Updated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Auto-refresh: Every 5 minutes")
    print()
    
    # Summary
    print("=" * 70)
    print("✅ ANALYSIS SHEET UPDATE COMPLETE!")
    print("=" * 70)
    print()
    print(f"📊 Data Summary:")
    print(f"  • Frequency records: {len(freq_data):,}")
    print(f"  • Market price records: {len(price_data):,}")
    print(f"  • Generation records: {len(gen_data):,}")
    print(f"  • Date range: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    print()
    print(f"🔗 View sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    print()


if __name__ == '__main__':
    main()
