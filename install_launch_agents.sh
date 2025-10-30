#!/bin/bash
# Script to install the launch agents for IRIS and NESO data collection

# Change to the project directory
cd "$(dirname "$0")"

# Create the LaunchAgents directory if it doesn't exist
mkdir -p ~/Library/LaunchAgents

# Copy the plist files to the LaunchAgents directory
cp com.georgemajor.elexoniris.plist ~/Library/LaunchAgents/
cp com.georgemajor.nesodata.plist ~/Library/LaunchAgents/

# Load the launch agents
launchctl load ~/Library/LaunchAgents/com.georgemajor.elexoniris.plist
launchctl load ~/Library/LaunchAgents/com.georgemajor.nesodata.plist

echo "Launch agents installed successfully."
echo "IRIS client will start automatically when you log in."
echo "NESO data collection will run every 15 minutes (0, 15, 30, 45) and at startup."
