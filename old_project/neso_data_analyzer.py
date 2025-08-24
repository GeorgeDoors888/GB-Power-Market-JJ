#!/usr/bin/env python3
"""
NESO Data Quality Analyzer
=========================
Analyzes the current NESO datasets for quality, coverage, and insights.
"""

import json
import csv
from google.cloud import storage
from datetime import datetime
import pandas as pd
from io import StringIO
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NESODataAnalyzer:
    def __init__(self, bucket_name="jibber-jabber-knowledge-bmrs-data"):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        
        self.analysis_results = {
            'dataset_count': 0,
            'total_files': 0,
            'total_size_mb': 0,
            'datasets_by_category': {},
            'file_formats': {},
            'data_coverage': {},
            'sample_data': {},
            'recommendations': []
        }
    
    def analyze_current_datasets(self):
        """Analyze all currently available NESO datasets"""
        logger.info("🔍 Starting comprehensive NESO data analysis...")
        
        # Get list of datasets
        datasets = self.get_dataset_list()
        logger.info(f"📊 Found {len(datasets)} datasets to analyze")
        
        self.analysis_results['dataset_count'] = len(datasets)
        
        # Analyze each dataset
        for i, dataset in enumerate(datasets, 1):
            logger.info(f"🔬 [{i}/{len(datasets)}] Analyzing: {dataset}")
            self.analyze_single_dataset(dataset)
        
        # Generate insights and recommendations
        self.generate_insights()
        
        # Save analysis report
        self.save_analysis_report()
        
        logger.info("✅ Data quality analysis complete!")
        return self.analysis_results
    
    def get_dataset_list(self):
        """Get list of available datasets"""
        datasets = set()
        blobs = self.bucket.list_blobs(prefix="neso_data/")
        
        for blob in blobs:
            if (blob.name.endswith("/") or 
                "session_summary" in blob.name or 
                "incremental_summary" in blob.name):
                continue
                
            path_parts = blob.name.split("/")
            if len(path_parts) >= 2:
                dataset_name = path_parts[1]
                datasets.add(dataset_name)
        
        return sorted(list(datasets))
    
    def analyze_single_dataset(self, dataset_name):
        """Analyze a single dataset in detail"""
        dataset_info = {
            'name': dataset_name,
            'file_count': 0,
            'total_size_bytes': 0,
            'file_types': set(),
            'sample_files': [],
            'data_samples': []
        }
        
        # List all files in this dataset
        prefix = f"neso_data/{dataset_name}/"
        blobs = list(self.bucket.list_blobs(prefix=prefix))
        
        dataset_info['file_count'] = len(blobs)
        
        for blob in blobs:
            dataset_info['total_size_bytes'] += blob.size
            
            # Determine file type
            if blob.name.endswith('.csv'):
                dataset_info['file_types'].add('CSV')
            elif blob.name.endswith('.json'):
                dataset_info['file_types'].add('JSON')
            elif blob.name.endswith('.png'):
                dataset_info['file_types'].add('PNG')
            elif blob.name.endswith('.pdf'):
                dataset_info['file_types'].add('PDF')
            else:
                dataset_info['file_types'].add('OTHER')
            
            # Sample file names
            if len(dataset_info['sample_files']) < 3:
                dataset_info['sample_files'].append(blob.name.split('/')[-1])
        
        # Analyze sample data content
        if dataset_info['file_count'] > 0:
            self.analyze_dataset_content(dataset_name, dataset_info)
        
        # Update global statistics
        self.analysis_results['total_files'] += dataset_info['file_count']
        self.analysis_results['total_size_mb'] += dataset_info['total_size_bytes'] / (1024 * 1024)
        
        # Categorize dataset
        category = self.categorize_dataset(dataset_name)
        if category not in self.analysis_results['datasets_by_category']:
            self.analysis_results['datasets_by_category'][category] = []
        self.analysis_results['datasets_by_category'][category].append(dataset_info)
        
        # Track file formats
        for file_type in dataset_info['file_types']:
            self.analysis_results['file_formats'][file_type] = self.analysis_results['file_formats'].get(file_type, 0) + 1
    
    def analyze_dataset_content(self, dataset_name, dataset_info):
        """Analyze the actual content of dataset files"""
        try:
            # Find a CSV file to sample
            prefix = f"neso_data/{dataset_name}/"
            blobs = list(self.bucket.list_blobs(prefix=prefix))
            
            csv_blob = None
            for blob in blobs:
                if blob.name.endswith('.csv'):
                    csv_blob = blob
                    break
            
            if csv_blob and csv_blob.size < 10 * 1024 * 1024:  # Only sample files < 10MB
                # Download and sample the data
                content = csv_blob.download_as_text()
                
                # Read with pandas
                df = pd.read_csv(StringIO(content))
                
                sample_info = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': list(df.columns)[:10],  # First 10 columns
                    'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
                    'date_range': self.extract_date_range(df),
                    'data_types': {col: str(df[col].dtype) for col in df.columns[:5]}  # First 5 column types
                }
                
                dataset_info['data_samples'].append(sample_info)
                
                # Store in global sample data
                self.analysis_results['sample_data'][dataset_name] = sample_info
                
        except Exception as e:
            logger.warning(f"⚠️  Could not analyze content for {dataset_name}: {e}")
    
    def extract_date_range(self, df):
        """Extract date range from dataframe"""
        date_columns = []
        for col in df.columns:
            if any(date_word in col.lower() for date_word in ['date', 'time', 'timestamp']):
                date_columns.append(col)
        
        if date_columns:
            try:
                # Try to parse the first date column
                date_col = date_columns[0]
                dates = pd.to_datetime(df[date_col], errors='coerce')
                valid_dates = dates.dropna()
                
                if len(valid_dates) > 0:
                    return {
                        'start_date': valid_dates.min().strftime('%Y-%m-%d'),
                        'end_date': valid_dates.max().strftime('%Y-%m-%d'),
                        'date_column': date_col
                    }
            except:
                pass
        
        return None
    
    def categorize_dataset(self, dataset_name):
        """Categorize dataset based on name"""
        name_lower = dataset_name.lower()
        
        if any(word in name_lower for word in ['demand', 'forecast']):
            return 'Demand & Forecasting'
        elif any(word in name_lower for word in ['wind', 'solar', 'renewable']):
            return 'Renewable Energy'
        elif any(word in name_lower for word in ['balancing', 'bsuos', 'bsad', 'auction']):
            return 'Balancing Services'
        elif any(word in name_lower for word in ['constraint', 'transmission', 'network']):
            return 'Network & Constraints'
        elif any(word in name_lower for word in ['carbon', 'emissions', 'environmental']):
            return 'Environmental'
        elif any(word in name_lower for word in ['interconnector', 'flow', 'trade']):
            return 'Interconnectors'
        elif any(word in name_lower for word in ['ancillary', 'service', 'stor', 'frequency']):
            return 'Ancillary Services'
        elif any(word in name_lower for word in ['fes', 'scenario', 'future']):
            return 'Future Scenarios'
        else:
            return 'Other'
    
    def generate_insights(self):
        """Generate insights and recommendations"""
        results = self.analysis_results
        
        # Data coverage insights
        total_datasets_with_dates = 0
        earliest_date = None
        latest_date = None
        
        for dataset_name, sample in results['sample_data'].items():
            if sample.get('date_range'):
                total_datasets_with_dates += 1
                date_range = sample['date_range']
                
                if earliest_date is None or date_range['start_date'] < earliest_date:
                    earliest_date = date_range['start_date']
                if latest_date is None or date_range['end_date'] > latest_date:
                    latest_date = date_range['end_date']
        
        results['data_coverage'] = {
            'datasets_with_dates': total_datasets_with_dates,
            'earliest_date': earliest_date,
            'latest_date': latest_date,
            'date_span_years': self.calculate_years_span(earliest_date, latest_date) if earliest_date and latest_date else 0
        }
        
        # Generate recommendations
        recommendations = []
        
        if results['total_size_mb'] > 1000:  # More than 1GB
            recommendations.append("💾 Large dataset collection - recommend BigQuery setup for efficient querying")
        
        if 'CSV' in results['file_formats'] and results['file_formats']['CSV'] > 10:
            recommendations.append("📊 Multiple CSV files detected - good for BigQuery ingestion")
        
        if results['data_coverage']['date_span_years'] > 3:
            recommendations.append("📅 Multi-year data coverage - excellent for trend analysis")
        
        if len(results['datasets_by_category']) >= 5:
            recommendations.append("🔄 Diverse dataset categories - suitable for comprehensive energy analysis")
        
        if results['dataset_count'] >= 20:
            recommendations.append("✅ Substantial dataset collection - ready for production analytics")
        
        results['recommendations'] = recommendations
    
    def calculate_years_span(self, start_date, end_date):
        """Calculate years between two date strings"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            return round((end - start).days / 365.25, 1)
        except:
            return 0
    
    def save_analysis_report(self):
        """Save analysis report to cloud storage"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create detailed report
        report = {
            'analysis_timestamp': timestamp,
            'summary': {
                'total_datasets': self.analysis_results['dataset_count'],
                'total_files': self.analysis_results['total_files'],
                'total_size_mb': round(self.analysis_results['total_size_mb'], 2),
                'categories': len(self.analysis_results['datasets_by_category']),
                'data_coverage': self.analysis_results['data_coverage']
            },
            'detailed_analysis': self.analysis_results,
            'executive_summary': self.generate_executive_summary()
        }
        
        # Upload to cloud storage
        blob_path = f"neso_data/data_quality_analysis_{timestamp}.json"
        blob = self.bucket.blob(blob_path)
        blob.upload_from_string(json.dumps(report, indent=2))
        
        logger.info(f"📊 Analysis report saved: {blob_path}")
        return report
    
    def generate_executive_summary(self):
        """Generate executive summary"""
        results = self.analysis_results
        
        summary = []
        summary.append(f"📊 Dataset Collection: {results['dataset_count']} datasets across {len(results['datasets_by_category'])} categories")
        summary.append(f"📁 File Inventory: {results['total_files']} files totaling {results['total_size_mb']:.1f} MB")
        
        if results['data_coverage']['earliest_date']:
            summary.append(f"📅 Data Coverage: {results['data_coverage']['earliest_date']} to {results['data_coverage']['latest_date']} ({results['data_coverage']['date_span_years']} years)")
        
        # Top categories
        categories = results['datasets_by_category']
        if categories:
            largest_category = max(categories.keys(), key=lambda k: len(categories[k]))
            summary.append(f"🏆 Largest Category: {largest_category} ({len(categories[largest_category])} datasets)")
        
        return summary
    
    def print_analysis_summary(self):
        """Print analysis summary to console"""
        results = self.analysis_results
        
        print("\n" + "="*70)
        print("🔬 NESO DATA QUALITY ANALYSIS SUMMARY")
        print("="*70)
        
        print(f"📊 Total Datasets: {results['dataset_count']}")
        print(f"📁 Total Files: {results['total_files']}")
        print(f"💾 Total Size: {results['total_size_mb']:.1f} MB")
        
        print(f"\n📂 Datasets by Category:")
        for category, datasets in results['datasets_by_category'].items():
            print(f"   • {category}: {len(datasets)} datasets")
        
        print(f"\n📄 File Formats:")
        for format_type, count in results['file_formats'].items():
            print(f"   • {format_type}: {count} datasets")
        
        if results['data_coverage']['earliest_date']:
            print(f"\n📅 Data Coverage:")
            print(f"   • Date Range: {results['data_coverage']['earliest_date']} to {results['data_coverage']['latest_date']}")
            print(f"   • Span: {results['data_coverage']['date_span_years']} years")
            print(f"   • Datasets with dates: {results['data_coverage']['datasets_with_dates']}")
        
        print(f"\n💡 Recommendations:")
        for rec in results['recommendations']:
            print(f"   {rec}")
        
        print("="*70)

def main():
    """Main execution function"""
    analyzer = NESODataAnalyzer()
    
    try:
        results = analyzer.analyze_current_datasets()
        analyzer.print_analysis_summary()
        
        print(f"\n✅ Analysis complete! {results['dataset_count']} datasets analyzed.")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()
