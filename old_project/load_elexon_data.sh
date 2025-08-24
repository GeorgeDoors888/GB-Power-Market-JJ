#!/bin/bash
# Script to load Elexon data from GCS to BigQuery

echo "===== Elexon Data Loading Script ====="
echo "This script will load Elexon data from GCS to BigQuery."
echo

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "Virtual environment not found. Creating one..."
        python -m venv venv
        source venv/bin/activate
        pip install google-cloud-storage google-cloud-bigquery
    fi
fi

# Check authentication
echo "Checking authentication status..."
./load_elexon_data.py --check-auth

if [[ $? -ne 0 ]]; then
    echo "Authentication failed. Please run: gcloud auth application-default login"
    exit 1
fi

# Ask user which dataset to load
echo "Which Elexon dataset would you like to load?"
echo "1) All Elexon datasets"
echo "2) Bid-Offer Acceptances"
echo "3) Generation Outturn"
echo "4) Demand Outturn"
echo "5) System Warnings"
echo "6) Frequency"
read -p "Enter your choice [1-6]: " data_choice

DATA_TYPE=""
case $data_choice in
    1) DATA_TYPE="all" ;;
    2) DATA_TYPE="bid_offer_acceptances" ;;
    3) DATA_TYPE="generation_outturn" ;;
    4) DATA_TYPE="demand_outturn" ;;
    5) DATA_TYPE="system_warnings" ;;
    6) DATA_TYPE="frequency" ;;
    *) echo "Invalid choice. Using 'all' as default."; DATA_TYPE="all" ;;
esac

# Ask about date filtering
echo "Would you like to filter by date?"
echo "1) Load all available data"
echo "2) Load data from a specific start date"
echo "3) Load data for a date range"
read -p "Enter your choice [1-3]: " date_choice

DATE_PARAMS=""
if [[ $date_choice -eq 2 ]]; then
    read -p "Enter the start date (YYYY-MM-DD): " date_input
    # Validate date format
    if [[ $date_input =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        DATE_PARAMS="--start-date $date_input"
    else
        echo "Invalid date format. Using no date filter."
    fi
elif [[ $date_choice -eq 3 ]]; then
    read -p "Enter the start date (YYYY-MM-DD): " start_date
    read -p "Enter the end date (YYYY-MM-DD): " end_date
    
    # Validate date formats
    if [[ $start_date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && [[ $end_date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        DATE_PARAMS="--start-date $start_date --end-date $end_date"
    else
        echo "Invalid date format. Using no date filter."
    fi
fi

# Ask about limiting files
echo "Would you like to limit the number of files processed per data type?"
echo "1) Process all files"
echo "2) Set a limit"
read -p "Enter your choice [1-2]: " limit_choice

MAX_FILES=""
if [[ $limit_choice -eq 2 ]]; then
    read -p "Enter maximum number of files to process: " files_input
    # Validate number
    if [[ $files_input =~ ^[0-9]+$ ]]; then
        MAX_FILES="--max-files $files_input"
    else
        echo "Invalid number. Processing all files."
    fi
fi

# Run the data loader
echo "Starting Elexon data loading process..."
echo "Running: ./load_elexon_data.py --data-type $DATA_TYPE $DATE_PARAMS $MAX_FILES"

./load_elexon_data.py --data-type $DATA_TYPE $DATE_PARAMS $MAX_FILES

if [[ $? -eq 0 ]]; then
    echo "Data loading completed successfully!"
    echo "You can now validate the data using the following command:"
    echo "  ./load_elexon_data.py --data-type $DATA_TYPE --validate-only"
else
    echo "Data loading completed with errors."
    echo "Please check the log file for details: elexon_data_loading.log"
fi

echo "===== Elexon Data Loading Script Complete ====="
