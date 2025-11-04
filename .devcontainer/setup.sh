#!/bin/bash
# Codespace setup script

echo "🚀 Setting up Codex Server in Codespace..."
echo ""

# Install main project dependencies
echo "📦 Installing main dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

# Setup codex-server
echo ""
echo "🔧 Setting up Codex Server..."
cd codex-server

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate and install dependencies
echo "Installing Codex Server dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Make scripts executable
chmod +x server-start.sh server-stop.sh server-status.sh

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Quick Start Commands:"
echo "   cd codex-server && source .venv/bin/activate"
echo "   python codex_server.py"
echo ""
echo "📝 Or use the convenience scripts:"
echo "   cd codex-server && ./server-start.sh"
echo ""
echo "🌐 Your server will be available at:"
echo "   https://[codespace-name]-8000.app.github.dev"
echo ""
echo "💰 Cost Control:"
echo "   - Auto-stops after 30min idle"
echo "   - Free: 120 core-hours/month (60 hours on 2-core)"
echo "   - Current usage: Check https://github.com/settings/billing"
echo ""
