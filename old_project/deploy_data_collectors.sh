#!/bin/bash
# Enhanced deployment script for Elexon & NESO data collection system
# This script orchestrates the deployment and execution of data downloaders
# and loaders to ensure comprehensive data coverage from 2016 to present.

set -e  # Exit on error

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
START_DATE="2016-01-01"
END_DATE=$(date +"%Y-%m-%d")
PROJECT_ID="jibber-jabber-knowledge"
BUCKET_NAME="jibber-jabber-knowledge-bmrs-data"
DATASET_ID="uk_energy_prod"

# Execution directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${SCRIPT_DIR}"

# Create a timestamp for logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "${LOG_DIR}"
MAIN_LOG="${LOG_DIR}/deployment_${TIMESTAMP}.log"

# Function for logging
log() {
  local level="$1"
  local message="$2"
  
  # Format the message based on level
  case "${level}" in
    "INFO")
      echo -e "${BLUE}[INFO]${NC} ${message}"
      ;;
    "SUCCESS")
      echo -e "${GREEN}[SUCCESS]${NC} ${message}"
      ;;
    "WARNING")
      echo -e "${YELLOW}[WARNING]${NC} ${message}"
      ;;
    "ERROR")
      echo -e "${RED}[ERROR]${NC} ${message}"
      ;;
    *)
      echo -e "${message}"
      ;;
  esac
  
  # Also log to file
  echo "[$(date +"%Y-%m-%d %H:%M:%S")] [${level}] ${message}" >> "${MAIN_LOG}"
}

# Function to check Google Cloud authentication
check_gcp_auth() {
  log "INFO" "Checking GCP authentication..."
  
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
    log "ERROR" "Not authenticated to GCP. Run 'gcloud auth login' first."
    exit 1
  fi
  
  log "SUCCESS" "GCP authentication verified."
  
  # Check project access
  if ! gcloud projects describe "${PROJECT_ID}" &>/dev/null; then
    log "ERROR" "Cannot access project ${PROJECT_ID}. Check permissions."
    exit 1
  fi
  
  log "SUCCESS" "Access to project ${PROJECT_ID} verified."
  
  # Check bucket access
  if ! gsutil ls -b "gs://${BUCKET_NAME}" &>/dev/null; then
    log "ERROR" "Cannot access bucket ${BUCKET_NAME}. Check permissions."
    exit 1
  fi
  
  log "SUCCESS" "Access to bucket ${BUCKET_NAME} verified."
}

# Function to check Python environment
check_python_env() {
  log "INFO" "Checking Python environment..."
  
  # Check if virtual environment is activated
  if [[ -z "${VIRTUAL_ENV}" ]]; then
    if [[ -d "venv" ]]; then
      log "INFO" "Activating virtual environment..."
      source venv/bin/activate
    else
      log "ERROR" "Virtual environment not found. Run ./setup_environment.sh first."
      exit 1
    fi
  fi
  
  # Check Python version
  PYTHON_VERSION=$(python3 --version 2>&1)
  log "INFO" "Using ${PYTHON_VERSION}"
  
  # Check required packages
  local required_packages="google-cloud-storage google-cloud-bigquery requests"
  
  for package in ${required_packages}; do
    if ! python3 -c "import ${package//-/_}" &>/dev/null; then
      log "WARNING" "Package ${package} not installed. Installing..."
      pip install "${package}"
    fi
  done
  
  log "SUCCESS" "Python environment ready."
}

# Function to check API key availability
check_api_key() {
  log "INFO" "Checking BMRS API key..."
  
  if [ -f "api.env" ]; then
    source api.env
    if [ -n "${BMRS_API_KEY}" ] || [ -n "${BMRS_API_KEY_1}" ]; then
      log "SUCCESS" "BMRS API key found in api.env"
    else
      log "ERROR" "BMRS API key not found in api.env"
      exit 1
    fi
  elif [ -n "${BMRS_API_KEY}" ]; then
    log "SUCCESS" "BMRS API key found in environment"
  else
    log "ERROR" "BMRS API key not found. Add to api.env or set BMRS_API_KEY environment variable."
    exit 1
  fi
}

# Function to deploy and run the downloader
run_data_downloader() {
  local dataset="$1"
  local start_date="${2:-$START_DATE}"
  local end_date="${3:-$END_DATE}"
  
  log "INFO" "Running data downloader for ${dataset} from ${start_date} to ${end_date}..."
  
  python3 enhanced_elexon_neso_downloader.py \
    --start-date "${start_date}" \
    --end-date "${end_date}" \
    --datasets "${dataset}" \
    --bucket "${BUCKET_NAME}" \
    --project "${PROJECT_ID}" \
    --dataset-id "${DATASET_ID}" \
    --max-days 7 2>&1 | tee -a "${LOG_DIR}/download_${dataset}_${TIMESTAMP}.log"
  
  local status=${PIPESTATUS[0]}
  
  if [ ${status} -eq 0 ]; then
    log "SUCCESS" "Download completed for ${dataset}"
  else
    log "ERROR" "Download failed for ${dataset} with status ${status}"
    return ${status}
  fi
}

