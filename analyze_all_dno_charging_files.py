#!/usr/bin/env python3
"""
Comprehensive DNO Charging Files Analysis
Scans both project folders and analyzes all charging documents
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import pandas as pd

# DNO patterns for file matching
DNO_PATTERNS = {
    "UKPN-LPN": ["london", "lpn", "lond", r"\bldn\b"],
    "UKPN-EPN": ["eastern", "epn", "eelc", "east england"],
    "UKPN-SPN": ["south eastern", "south-eastern", "spn", "seeb"],
    "ENWL": ["enwl", "electricity north west", "norw", r"\benw\b"],
    "NPg-NE": ["north east", "northeast", "neeb", "npg.*ne", "northern.*ne"],
    "NPg-Y": ["yorkshire", "yelg", "npg.*y", "york"],
    "SP-Distribution": ["spd", "spow", "south scotland", "sp distribution", "sp energy.*scotland"],
    "SP-Manweb": ["spm", "manw", "manweb", "sp energy.*manweb", "merseyside"],
    "SSE-SHEPD": ["shepd", "hyde", "hydro", "north scotland", "scottish hydro"],
    "SSE-SEPD": ["sepd", "sout", "southern electric", "sse.*southern"],
    "NGED-WM": ["wmid", "mide", "west midlands", r"\bwm\b", "nged.*west", "wpd.*west"],
    "NGED-EM": ["emid", "emeb", "east midlands", r"\bem\b", "nged.*east", "wpd.*east"],
    "NGED-SW": ["swest", "sweb", "south west", "southwest", r"\bsw\b", "nged.*sw", "wpd.*sw"],
    "NGED-SWales": ["swales", "swae", "south wales", "nged.*wales", "wpd.*wales"]
}

# Keywords for charging documents
CHARGING_KEYWORDS = [
    "duos", "duse", "use of system", "charging statement",
    "tariff", "schedule of charges", "connection charge",
    "lc14", "license condition 14", "ed2", "riio", "pcfm",
    "residential bands", "residual bands", "charging methodology"
]

# Search locations
SEARCH_FOLDERS = [
    "/Users/georgemajor/GB Power Market JJ",
    "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"
]


def extract_years(filename: str) -> list:
    """Extract years from filename"""
    years = []
    
    # 4-digit years
    years.extend(re.findall(r'20[12][0-9]', filename))
    
    # Year ranges like 2024-25 or 24-25
    for match in re.finditer(r'20(\d{2})[/-](\d{2})', filename):
        years.append(f"20{match.group(1)}")
        years.append(f"20{match.group(2)}")
        
    for match in re.finditer(r'(?<!\d)(\d{2})[/-](\d{2})(?!\d)', filename):
        yr1, yr2 = match.groups()
        if 10 <= int(yr1) <= 30:  # Assume 2010-2030
            years.append(f"20{yr1}")
        if 10 <= int(yr2) <= 30:
            years.append(f"20{yr2}")
    
    return sorted(list(set([int(y) for y in years if y])))


def categorize_by_dno(filename: str) -> str:
    """Identify DNO from filename"""
    filename_lower = filename.lower()
    
    for dno_key, patterns in DNO_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower):
                return dno_key
    
    return "UNKNOWN"


def is_charging_file(filename: str) -> bool:
    """Check if file is charging-related"""
    filename_lower = filename.lower()
    return any(keyword in filename_lower for keyword in CHARGING_KEYWORDS)


def scan_folder(folder_path: str) -> list:
    """Scan folder for charging files"""
    print(f"\n📂 Scanning: {folder_path}")
    
    if not os.path.exists(folder_path):
        print(f"  ⚠️  Folder does not exist")
        return []
    
    files = []
    file_extensions = {'.pdf', '.xlsx', '.xls', '.csv'}
    
    try:
        for root, dirs, filenames in os.walk(folder_path):
            # Skip hidden and system folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.venv', 'venv']]
            
            for filename in filenames:
                if Path(filename).suffix.lower() in file_extensions:
                    if is_charging_file(filename):
                        filepath = os.path.join(root, filename)
                        try:
                            stat = os.stat(filepath)
                            files.append({
                                'path': filepath,
                                'name': filename,
                                'size': stat.st_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'extension': Path(filename).suffix.lower()
                            })
                        except:
                            pass
    except Exception as e:
        print(f"  ⚠️  Error scanning: {e}")
    
    print(f"  Found {len(files)} charging files")
    return files


def analyze_files(all_files: list) -> dict:
    """Analyze and categorize all files"""
    print("\n🔍 Analyzing files...")
    
    analysis = {
        'total_files': len(all_files),
        'by_dno': defaultdict(list),
        'by_year': defaultdict(list),
        'by_extension': defaultdict(int),
        'coverage': {},
        'recent_files': []  # Last 3 years
    }
    
    current_year = 2025
    
    for file_info in all_files:
        filename = file_info['name']
        
        # DNO categorization
        dno = categorize_by_dno(filename)
        analysis['by_dno'][dno].append(file_info)
        
        # Year extraction
        years = extract_years(filename)
        for year in years:
            analysis['by_year'][year].append(file_info)
            
            # Track recent files (last 3 years)
            if year >= current_year - 3:
                analysis['recent_files'].append({
                    'file': filename,
                    'dno': dno,
                    'year': year
                })
        
        # File type
        analysis['by_extension'][file_info['extension']] += 1
    
    # Calculate coverage (DNOs with data for last 3 years)
    for dno_key in DNO_PATTERNS.keys():
        dno_files = analysis['by_dno'][dno_key]
        if not dno_files:
            analysis['coverage'][dno_key] = {
                'has_data': False,
                'years': [],
                'file_count': 0,
                'recent_years': []
            }
            continue
        
        years_covered = set()
        for f in dno_files:
            years_covered.update(extract_years(f['name']))
        
        recent_years = [y for y in years_covered if y >= current_year - 3]
        
        analysis['coverage'][dno_key] = {
            'has_data': True,
            'years': sorted(years_covered),
            'file_count': len(dno_files),
            'recent_years': sorted(recent_years),
            'has_last_3_years': len(recent_years) >= 3
        }
    
    return analysis


def generate_report(analysis: dict) -> str:
    """Generate markdown report"""
    lines = [
        "# DNO Charging Files - Complete Analysis",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n**Total Files Found:** {analysis['total_files']}",
        "\n---\n"
    ]
    
    # Summary by DNO
    lines.append("\n## Coverage by DNO License Area\n")
    lines.append("| DNO | Files | Years Covered | Last 3 Years | Status |")
    lines.append("|-----|-------|---------------|--------------|--------|")
    
    for dno_key in sorted(DNO_PATTERNS.keys()):
        cov = analysis['coverage'][dno_key]
        
        if not cov['has_data']:
            lines.append(f"| {dno_key} | 0 | - | ❌ No data | ❌ Missing |")
            continue
        
        year_range = f"{min(cov['years'])}-{max(cov['years'])}" if cov['years'] else "Unknown"
        recent = ", ".join(map(str, cov['recent_years'])) if cov['recent_years'] else "None"
        status = "✅ Complete" if cov['has_last_3_years'] else "⚠️ Incomplete"
        
        lines.append(f"| {dno_key} | {cov['file_count']} | {year_range} | {recent} | {status} |")
    
    # File types
    lines.append("\n\n## File Types\n")
    for ext, count in sorted(analysis['by_extension'].items()):
        lines.append(f"- **{ext}**: {count} files")
    
    # Recent files (last 3 years)
    lines.append("\n\n## Recent Files (2023-2025)\n")
    
    recent_by_dno = defaultdict(list)
    for item in analysis['recent_files']:
        recent_by_dno[item['dno']].append(item)
    
    for dno_key in sorted(recent_by_dno.keys()):
        items = recent_by_dno[dno_key]
        lines.append(f"\n### {dno_key} ({len(items)} files)\n")
        
        # Group by year
        by_year = defaultdict(list)
        for item in items:
            by_year[item['year']].append(item['file'])
        
        for year in sorted(by_year.keys(), reverse=True):
            files = by_year[year]
            lines.append(f"\n**{year}:**")
            for f in sorted(files):
                lines.append(f"- {f}")
    
    # Year coverage matrix
    lines.append("\n\n## Year Coverage Matrix\n")
    lines.append("| DNO | 2023 | 2024 | 2025 | Total Years |")
    lines.append("|-----|------|------|------|-------------|")
    
    for dno_key in sorted(DNO_PATTERNS.keys()):
        cov = analysis['coverage'][dno_key]
        
        has_2023 = "✅" if 2023 in cov['years'] else "❌"
        has_2024 = "✅" if 2024 in cov['years'] else "❌"
        has_2025 = "✅" if 2025 in cov['years'] else "❌"
        total = len(cov['years'])
        
        lines.append(f"| {dno_key} | {has_2023} | {has_2024} | {has_2025} | {total} |")
    
    # Detailed file list by DNO
    lines.append("\n\n## Detailed File Inventory\n")
    
    for dno_key in sorted(analysis['by_dno'].keys()):
        files = analysis['by_dno'][dno_key]
        if not files:
            continue
            
        lines.append(f"\n### {dno_key} ({len(files)} files)\n")
        
        for f in sorted(files, key=lambda x: x['name']):
            size_mb = f['size'] / (1024 * 1024)
            years = extract_years(f['name'])
            year_str = ", ".join(map(str, years)) if years else "Unknown"
            lines.append(f"- **{f['name']}** ({f['extension']}, {size_mb:.2f} MB, Years: {year_str})")
    
    return "\n".join(lines)


def main():
    """Main execution"""
    print("="*70)
    print("DNO CHARGING FILES - COMPREHENSIVE ANALYSIS")
    print("="*70)
    
    # Scan both folders
    all_files = []
    for folder in SEARCH_FOLDERS:
        files = scan_folder(folder)
        all_files.extend(files)
    
    print(f"\n✅ Total charging files found: {len(all_files)}")
    
    if not all_files:
        print("\n❌ No charging files found in any location")
        return
    
    # Analyze
    analysis = analyze_files(all_files)
    
    # Generate report
    report = generate_report(analysis)
    
    # Save reports
    report_file = Path("DNO_CHARGING_FILES_COMPLETE_ANALYSIS.md")
    report_file.write_text(report)
    print(f"\n✅ Report saved: {report_file}")
    
    # Save JSON
    json_file = Path("dno_charging_files_analysis.json")
    with open(json_file, 'w') as f:
        json.dump({
            'total_files': analysis['total_files'],
            'by_extension': dict(analysis['by_extension']),
            'coverage': analysis['coverage'],
            'scan_date': datetime.now().isoformat()
        }, f, indent=2, default=str)
    print(f"✅ JSON data saved: {json_file}")
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    complete_count = sum(1 for cov in analysis['coverage'].values() if cov.get('has_last_3_years'))
    print(f"DNOs with complete data (last 3 years): {complete_count}/14")
    
    print("\nBy DNO:")
    for dno_key in sorted(DNO_PATTERNS.keys()):
        cov = analysis['coverage'][dno_key]
        if cov['has_data']:
            status = "✅" if cov['has_last_3_years'] else "⚠️"
            print(f"  {status} {dno_key:20s}: {cov['file_count']:3d} files ({len(cov['years'])} years)")
        else:
            print(f"  ❌ {dno_key:20s}: No data")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
