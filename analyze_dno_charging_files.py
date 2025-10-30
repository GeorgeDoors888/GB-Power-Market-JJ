#!/usr/bin/env python3
"""
Analyze DNO Charging Files in Google Drive
Extract charging data from PDFs and Excel files for all 14 license areas

This script:
1. Lists all charging-related files in Google Drive backup
2. Categorizes by DNO license area
3. Extracts tariff data from Excel files
4. Prepares data for Google Sheets and BigQuery
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# DNO patterns for file matching
DNO_PATTERNS = {
    "UKPN-LPN": ["london", "lpn", "lond"],
    "UKPN-EPN": ["eastern", "epn", "eelc"],
    "UKPN-SPN": ["south eastern", "south-eastern", "spn", "seeb"],
    "ENWL": ["enwl", "electricity north west", "norw", "north west"],
    "NPg-NE": ["north east", "northeast", "neeb", "npg-ne", "northern powergrid.*north east"],
    "NPg-Y": ["yorkshire", "yelg", "npg-y", "northern powergrid.*yorkshire"],
    "SP-Distribution": ["spd", "spow", "south scotland", "sp distribution", "sp energy.*scotland"],
    "SP-Manweb": ["spm", "manw", "manweb", "sp energy.*manweb", "merseyside"],
    "SSE-SHEPD": ["shepd", "hyde", "hydro", "north scotland", "scottish hydro"],
    "SSE-SEPD": ["sepd", "sout", "southern electric", "sse.*southern"],
    "NGED-WM": ["wmid", "mide", "west midlands", "nged.*west", "wpd.*west"],
    "NGED-EM": ["emid", "emeb", "east midlands", "nged.*east", "wpd.*east"],
    "NGED-SW": ["swest", "sweb", "south west", "southwest", "nged.*sw", "wpd.*sw"],
    "NGED-SWales": ["swales", "swae", "south wales", "nged.*wales", "wpd.*wales"]
}

# Keywords for charging documents
CHARGING_KEYWORDS = [
    "duos", "duse", "use of system", "charging statement",
    "tariff", "schedule of charges", "connection charge",
    "lc14", "license condition 14", "ed2", "riio", "pcfm",
    "residential bands", "residual bands"
]


class DNOChargingAnalyzer:
    """Analyze DNO charging files from Google Drive"""
    
    def __init__(self, credentials_file: str = "jibber_jabber_key.json"):
        self.credentials_file = credentials_file
        self.drive_service = None
        self.backup_folder_id = "1DLuQIjPt-egchPpXtlZqsrW5LNG0FkIP"  # GB Power Market JJ Backup
        self.file_catalog = {dno: [] for dno in DNO_PATTERNS.keys()}
        
    def authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self.drive_service = build('drive', 'v3', credentials=credentials)
            print("✅ Authenticated with Google Drive API")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
            
    def list_charging_files(self) -> List[Dict]:
        """List all charging-related files in Google Drive backup"""
        print("\n📂 Scanning Google Drive for charging documents...")
        
        all_files = []
        page_token = None
        
        try:
            while True:
                query = f"'{self.backup_folder_id}' in parents and trashed=false"
                results = self.drive_service.files().list(
                    q=query,
                    pageSize=1000,
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)",
                    pageToken=page_token
                ).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            print(f"  Found {len(all_files)} total files in backup")
            
            # Filter for charging-related files
            charging_files = []
            for file in all_files:
                filename = file['name'].lower()
                
                # Check if file is PDF or Excel
                if not (filename.endswith('.pdf') or filename.endswith(('.xlsx', '.xls', '.csv'))):
                    continue
                    
                # Check if filename contains charging keywords
                if any(keyword in filename for keyword in CHARGING_KEYWORDS):
                    charging_files.append(file)
                    
            print(f"  Found {len(charging_files)} charging-related documents")
            return charging_files
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
            
    def categorize_by_dno(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize files by DNO license area"""
        print("\n🏷️  Categorizing files by DNO license area...")
        
        categorized = {dno: [] for dno in DNO_PATTERNS.keys()}
        uncategorized = []
        
        for file in files:
            filename = file['name'].lower()
            matched = False
            
            # Try to match with DNO patterns
            for dno_key, patterns in DNO_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, filename):
                        categorized[dno_key].append(file)
                        matched = True
                        break
                if matched:
                    break
                    
            if not matched:
                uncategorized.append(file)
                
        # Print summary
        for dno_key, dno_files in categorized.items():
            if len(dno_files) > 0:
                print(f"  {dno_key}: {len(dno_files)} files")
                
        if uncategorized:
            print(f"  Uncategorized: {len(uncategorized)} files")
            
        self.file_catalog = categorized
        return categorized
        
    def extract_year_from_filename(self, filename: str) -> List[int]:
        """Extract years from filename"""
        # Look for 4-digit years (2010-2030)
        years = re.findall(r'20[12][0-9]', filename)
        
        # Also look for year ranges like "2024-25" or "24-25"
        year_ranges = re.findall(r'20(\d{2})[/-](\d{2})', filename)
        for yr1, yr2 in year_ranges:
            years.extend([f"20{yr1}", f"20{yr2}"])
            
        # Convert to integers and remove duplicates
        return sorted(list(set([int(y) for y in years])))
        
    def generate_file_catalog_report(self, categorized: Dict[str, List[Dict]]) -> str:
        """Generate markdown report of all charging files"""
        report_lines = [
            "# DNO Charging Documents Catalog",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n**Total Files:** {sum(len(files) for files in categorized.values())}",
            "\n---\n"
        ]
        
        for dno_key in sorted(categorized.keys()):
            files = categorized[dno_key]
            if not files:
                continue
                
            report_lines.append(f"\n## {dno_key}")
            report_lines.append(f"\n**Document Count:** {len(files)}\n")
            
            # Group by year
            files_by_year = {}
            for file in files:
                years = self.extract_year_from_filename(file['name'])
                if not years:
                    years = [0]  # Unknown year
                    
                for year in years:
                    if year not in files_by_year:
                        files_by_year[year] = []
                    files_by_year[year].append(file)
                    
            # Print by year
            for year in sorted(files_by_year.keys(), reverse=True):
                if year == 0:
                    report_lines.append("\n### Unknown Year\n")
                else:
                    report_lines.append(f"\n### Year {year}\n")
                    
                for file in sorted(files_by_year[year], key=lambda x: x['name']):
                    size_mb = int(file.get('size', 0)) / (1024 * 1024)
                    file_type = "PDF" if file['name'].endswith('.pdf') else "Excel"
                    
                    report_lines.append(
                        f"- **{file['name']}** ({file_type}, {size_mb:.2f} MB)"
                    )
                    report_lines.append(f"  - File ID: `{file['id']}`")
                    report_lines.append(f"  - Link: https://drive.google.com/file/d/{file['id']}/view")
                    
            report_lines.append("\n---\n")
            
        return "\n".join(report_lines)
        
    def generate_summary_json(self, categorized: Dict[str, List[Dict]]) -> Dict:
        """Generate JSON summary for programmatic access"""
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_files": sum(len(files) for files in categorized.values()),
            "dnos": {}
        }
        
        for dno_key, files in categorized.items():
            if not files:
                continue
                
            # Extract years
            all_years = set()
            for file in files:
                years = self.extract_year_from_filename(file['name'])
                all_years.update(years)
                
            summary["dnos"][dno_key] = {
                "file_count": len(files),
                "years_covered": sorted([y for y in all_years if y > 0]),
                "year_range": {
                    "min": min([y for y in all_years if y > 0], default=None),
                    "max": max([y for y in all_years if y > 0], default=None)
                },
                "file_types": {
                    "pdf": sum(1 for f in files if f['name'].endswith('.pdf')),
                    "excel": sum(1 for f in files if f['name'].endswith(('.xlsx', '.xls')))
                },
                "files": [
                    {
                        "id": f['id'],
                        "name": f['name'],
                        "size": f.get('size', 0),
                        "years": self.extract_year_from_filename(f['name']),
                        "type": "pdf" if f['name'].endswith('.pdf') else "excel"
                    }
                    for f in files
                ]
            }
            
        return summary
        

