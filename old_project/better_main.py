def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Direct BOD Analysis with Alternative Authentication")
    
    # Date range
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    
    # Project settings
    parser.add_argument("--project", help=f"Google Cloud project ID (default: {DEFAULT_PROJECT_ID})")
    parser.add_argument("--dataset", help=f"BigQuery dataset name (default: {DEFAULT_DATASET})")
    parser.add_argument("--bod-table", help=f"BOD table name (default: {DEFAULT_TABLE_BOD})")
    parser.add_argument("--impniv-table", help=f"Imbalance/NIV table name (default: {DEFAULT_TABLE_IMPNIV})")
    parser.add_argument("--demand-table", help=f"Demand table name (default: {DEFAULT_TABLE_DEMAND})")
    parser.add_argument("--genmix-table", help=f"Generation mix table name (default: {DEFAULT_TABLE_GENMIX})")
    
    # Authentication
    parser.add_argument("--service-account", help="Path to service account key file")
    
    # Output
    parser.add_argument("--output-dir", help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    
    # Flags
    parser.add_argument("--use-synthetic", action="store_true", help="Use synthetic data instead of querying BigQuery")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse dates
    start_date = None
    if args.start_date:
        start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    
    end_date = None
    if args.end_date:
        end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    
    # Set up configuration
    project_id = args.project or DEFAULT_PROJECT_ID
    dataset = args.dataset or DEFAULT_DATASET
    table_bod = args.bod_table or DEFAULT_TABLE_BOD
    table_impniv = args.impniv_table or DEFAULT_TABLE_IMPNIV
    table_demand = args.demand_table or DEFAULT_TABLE_DEMAND
    table_genmix = args.genmix_table or DEFAULT_TABLE_GENMIX
    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    
    # Run analysis
    analyzer = DirectBODAnalysis(
        project_id=project_id,
        dataset=dataset,
        table_bod=table_bod,
        table_impniv=table_impniv,
        table_demand=table_demand,
        table_genmix=table_genmix,
        start_date=start_date,
        end_date=end_date,
        output_dir=output_dir,
        service_account_path=args.service_account,
        use_synthetic=args.use_synthetic,
        debug=args.debug
    )
    
    success = analyzer.run_analysis()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
