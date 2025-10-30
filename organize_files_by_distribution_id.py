"""
DNO Charging Files - Distribution ID and Year Organization
Generates JSON file mapping all charging files by Distribution ID and Year

Usage:
    python organize_files_by_distribution_id.py

Output:
    dno_files_by_distribution_id_and_year.json
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# DNO mapping with Distribution IDs (MPAN first 2 digits)
DNO_MAPPING = {
    10: {
        "dno_key": "UKPN-EPN",
        "name": "UK Power Networks (Eastern)",
        "short_code": "EPN",
        "market_participant_id": "EELC",
        "gsp_group_id": "A",
        "gsp_group_name": "Eastern"
    },
    11: {
        "dno_key": "NGED-EM",
        "name": "National Grid Electricity Distribution – East Midlands",
        "short_code": "EMID",
        "market_participant_id": "EMEB",
        "gsp_group_id": "B",
        "gsp_group_name": "East Midlands"
    },
    12: {
        "dno_key": "UKPN-LPN",
        "name": "UK Power Networks (London)",
        "short_code": "LPN",
        "market_participant_id": "LOND",
        "gsp_group_id": "C",
        "gsp_group_name": "London"
    },
    13: {
        "dno_key": "SP-Manweb",
        "name": "SP Energy Networks (SPM)",
        "short_code": "SPM",
        "market_participant_id": "MANW",
        "gsp_group_id": "D",
        "gsp_group_name": "Merseyside & North Wales"
    },
    14: {
        "dno_key": "NGED-WM",
        "name": "National Grid Electricity Distribution – West Midlands",
        "short_code": "WMID",
        "market_participant_id": "MIDE",
        "gsp_group_id": "E",
        "gsp_group_name": "West Midlands"
    },
    15: {
        "dno_key": "NPg-NE",
        "name": "Northern Powergrid (North East)",
        "short_code": "NE",
        "market_participant_id": "NEEB",
        "gsp_group_id": "F",
        "gsp_group_name": "North East"
    },
    16: {
        "dno_key": "ENWL",
        "name": "Electricity North West",
        "short_code": "ENWL",
        "market_participant_id": "NORW",
        "gsp_group_id": "G",
        "gsp_group_name": "North West"
    },
    17: {
        "dno_key": "SSE-SHEPD",
        "name": "Scottish Hydro Electric Power Distribution",
        "short_code": "SHEPD",
        "market_participant_id": "HYDE",
        "gsp_group_id": "P",
        "gsp_group_name": "North Scotland"
    },
    18: {
        "dno_key": "SP-Distribution",
        "name": "SP Energy Networks (SPD)",
        "short_code": "SPD",
        "market_participant_id": "SPOW",
        "gsp_group_id": "N",
        "gsp_group_name": "South Scotland"
    },
    19: {
        "dno_key": "UKPN-SPN",
        "name": "UK Power Networks (South Eastern)",
        "short_code": "SPN",
        "market_participant_id": "SEEB",
        "gsp_group_id": "J",
        "gsp_group_name": "South Eastern"
    },
    20: {
        "dno_key": "SSE-SEPD",
        "name": "Southern Electric Power Distribution",
        "short_code": "SEPD",
        "market_participant_id": "SOUT",
        "gsp_group_id": "H",
        "gsp_group_name": "Southern"
    },
    21: {
        "dno_key": "NGED-SWales",
        "name": "National Grid Electricity Distribution – South Wales",
        "short_code": "SWALES",
        "market_participant_id": "SWAE",
        "gsp_group_id": "K",
        "gsp_group_name": "South Wales"
    },
    22: {
        "dno_key": "NGED-SW",
        "name": "National Grid Electricity Distribution – South West",
        "short_code": "SWEST",
        "market_participant_id": "SWEB",
        "gsp_group_id": "L",
        "gsp_group_name": "South Western"
    },
    23: {
        "dno_key": "NPg-Y",
        "name": "Northern Powergrid (Yorkshire)",
        "short_code": "Y",
        "market_participant_id": "YELG",
        "gsp_group_id": "M",
        "gsp_group_name": "Yorkshire"
    }
}

# Search patterns for each Distribution ID
SEARCH_PATTERNS = {
    10: ["eastern", "eastern power", "epn", "eelc"],
    11: ["east midlands", "east-midlands", "emid", "emeb"],
    12: ["london", "london power", "lpn", "lond"],
    13: ["manweb", "sp manweb", "spm", "manw"],
    14: ["west midlands", "west-midlands", "wmid", "mide"],
    15: ["northeast", "north-east", "north east", "northern powergrid ne", "northern powergrid (northeast)", "neeb"],  # Fixed: added "northeast" (one word)
    16: ["north west", "north-west", "enwl", "norw"],
    17: ["shepd", "scottish hydro", "hyde", "north scotland"],
    18: ["spd", "sp distribution", "spow", "south scotland"],
    19: ["south-eastern-power-networks", "south eastern power", "southeastern", "spn", "seeb"],  # Fixed: added full pattern
    20: ["sepd", "southern electric", "sout"],
    21: ["south wales", "south-wales", "swales", "swae"],
    22: ["south west", "south-west", "swest", "sweb"],
    23: ["yorkshire", "yelg", "northern powergrid (yorkshire)", "northern powergrid y"],
}

# Project folders to scan
FOLDERS = [
    "/Users/georgemajor/GB Power Market JJ",
    "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"
]

# File extensions to include
EXTENSIONS = [".pdf", ".xlsx", ".xls", ".csv"]

# Directories to exclude
EXCLUDE_DIRS = [
    '__pycache__', 'node_modules', '.venv', 'venv', 
    'environment', 'gsheets_env', '.git'
]


def extract_year_from_filename(filename):
    """Extract 4-digit year from filename (2010-2030 range)"""
    year_match = re.search(r'(20[1-3][0-9])', filename)
    return year_match.group(1) if year_match else None


def match_distribution_id(filename):
    """Determine which Distribution ID a file belongs to
    
    Priority matching to avoid conflicts:
    1. Check for specific patterns first (e.g., "south-eastern" before "eastern")
    2. Handle NPg areas carefully (Yorkshire vs North East)
    """
    filename_lower = filename.lower()
    
    # Priority 1: Check UKPN-SPN first (before EPN which contains "eastern")
    if "south-eastern-power-networks" in filename_lower or "south eastern power networks" in filename_lower:
        return 19
    
    # Priority 2: Check NPg Yorkshire (before North East patterns)
    if "yorkshire" in filename_lower or "yelg" in filename_lower:
        return 23
    
    # Priority 3: Check NPg North East (excluding Yorkshire)
    if any(pattern in filename_lower for pattern in SEARCH_PATTERNS[15]):
        if "yorkshire" not in filename_lower:
            return 15
    
    # Priority 4: Check all other patterns in order
    for dist_id, patterns in SEARCH_PATTERNS.items():
        if dist_id in [15, 19, 23]:  # Skip already handled: NPg-NE, UKPN-SPN, NPg-Y
            continue
        if any(pattern in filename_lower for pattern in patterns):
            return dist_id
    
    return None


def scan_folders():
    """Scan project folders and organize files by Distribution ID and Year"""
    files_by_id_year = defaultdict(lambda: defaultdict(list))
    file_paths = {}  # Store full paths for each file
    
    for folder in FOLDERS:
        if not os.path.exists(folder):
            print(f"⚠️  Folder not found: {folder}")
            continue
        
        print(f"📂 Scanning: {folder}")
        
        for root, dirs, files in os.walk(folder):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in EXCLUDE_DIRS]
            
            for filename in files:
                # Check file extension
                if Path(filename).suffix.lower() not in EXTENSIONS:
                    continue
                
                # Match to Distribution ID
                dist_id = match_distribution_id(filename)
                if dist_id is None:
                    continue
                
                # Extract year
                year = extract_year_from_filename(filename) or "unknown"
                
                # Store file info
                files_by_id_year[dist_id][year].append(filename)
                
                # Store full path (first occurrence)
                if filename not in file_paths:
                    file_paths[filename] = os.path.join(root, filename)
    
    return files_by_id_year, file_paths


def generate_summary(files_by_id_year):
    """Generate summary statistics"""
    total_files = 0
    total_unique_files = set()
    
    for dist_id in files_by_id_year:
        for year in files_by_id_year[dist_id]:
            file_list = files_by_id_year[dist_id][year]
            total_files += len(file_list)
            total_unique_files.update(file_list)
    
    return {
        "total_files": total_files,
        "unique_files": len(total_unique_files),
        "distribution_ids_found": len(files_by_id_year),
        "distribution_ids_missing": [
            dist_id for dist_id in DNO_MAPPING.keys() 
            if dist_id not in files_by_id_year
        ]
    }


def build_output_structure(files_by_id_year, file_paths):
    """Build comprehensive JSON output structure"""
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "description": "DNO charging files organized by Distribution ID and Year",
            "project": "GB Power Market - DNO DUoS Charging Analysis",
            "folders_scanned": FOLDERS
        },
        "dno_mapping": DNO_MAPPING,
        "files_by_distribution_id": {}
    }
    
    for dist_id in sorted(files_by_id_year.keys()):
        dno_info = DNO_MAPPING[dist_id]
        years_data = {}
        
        for year in sorted(files_by_id_year[dist_id].keys(), 
                          key=lambda x: (x == "unknown", x)):
            # Remove duplicates and sort
            file_list = sorted(set(files_by_id_year[dist_id][year]))
            
            years_data[year] = {
                "count": len(file_list),
                "files": [
                    {
                        "filename": fname,
                        "path": file_paths.get(fname, ""),
                        "extension": Path(fname).suffix.lower(),
                        "size_bytes": os.path.getsize(file_paths[fname]) 
                                     if fname in file_paths and os.path.exists(file_paths[fname]) 
                                     else None
                    }
                    for fname in file_list
                ]
            }
        
        output["files_by_distribution_id"][str(dist_id)] = {
            "dno_info": dno_info,
            "years": years_data,
            "total_files": sum(y["count"] for y in years_data.values())
        }
    
    return output


def main():
    """Main execution function"""
    print("=" * 80)
    print("DNO CHARGING FILES - DISTRIBUTION ID AND YEAR ORGANIZATION")
    print("=" * 80)
    print()
    
    # Scan folders
    files_by_id_year, file_paths = scan_folders()
    
    # Generate summary
    summary = generate_summary(files_by_id_year)
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files found: {summary['total_files']}")
    print(f"Unique files: {summary['unique_files']}")
    print(f"Distribution IDs found: {summary['distribution_ids_found']}/14")
    
    if summary['distribution_ids_missing']:
        print(f"\n⚠️  Missing Distribution IDs: {summary['distribution_ids_missing']}")
        for dist_id in summary['distribution_ids_missing']:
            dno = DNO_MAPPING[dist_id]
            print(f"   - {dist_id}: {dno['short_code']} ({dno['name']})")
    
    print()
    
    # Build output structure
    output = build_output_structure(files_by_id_year, file_paths)
    output["summary"] = summary
    
    # Write JSON file
    output_file = "dno_files_by_distribution_id_and_year.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated: {output_file}")
    print(f"   Size: {os.path.getsize(output_file):,} bytes")
    print()
    
    # Print Distribution ID summary
    print("=" * 80)
    print("FILES BY DISTRIBUTION ID")
    print("=" * 80)
    for dist_id in sorted(files_by_id_year.keys()):
        dno = DNO_MAPPING[dist_id]
        total = output["files_by_distribution_id"][str(dist_id)]["total_files"]
        print(f"{dist_id:2d} | {dno['short_code']:6s} | {dno['gsp_group_id']} | {total:3d} files | {dno['name']}")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