def main():
    """Main execution"""
    analyzer = DNOChargingAnalyzer()
    
    # Authenticate
    if not analyzer.authenticate():
        return
        
    # List charging files
    files = analyzer.list_charging_files()
    
    if not files:
        print("❌ No charging files found")
        return
        
    # Categorize by DNO
    categorized = analyzer.categorize_by_dno(files)
    
    # Generate reports
    print("\n📝 Generating reports...")
    
    # Markdown report
    report_md = analyzer.generate_file_catalog_report(categorized)
    report_file = Path("DNO_CHARGING_FILES_CATALOG.md")
    report_file.write_text(report_md)
    print(f"  ✅ Markdown report: {report_file}")
    
    # JSON summary
    summary_json = analyzer.generate_summary_json(categorized)
    summary_file = Path("dno_charging_files_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary_json, f, indent=2)
    print(f"  ✅ JSON summary: {summary_file}")
    
    # Print quick summary
    print("\n" + "="*70)
    print("CHARGING FILES SUMMARY")
    print("="*70)
    for dno_key in sorted(categorized.keys()):
        files = categorized[dno_key]
        if files:
            years = set()
            for f in files:
                years.update(analyzer.extract_year_from_filename(f['name']))
            years = [y for y in years if y > 0]
            
            if years:
                year_range = f"{min(years)}-{max(years)}"
            else:
                year_range = "Unknown"
                
            print(f"{dno_key:20s}: {len(files):3d} files ({year_range})")
            
    print("="*70)
    

if __name__ == "__main__":
    main()
