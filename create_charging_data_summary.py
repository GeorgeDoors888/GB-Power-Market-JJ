#!/usr/bin/env python3
"""
Generate comprehensive charging data summary per year for all 14 DNOs
Reads from dno_files_by_distribution_id_and_year.json and creates markdown report
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_json_data():
    """Load the distribution ID JSON file"""
    json_path = Path("/Users/georgemajor/GB Power Market JJ/dno_files_by_distribution_id_and_year.json")
    with open(json_path, 'r') as f:
        return json.load(f)

def analyze_charging_data(data):
    """Analyze charging data by year and DNO"""
    
    # Extract files by distribution ID
    files_by_dist = data.get('files_by_distribution_id', {})
    
    # Create year-based summary
    year_summary = defaultdict(lambda: {
        'total_files': 0,
        'dnos_with_data': [],
        'file_types': defaultdict(int),
        'total_size_mb': 0
    })
    
    # Create DNO-based summary
    dno_summary = {}
    
    # All years across all DNOs
    all_years = set()
    
    for dist_id, dist_data in files_by_dist.items():
        dno_info = dist_data.get('dno_info', {})
        dno_key = dno_info.get('dno_key', f'ID-{dist_id}')
        years_data = dist_data.get('years', {})
        
        # Initialize DNO summary
        # Filter out 'unknown' years and convert to int
        valid_years = [int(y) for y in years_data.keys() if y.isdigit()]
        
        dno_summary[dist_id] = {
            'dno_key': dno_key,
            'name': dno_info.get('name', ''),
            'short_code': dno_info.get('short_code', ''),
            'total_files': dist_data.get('total_files', 0),
            'years': sorted(valid_years),
            'year_range': '',
            'file_types': defaultdict(int),
            'total_size_mb': 0
        }
        
        if dno_summary[dist_id]['years']:
            min_year = min(dno_summary[dist_id]['years'])
            max_year = max(dno_summary[dist_id]['years'])
            dno_summary[dist_id]['year_range'] = f"{min_year}-{max_year}"
            dno_summary[dist_id]['coverage_years'] = len(dno_summary[dist_id]['years'])
        
        # Analyze each year
        for year, year_data in years_data.items():
            # Skip 'unknown' years in the summary
            if not year.isdigit():
                continue
            
            # Handle both list of files and dict with 'files' key
            if isinstance(year_data, dict):
                year_files = year_data.get('files', [])
            else:
                year_files = year_data
                
            all_years.add(int(year))
            year_summary[year]['total_files'] += len(year_files)
            year_summary[year]['dnos_with_data'].append(dno_key)
            
            for file_info in year_files:
                # File type analysis
                filename = file_info.get('filename', '')
                size_bytes = file_info.get('size_bytes', 0)
                size_mb = size_bytes / (1024 * 1024) if size_bytes > 0 else 0
                
                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    file_type = 'Excel'
                elif filename.endswith('.pdf'):
                    file_type = 'PDF'
                elif filename.endswith('.csv'):
                    file_type = 'CSV'
                else:
                    file_type = 'Other'
                
                year_summary[year]['file_types'][file_type] += 1
                year_summary[year]['total_size_mb'] += size_mb
                
                dno_summary[dist_id]['file_types'][file_type] += 1
                dno_summary[dist_id]['total_size_mb'] += size_mb
    
    return year_summary, dno_summary, sorted(all_years)

def generate_markdown_report(data, year_summary, dno_summary, all_years):
    """Generate comprehensive markdown report"""
    
    report = []
    report.append("# DNO Charging Data Summary Report")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n**Project:** GB Power Market - DNO DUoS Charging Analysis")
    report.append("\n---\n")
    
    # Executive Summary
    summary = data.get('summary', {})
    report.append("## Executive Summary\n")
    report.append(f"- **Total Files Found:** {summary.get('total_files', 0)}")
    report.append(f"- **Unique Files:** {summary.get('unique_files', 0)}")
    report.append(f"- **Distribution IDs Found:** {summary.get('distribution_ids_found', 0)}/14")
    report.append(f"- **Year Coverage:** {min(all_years)}-{max(all_years)} ({len(all_years)} years)")
    report.append(f"- **Total Data Size:** {sum(d['total_size_mb'] for d in dno_summary.values()):.1f} MB\n")
    
    # GeoJSON Files Summary
    report.append("## GeoJSON Files Backup Summary\n")
    report.append("**Location:** `/Users/georgemajor/GB Power Market JJ/old_project/GIS_data/`\n")
    report.append("**Files Copied:** 19 GeoJSON files (~150 MB total)\n")
    report.append("\n### GeoJSON Inventory:\n")
    report.append("| File | Size | Description |")
    report.append("|------|------|-------------|")
    report.append("| GSP_regions_4326_20250109.geojson | 9.9M | GSP Regions (WGS84) - Latest |")
    report.append("| GSP_regions_4326_20250109_simplified.geojson | 9.2M | GSP Regions (WGS84) - Simplified |")
    report.append("| GSP_regions_4326_20250102.geojson | 9.7M | GSP Regions (WGS84) - Jan 2 |")
    report.append("| GSP_regions_4326_20250102_simplified.geojson | 9.1M | GSP Regions (WGS84) - Simplified |")
    report.append("| GSP_regions_27700_20250109.geojson | 10M | GSP Regions (British National Grid) |")
    report.append("| GSP_regions_27700_20250109_simplified.geojson | 9.5M | GSP Regions (BNG) - Simplified |")
    report.append("| GSP_regions_27700_20250102.geojson | 10M | GSP Regions (BNG) - Jan 2 |")
    report.append("| GSP_regions_27700_20250102_simplified.geojson | 9.4M | GSP Regions (BNG) - Simplified |")
    report.append("| gsp_regions_20220314.geojson | 13M | GSP Regions - March 2022 |")
    report.append("| gsp_regions_20220314_simplified.geojson | 11M | GSP Regions - 2022 Simplified |")
    report.append("| gsp_regions_20181031.geojson | 3.2M | GSP Regions - Oct 2018 |")
    report.append("| gsp_regions_20181031_simplified.geojson | 2.5M | GSP Regions - 2018 Simplified |")
    report.append("| gb-dno-license-areas-20240503-as-geojson.geojson | 2.9M | DNO License Areas - May 2024 |")
    report.append("| gb-dno-license-areas-20240503-as-geojson_simplified.geojson | 2.3M | DNO Areas - Simplified |")
    report.append("| dno_license_areas_20200506.geojson | 2.9M | DNO License Areas - May 2020 |")
    report.append("| dno_license_areas_20200506_simplified.geojson | 2.3M | DNO Areas - 2020 Simplified |")
    report.append("| merged_geojson.geojson | 29M | Merged/Combined Dataset |")
    report.append("| tnuosgenzones_geojs.geojson | 46K | TNUoS Generation Zones |")
    report.append("| tnuosgenzones_geojs_simplified.geojson | 43K | TNUoS Zones - Simplified |\n")
    
    report.append("**Key Features:**")
    report.append("- Multiple GSP region versions: 2018, 2022, and 2025 (Jan 2 & Jan 9)")
    report.append("- Both coordinate systems: WGS84 (EPSG:4326) and British National Grid (EPSG:27700)")
    report.append("- Simplified versions for faster rendering")
    report.append("- DNO boundary versions from 2020 and 2024")
    report.append("- TNUoS generation zones (new data source)")
    report.append("- Ready for BigQuery import with GEOGRAPHY type\n")
    
    # Summary by Year
    report.append("## Charging Data Summary by Year\n")
    report.append("| Year | Files | DNOs | Excel | PDF | CSV | Size (MB) |")
    report.append("|------|-------|------|-------|-----|-----|-----------|")
    
    for year in all_years:
        year_data = year_summary[str(year)]
        report.append(
            f"| {year} | {year_data['total_files']} | "
            f"{len(year_data['dnos_with_data'])} | "
            f"{year_data['file_types']['Excel']} | "
            f"{year_data['file_types']['PDF']} | "
            f"{year_data['file_types']['CSV']} | "
            f"{year_data['total_size_mb']:.1f} |"
        )
    
    # Totals row
    total_files = sum(year_summary[str(y)]['total_files'] for y in all_years)
    total_excel = sum(year_summary[str(y)]['file_types']['Excel'] for y in all_years)
    total_pdf = sum(year_summary[str(y)]['file_types']['PDF'] for y in all_years)
    total_csv = sum(year_summary[str(y)]['file_types']['CSV'] for y in all_years)
    total_size = sum(year_summary[str(y)]['total_size_mb'] for y in all_years)
    
    report.append(
        f"| **TOTAL** | **{total_files}** | **14** | "
        f"**{total_excel}** | **{total_pdf}** | **{total_csv}** | **{total_size:.1f}** |\n"
    )
    
    # Summary by DNO
    report.append("## Charging Data Summary by DNO (All 14 Distribution IDs)\n")
    report.append("| ID | DNO | Name | Files | Years | Coverage | Excel | PDF | CSV | Size (MB) |")
    report.append("|----|-----|------|-------|-------|----------|-------|-----|-----|-----------|")
    
    for dist_id in sorted(dno_summary.keys(), key=lambda x: int(x)):
        dno = dno_summary[dist_id]
        report.append(
            f"| {dist_id} | {dno['short_code']} | {dno['name'][:30]}... | "
            f"{dno['total_files']} | {dno['coverage_years']} | "
            f"{dno['year_range']} | "
            f"{dno['file_types']['Excel']} | "
            f"{dno['file_types']['PDF']} | "
            f"{dno['file_types']['CSV']} | "
            f"{dno['total_size_mb']:.1f} |"
        )
    
    report.append(
        f"\n**Total:** {sum(d['total_files'] for d in dno_summary.values())} files | "
        f"{sum(d['total_size_mb'] for d in dno_summary.values()):.1f} MB\n"
    )
    
    # Detailed DNO Analysis
    report.append("## Detailed Analysis by DNO\n")
    
    for dist_id in sorted(dno_summary.keys(), key=lambda x: int(x)):
        dno = dno_summary[dist_id]
        report.append(f"### Distribution ID {dist_id}: {dno['dno_key']} - {dno['name']}\n")
        report.append(f"**Short Code:** {dno['short_code']}  ")
        report.append(f"**Total Files:** {dno['total_files']}  ")
        report.append(f"**Year Coverage:** {dno['year_range']} ({dno['coverage_years']} years)  ")
        report.append(f"**Total Size:** {dno['total_size_mb']:.1f} MB\n")
        
        report.append("**File Types:**")
        if dno['file_types']['Excel'] > 0:
            report.append(f"- Excel: {dno['file_types']['Excel']} files")
        if dno['file_types']['PDF'] > 0:
            report.append(f"- PDF: {dno['file_types']['PDF']} files")
        if dno['file_types']['CSV'] > 0:
            report.append(f"- CSV: {dno['file_types']['CSV']} files")
        
        report.append(f"\n**Years with Data:** {', '.join(str(y) for y in dno['years'])}\n")
    
    # Coverage Matrix
    report.append("## Year Coverage Matrix\n")
    report.append("| DNO | " + " | ".join(str(y) for y in all_years) + " |")
    report.append("|-----|" + "|".join(["---"] * len(all_years)) + "|")
    
    files_by_dist = data.get('files_by_distribution_id', {})
    for dist_id in sorted(dno_summary.keys(), key=lambda x: int(x)):
        dno = dno_summary[dist_id]
        row = [dno['short_code']]
        
        years_data = files_by_dist[dist_id].get('years', {})
        for year in all_years:
            if str(year) in years_data:
                count = len(years_data[str(year)])
                row.append(f"✓ ({count})")
            else:
                row.append("—")
        
        report.append("| " + " | ".join(row) + " |")
    
    report.append("\n**Legend:** ✓ (n) = Data available (n files), — = No data\n")
    
    # Data Quality Assessment
    report.append("## Data Quality Assessment\n")
    report.append("### High Quality Coverage (10+ years)\n")
    report.append("| DNO | Years | Coverage | Assessment |")
    report.append("|-----|-------|----------|------------|")
    
    for dist_id in sorted(dno_summary.keys(), key=lambda x: int(x)):
        dno = dno_summary[dist_id]
        if dno['coverage_years'] >= 10:
            assessment = "Excellent" if dno['coverage_years'] >= 12 else "Very Good"
            report.append(
                f"| {dno['short_code']} | {dno['coverage_years']} | "
                f"{dno['year_range']} | {assessment} |"
            )
    
    report.append("\n### Moderate Coverage (5-9 years)\n")
    report.append("| DNO | Years | Coverage | Assessment |")
    report.append("|-----|-------|----------|------------|")
    
    for dist_id in sorted(dno_summary.keys(), key=lambda x: int(x)):
        dno = dno_summary[dist_id]
        if 5 <= dno['coverage_years'] < 10:
            report.append(
                f"| {dno['short_code']} | {dno['coverage_years']} | "
                f"{dno['year_range']} | Good |"
            )
    
    report.append("\n### Limited Coverage (< 5 years)\n")
    report.append("| DNO | Years | Coverage | Assessment |")
    report.append("|-----|-------|----------|------------|")
    
    for dist_id in sorted(dno_summary.keys(), key=lambda x: int(x)):
        dno = dno_summary[dist_id]
        if dno['coverage_years'] < 5:
            assessment = "Fair" if dno['coverage_years'] >= 3 else "Limited"
            report.append(
                f"| {dno['short_code']} | {dno['coverage_years']} | "
                f"{dno['year_range']} | {assessment} |"
            )
    
    # Next Steps
    report.append("\n## Next Steps\n")
    report.append("### 1. GeoJSON Import to BigQuery")
    report.append("- Import DNO boundaries (3 versions: 2020, 2024) to `dno_boundaries` table")
    report.append("- Import GSP regions (4 versions: 2018, 2022, 2025) to `gsp_boundaries` table")
    report.append("- Import TNUoS generation zones to `tnuos_zones` table")
    report.append("- Validate with ST_ISVALID and area calculations")
    report.append("- Enable spatial queries (point-in-polygon, distance, intersection)\n")
    
    report.append("### 2. Parse Charging Files")
    report.append("**Priority Order:**")
    report.append("1. **NGED areas (IDs 11, 14, 21, 22):** 67 files, 2014-2026 (13 years) - Most complete dataset")
    report.append("2. **UKPN areas (IDs 10, 12, 19):** 42 files, 2017-2026 (10 years) - London and South East")
    report.append("3. **SSEN areas (IDs 17, 20):** 76 files, 2017-2026 (10 years) - Scotland and Southern")
    report.append("4. **NPg areas (IDs 15, 23):** 48 files, 2023-2026 (4 years) - North East and Yorkshire")
    report.append("5. **SPEN areas (IDs 13, 18):** 42 files, 2020-2026 (7 years) - Scotland and Merseyside")
    report.append("6. **ENWL (ID 16):** 48 files, 2020-2026 (7 years) - North West\n")
    
    report.append("**Extract from Excel/PDF:**")
    report.append("- Tariff codes (LV/HV, domestic/commercial/industrial)")
    report.append("- Unit rates (p/kWh) by time band (day/night/peak/off-peak)")
    report.append("- Capacity charges (p/kVA/day)")
    report.append("- Fixed charges (p/day)")
    report.append("- Effective dates and change history")
    report.append("- Customer categories (UMS, domestic, non-domestic)")
    report.append("- Voltage levels (LV, HV, EHV, 132kV)\n")
    
    report.append("### 3. Load to BigQuery")
    report.append("- Table: `charging_tariffs` (partitioned by year, clustered by dno_key)")
    report.append("- Schema: year, dno_key, distribution_id, tariff_code, rate_type, time_band, unit_rate, capacity_charge, fixed_charge, voltage, category")
    report.append("- Enable time-series analysis and DNO comparison queries\n")
    
    report.append("### 4. Create Google Sheets Dashboard")
    report.append("- Master tariff lookup with year/DNO/voltage dropdowns")
    report.append("- Year-by-year comparison view")
    report.append("- Search by tariff code")
    report.append("- Annual cost calculator")
    report.append("- Connected to BigQuery for real-time data\n")
    
    report.append("---\n")
    report.append(f"\n**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n**Source Data:** `dno_files_by_distribution_id_and_year.json`")
    report.append(f"\n**GeoJSON Location:** `/Users/georgemajor/GB Power Market JJ/old_project/GIS_data/`")
    
    return "\n".join(report)

def main():
    """Main execution"""
    print("=" * 80)
    print("DNO CHARGING DATA SUMMARY GENERATOR")
    print("=" * 80)
    print()
    
    # Load data
    print("📂 Loading JSON data...")
    data = load_json_data()
    print(f"   ✅ Loaded {data['summary']['total_files']} files")
    
    # Analyze
    print("📊 Analyzing charging data by year and DNO...")
    year_summary, dno_summary, all_years = analyze_charging_data(data)
    print(f"   ✅ Analyzed {len(all_years)} years across 14 DNOs")
    
    # Generate report
    print("📝 Generating comprehensive markdown report...")
    report = generate_markdown_report(data, year_summary, dno_summary, all_years)
    
    # Save report
    output_path = Path("/Users/georgemajor/GB Power Market JJ/DNO_CHARGING_DATA_SUMMARY.md")
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"   ✅ Report saved: {output_path}")
    print(f"   📄 Size: {len(report):,} characters")
    print()
    print("=" * 80)
    print("SUMMARY COMPLETE!")
    print("=" * 80)
    print()
    print(f"Report location: {output_path}")
    print(f"GeoJSON files: /Users/georgemajor/GB Power Market JJ/old_project/GIS_data/")
    print()

if __name__ == "__main__":
    main()
