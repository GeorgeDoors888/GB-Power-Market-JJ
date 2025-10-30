#!/bin/bash
# This script runs the BigQuery query Python script using the correct virtual environment.

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Define the path to the python executable in the virtual environment
PYTHON_EXEC="$DIR/.venv/bin/python"

# Define the path to the python script to run
PYTHON_SCRIPT="$DIR/run_bq_query.py"

# Execute the python script
echo "Running Python script: $PYTHON_SCRIPT"
"$PYTHON_EXEC" "$PYTHON_SCRIPT"