# Function to deploy and run the BigQuery loader
run_bigquery_loader() {
  local dataset="$1"
  local start_date="${2:-$START_DATE}"
  local end_date="${3:-$END_DATE}"
  
  log "INFO" "Running BigQuery loader for ${dataset} from ${start_date} to ${end_date}..."
  
  python3 enhanced_bigquery_loader.py \
    --start-date "${start_date}" \
    --end-date "${end_date}" \
    --datasets "${dataset}" \
    --bucket "${BUCKET_NAME}" \
    --project "${PROJECT_ID}" \
    --dataset-id "${DATASET_ID}" \
    --max-workers 4 2>&1 | tee -a "${LOG_DIR}/load_${dataset}_${TIMESTAMP}.log"
  
  local status=${PIPESTATUS[0]}
  
  if [ ${status} -eq 0 ]; then
    log "SUCCESS" "BigQuery load completed for ${dataset}"
  else
    log "ERROR" "BigQuery load failed for ${dataset} with status ${status}"
    return ${status}
  fi
}

# Function to verify BigQuery data
verify_bigquery_data() {
  local dataset="$1"
  local table_name=""
  
  case "${dataset}" in
    "bid_offer_acceptances")
      table_name="elexon_bid_offer_acceptances"
      ;;
    "generation_outturn")
      table_name="elexon_generation_outturn"
      ;;
    "demand_outturn")
      table_name="elexon_demand_outturn"
      ;;
    "system_warnings")
      table_name="elexon_system_warnings"
      ;;
    "frequency")
      table_name="elexon_frequency"
      ;;
    "fuel_instructions")
      table_name="elexon_fuel_instructions"
      ;;
    "individual_generation")
      table_name="elexon_individual_generation"
      ;;
    "market_index")
      table_name="elexon_market_index"
      ;;
    "wind_forecasts")
      table_name="elexon_wind_forecasts"
      ;;
    "balancing_services")
      table_name="elexon_balancing_services"
      ;;
    "carbon_intensity")
      table_name="elexon_carbon_intensity"
      ;;
    *)
      log "ERROR" "Unknown dataset: ${dataset}"
      return 1
      ;;
  esac
  
  log "INFO" "Verifying BigQuery data for ${table_name}..."
  
  # Run a count query to check if data exists
  local count=$(bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET_ID}.${table_name}\`" | tail -n 1)
  
  if [ -z "${count}" ] || [ "${count}" -eq "0" ]; then
    log "WARNING" "No data found in ${table_name}"
    return 1
  fi
  
  # Check date range
  local min_date=$(bq query --use_legacy_sql=false --format=csv "SELECT MIN(CAST(settlement_date AS DATE)) FROM \`${PROJECT_ID}.${DATASET_ID}.${table_name}\`" | tail -n 1)
  local max_date=$(bq query --use_legacy_sql=false --format=csv "SELECT MAX(CAST(settlement_date AS DATE)) FROM \`${PROJECT_ID}.${DATASET_ID}.${table_name}\`" | tail -n 1)
  
  log "INFO" "Table ${table_name} contains ${count} rows from ${min_date} to ${max_date}"
  
  # Parse dates to check coverage
  local min_year=$(echo "${min_date}" | cut -d'-' -f1)
  local max_year=$(echo "${max_date}" | cut -d'-' -f1)
  local current_year=$(date +"%Y")
  
  # Check if we have data from 2016
  if [ -z "${min_year}" ] || [ "${min_year}" -gt "2016" ]; then
    log "WARNING" "Missing early data in ${table_name}. Earliest date is ${min_date}"
    return 1
  fi
  
  # Check if we have current data
  if [ -z "${max_year}" ] || [ "${max_year}" -lt "${current_year}" ]; then
    log "WARNING" "Missing recent data in ${table_name}. Latest date is ${max_date}"
    return 1
  fi
  
  log "SUCCESS" "Data verification passed for ${table_name}"
  return 0
}

# Main execution

# Display banner
echo "=================================================="
echo "  Elexon & NESO Data Collection System Deployment "
echo "  $(date)"
echo "=================================================="

# Check prerequisites
check_gcp_auth
check_python_env
check_api_key

# List of datasets to process
datasets=(
  "bid_offer_acceptances"
  "generation_outturn"
  "demand_outturn"
  "system_warnings"
  "frequency"
  "fuel_instructions"
  "individual_generation"
  "market_index"
  "wind_forecasts"
  "balancing_services"
  "carbon_intensity"
)

# Process each dataset
successful=0
failed=0

for dataset in "${datasets[@]}"; do
  log "INFO" "Processing dataset: ${dataset}"
  
  # First, try to verify if data already exists
  if verify_bigquery_data "${dataset}"; then
    log "INFO" "Dataset ${dataset} already has complete data. Skipping."
    ((successful++))
    continue
  fi
  
  # If data is missing or incomplete, download and load it
  if run_data_downloader "${dataset}" && run_bigquery_loader "${dataset}"; then
    # Verify the data after loading
    if verify_bigquery_data "${dataset}"; then
      log "SUCCESS" "Dataset ${dataset} successfully processed and verified"
      ((successful++))
    else
      log "WARNING" "Dataset ${dataset} processed but verification failed"
      ((failed++))
    fi
  else
    log "ERROR" "Failed to process dataset ${dataset}"
    ((failed++))
  fi
  
  # Add a short delay between datasets to avoid API rate limits
  sleep 5
done

# Final summary
log "INFO" "Deployment completed with ${successful} successful and ${failed} failed datasets"

if [ ${failed} -eq 0 ]; then
  log "SUCCESS" "All datasets processed successfully!"
else
  log "WARNING" "${failed} datasets had issues. Check logs for details."
fi

echo "Logs available at: ${MAIN_LOG}"
echo "=================================================="
