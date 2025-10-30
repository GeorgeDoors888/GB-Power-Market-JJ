#!/bin/zsh
# Startup script for Elexon Data Ingestor
# Save this file in a location that gets executed at login/startup

# Change to the project directory
cd /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop

# Activate the virtual environment
source .venv/bin/activate

# Run the ingestor script
python startup_ingestor.py

# Keep terminal open after completion (optional)
# echo "Press any key to close this window..."
# read -k1 -s
