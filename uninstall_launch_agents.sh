#!/bin/bash
# Script to uninstall the launch agents for IRIS and NESO data collection

# Unload the launch agents
launchctl unload ~/Library/LaunchAgents/com.georgemajor.elexoniris.plist
launchctl unload ~/Library/LaunchAgents/com.georgemajor.nesodata.plist

# Remove the plist files
rm -f ~/Library/LaunchAgents/com.georgemajor.elexoniris.plist
rm -f ~/Library/LaunchAgents/com.georgemajor.nesodata.plist

echo "Launch agents uninstalled successfully."
