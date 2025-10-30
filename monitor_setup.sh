#!/bin/bash
"""
Monitor Environment Setup and Ingestion Progress
"""

echo "🔍 Environment Setup & Ingestion Monitor"
echo "========================================"
echo "⏰ Current time: $(date)"
echo ""

# Check if virtual environment exists
if [ -d ".venv_ingestion" ]; then
    echo "✅ Virtual environment (.venv_ingestion) exists"

    # Check if it's properly set up
    if [ -f ".venv_ingestion/bin/python" ]; then
        echo "✅ Python executable found in virtual environment"

        # Test basic imports
        .venv_ingestion/bin/python -c "
import sys
print(f'🐍 Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')

try:
    import pandas as pd
    print(f'✅ pandas {pd.__version__}')
except ImportError:
    print('❌ pandas not available')

try:
    from google.cloud import bigquery
    print('✅ google-cloud-bigquery available')
except ImportError:
    print('❌ google-cloud-bigquery not available')

try:
    import requests
    print(f'✅ requests available')
except ImportError:
    print('❌ requests not available')
"
    else
        echo "❌ Python executable not found in virtual environment"
    fi
else
    echo "❌ Virtual environment (.venv_ingestion) not found"
    echo "💡 Run ./setup_environment.sh to create it"
fi

echo ""
echo "📊 Setup Process Status:"
echo "========================"

# Check if setup is running
if pgrep -f "setup_environment.sh" > /dev/null; then
    echo "🔄 Environment setup is currently RUNNING"
    PID=$(pgrep -f "setup_environment.sh")
    echo "🆔 Process ID: $PID"
else
    echo "⭕ Environment setup is NOT running"
fi

echo ""
echo "📊 Ingestion Process Status:"
echo "============================"

# Check if 4-day ingestion is running
if pgrep -f "ingest_elexon_4days.py" > /dev/null; then
    echo "🔄 4-day ingestion is currently RUNNING"
    PID=$(pgrep -f "ingest_elexon_4days.py")
    echo "🆔 Process ID: $PID"

    # Show recent log activity if available
    if ls logs/4day_ingestion_*.log 1> /dev/null 2>&1; then
        echo "📄 Last 3 lines from most recent ingestion log:"
        tail -3 $(ls -t logs/4day_ingestion_*.log | head -1)
    fi
else
    echo "⭕ 4-day ingestion is NOT running"
fi

echo ""
echo "📁 Log Files:"
echo "============="
if ls logs/*.log 1> /dev/null 2>&1; then
    echo "Available log files:"
    ls -la logs/*.log | tail -5
else
    echo "No log files found in logs/ directory"
fi

echo ""
echo "🔄 Background Python Processes:"
echo "==============================="
ps aux | grep python | grep -v grep | head -3

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. If environment setup completed: run ./ingest_elexon_4days.py"
echo "2. Monitor progress: ./monitor_setup.sh"
echo "3. Check logs: tail -f logs/4day_ingestion_*.log"
