#!/bin/bash
# Quick start script for Codex Server

echo "🚀 Starting Codex Server Setup..."
echo ""

# Navigate to codex-server directory
cd "$(dirname "$0")"

# Check Python version
echo "📦 Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Start server
echo ""
echo "🎯 Starting Codex Server on http://localhost:8000"
echo "   Health check: http://localhost:8000/health"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 codex_server.py
