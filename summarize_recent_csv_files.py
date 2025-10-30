#!/usr/bin/env python3
"""
CSV Files Summary Generator
--------------------------
Summarizes all CSV files modified in the last 3 days in a machine-readable format.
Provides key metrics like file size, row count, column names, and data sample.
"""

import csv
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd


def get_recent_csv_files(base_dir: str, days: int = 3) -> List[str]:
    """
    Find all CSV files modified in the last specified number of days.
    
    Args:
        base_dir: Base directory to search in
        days: Number of days to look back
        
    Returns:
        List of paths to CSV files
    """
    csv_files = []
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
    cutoff_timestamp = cutoff_time.timestamp()
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith('.csv'):
                file_path = os.path.join(root, file)
                mod_time = os.path.getmtime(file_path)
                if mod_time >= cutoff_timestamp:
                    csv_files.append(file_path)
    
    return csv_files


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get basic file information.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file metadata
    """
    stat = os.stat(file_path)
    return {
        "path": file_path,
        "name": os.path.basename(file_path),
        "directory": os.path.dirname(file_path),
        "size_bytes": stat.st_size,
        "size_human": f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024 * 1024 else f"{stat.st_size / (1024 * 1024):.1f} MB",
        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
    }


def analyze_csv_structure(file_path: str, max_rows: int = 5) -> Dict[str, Any]:
    """
    Analyze CSV file structure and content.
    
    Args:
        file_path: Path to the CSV file
        max_rows: Maximum number of rows to analyze
        
    Returns:
        Dictionary with CSV structure information
    """
    try:
        # Try to use pandas for fast analysis
        df = pd.read_csv(file_path, nrows=max_rows)
        
        # Get basic stats
        result = {
            "columns": df.columns.tolist(),
            "column_count": len(df.columns),
            "row_sample_count": len(df),
            "data_types": {col: str(df[col].dtype) for col in df.columns},
            "sample_rows": df.head(max_rows).to_dict(orient="records"),
            "has_header": True,  # Pandas assumes this
        }
        
        # Count total rows
        try:
            total_rows = sum(1 for _ in open(file_path, 'r')) - 1  # -1 for header
            result["total_rows"] = total_rows
        except Exception:
            result["total_rows"] = "unknown"
        
        return result
    
    except Exception as e:
        # Fallback to basic CSV parsing
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = []
                for i, row in enumerate(reader):
                    if i >= max_rows + 1:  # +1 for header
                        break
                    rows.append(row)
            
            if not rows:
                return {"error": "Empty file or parsing error"}
            
            headers = rows[0]
            data_rows = rows[1:] if len(rows) > 1 else []
            
            # Count total rows
            try:
                total_rows = sum(1 for _ in open(file_path, 'r')) - 1  # -1 for header
            except Exception:
                total_rows = "unknown"
            
            return {
                "columns": headers,
                "column_count": len(headers),
                "row_sample_count": len(data_rows),
                "total_rows": total_rows,
                "sample_rows": data_rows,
                "has_header": True,  # Assuming first row is header
                "error": f"Pandas error: {str(e)}, using basic CSV parser"
            }
        
        except Exception as e2:
            return {"error": f"Failed to parse CSV: {str(e)}, {str(e2)}"}


def summarize_csv_files(base_dir: str, days: int = 3, output_format: str = "json") -> str:
    """
    Generate a summary of all CSV files modified in the last specified days.
    
    Args:
        base_dir: Base directory to search in
        days: Number of days to look back
        output_format: Output format (json or csv)
        
    Returns:
        Summary string in the specified format
    """
    print(f"Finding CSV files modified in the last {days} days in {base_dir}...")
    
    # Get list of recent CSV files
    csv_files = get_recent_csv_files(base_dir, days)
    
    if not csv_files:
        return json.dumps({"error": f"No CSV files found modified in the last {days} days"})
    
    print(f"Found {len(csv_files)} CSV files. Analyzing...")
    
    # Analyze each CSV file
    results = []
    for i, file_path in enumerate(csv_files):
        print(f"  [{i+1}/{len(csv_files)}] Analyzing {os.path.basename(file_path)}...")
        file_info = get_file_info(file_path)
        try:
            csv_structure = analyze_csv_structure(file_path)
            file_info.update(csv_structure)
        except Exception as e:
            file_info["error"] = f"Analysis error: {str(e)}"
        
        results.append(file_info)
    
    # Group by directory
    grouped_results = {}
    for result in results:
        directory = result["directory"]
        if directory not in grouped_results:
            grouped_results[directory] = []
        grouped_results[directory].append(result)
    
    # Sort directories by count
    sorted_dirs = sorted(grouped_results.keys(), 
                         key=lambda x: len(grouped_results[x]), 
                         reverse=True)
    
    # Create final summary
    summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "base_directory": base_dir,
        "days_looked_back": days,
        "total_csv_files": len(csv_files),
        "directories": {
            dir_path: {
                "file_count": len(grouped_results[dir_path]),
                "files": grouped_results[dir_path]
            }
            for dir_path in sorted_dirs
        }
    }
    
    if output_format == "json":
        return json.dumps(summary, indent=2)
    else:
        # Return error for now, CSV output format could be implemented if needed
        return json.dumps({"error": "Only JSON output format is supported currently"})


def main():
    """Main function."""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Summarize CSV files modified in the last N days')
    parser.add_argument('--dir', '-d', default=os.getcwd(), 
                        help='Base directory to search (default: current directory)')
    parser.add_argument('--days', '-n', type=int, default=3,
                        help='Number of days to look back (default: 3)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output file (default: stdout)')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json',
                        help='Output format (default: json)')
    
    args = parser.parse_args()
    
    # Generate summary
    summary = summarize_csv_files(args.dir, args.days, args.format)
    
    # Output summary
    if args.output:
        with open(args.output, 'w') as f:
            f.write(summary)
        print(f"Summary written to {args.output}")
    else:
        print(summary)


if __name__ == '__main__':
    main()
