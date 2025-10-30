#!/bin/bash
"""
Complete Environment Setup Script
Creates a fresh virtual environment and installs all dependencies for Elexon data ingestion
"""

set -e  # Exit on any error

echo "🚀 Setting up complete environment for Elexon data ingestion..."
echo "=============================================================="

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📍 Working directory: $SCRIPT_DIR"

# Remove existing virtual environment if it exists
if [ -d ".venv_ingestion" ]; then
    echo "🧹 Removing existing virtual environment..."
    rm -rf .venv_ingestion
fi

# Create new virtual environment
echo "🔧 Creating new virtual environment (.venv_ingestion)..."
python3 -m venv .venv_ingestion

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source .venv_ingestion/bin/activate

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install core dependencies first
echo "🔧 Installing core dependencies..."
pip install wheel setuptools

# Install all requirements
echo "📚 Installing requirements from requirements.txt..."
pip install -r requirements.txt

# Install any additional dependencies that might be missing
echo "🔧 Installing additional dependencies..."
pip install \
    google-cloud-core \
    google-cloud-storage \
    google-api-core \
    grpcio \
    protobuf \
    urllib3 \
    certifi \
    charset-normalizer \
    idna

echo ""
echo "✅ Environment setup complete!"
echo "=============================================="
echo ""
echo "📋 Installed packages:"
pip list | grep -E "(google|pandas|requests|tqdm|python-dotenv|pyarrow)"

echo ""
echo "🎯 Next steps:"
echo "1. Activate environment: source .venv_ingestion/bin/activate"
echo "2. Run 4-day ingestion: python ingest_elexon_4days.py"
echo ""
echo "🔍 Environment verification:"
python -c "
import sys
print(f'Python version: {sys.version}')
print(f'Virtual environment: {sys.prefix}')

try:
    import pandas as pd
    print(f'✅ pandas {pd.__version__}')
except ImportError as e:
    print(f'❌ pandas: {e}')

try:
    from google.cloud import bigquery
    print('✅ google-cloud-bigquery')
except ImportError as e:
    print(f'❌ google-cloud-bigquery: {e}')

try:
    import requests
    print(f'✅ requests {requests.__version__}')
except ImportError as e:
    print(f'❌ requests: {e}')

try:
    import tqdm
    print(f'✅ tqdm {tqdm.__version__}')
except ImportError as e:
    print(f'❌ tqdm: {e}')

try:
    from dotenv import load_dotenv
    print('✅ python-dotenv')
except ImportError as e:
    print(f'❌ python-dotenv: {e}')

try:
    import pyarrow
    print(f'✅ pyarrow {pyarrow.__version__}')
except ImportError as e:
    print(f'❌ pyarrow: {e}')
"

echo ""
echo "🚀 Environment is ready for Elexon data ingestion!"
