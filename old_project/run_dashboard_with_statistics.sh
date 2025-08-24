#!/bin/bash
# Script to run the dashboard with the advanced statistics

# Activate the virtual environment
source venv/bin/activate

# Kill any existing Streamlit processes
pkill -f streamlit || true

# Wait a moment to ensure ports are released
sleep 2

# Create a temporary Streamlit config file to set the port
cat > ~/.streamlit/config.toml << EOF
[server]
port = 8505
EOF

# Run the main interactive dashboard
echo "Starting the UK Energy Dashboard with Advanced Statistics on port 8505..."
echo "Please visit http://localhost:8505 in your browser"
echo "BE SURE TO LOOK FOR AND CLICK ON THE 'ADVANCED STATISTICS' TAB AT THE TOP"
echo "The tabs should be: Demand Analysis, Generation Analysis, Balancing Analysis, Advanced Statistics"
echo ""
streamlit run "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber/interactive_dashboard_app.py"
