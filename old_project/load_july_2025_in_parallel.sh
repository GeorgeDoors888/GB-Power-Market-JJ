#!/bin/bash

# Script to load the remaining 53 Elexon datasets for July 2025 into BigQuery in parallel.

# --- Configuration ---
DATASET_ID="jibber-jabber-knowledge:uk_energy"
GCS_BUCKET_BASE="gs://jibber-jabber-knowledge-bmrs-data/bmrs_data"
YEAR="2025"
MONTH="07"

# --- List of 53 remaining datasets ---
DATA_TYPES=(
    "abst" "b1320" "b1330" "b1430" "b1440" "b1510" "b1520" "b1530" "b1540" 
    "b1610" "b1620" "b1630" "b1720" "b1730" "b1740" "b1750" "b1760" "b1770" 
    "b1780" "b1790" "b1810" "b1820" "b1830" "b0610" "b0620" "b0630" "b0640" 
    "b0650" "b0710" "b0720" "b0810" "b0910" "b1010" "b1020" "b1030" "b1110" 
    "b1210" "bod" "dersydata" "detayl" "forgen" "freq" "fuelhh" "fuelinst" 
    "intercon" "lolp" "mid" "nonbm" "pn" "qas" "remit" "syswarn" "windfor"
)

echo "🚀 Starting parallel load for 53 datasets for $YEAR-$MONTH..."

# --- Loop and launch background jobs ---
for DATA_TYPE in "${DATA_TYPES[@]}"; do
    TABLE_NAME="elexon_${DATA_TYPE}_${YEAR}_${MONTH}"
    GCS_PATH="${GCS_BUCKET_BASE}/${DATA_TYPE}/${YEAR}/${MONTH}/*.json"
    
    echo "  -> Launching load for ${TABLE_NAME}"
    
    bq load \
        --source_format=NEWLINE_DELIMITED_JSON \
        --autodetect \
        "${DATASET_ID}.${TABLE_NAME}" \
        "${GCS_PATH}" &
done

# --- Wait for all background jobs to complete ---
echo "⏳ Waiting for all load jobs to complete..."
wait
echo "✅ All parallel load jobs finished."

