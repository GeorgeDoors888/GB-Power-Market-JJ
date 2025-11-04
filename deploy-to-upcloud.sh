#!/bin/bash
# Deploy Drive→BigQuery Indexer to UpCloud
# Server: almalinux-1cpu-1gb-uk-lon1
# IP: 94.237.55.15

set -e

SERVER_IP="94.237.55.15"
SERVER_USER="root"
PROJECT_NAME="drive-bq-indexer"

echo "🚀 Deploying Drive→BigQuery Indexer to UpCloud"
echo "================================================"
echo ""
echo "Server: almalinux-1cpu-1gb-uk-lon1"
echo "IP: $SERVER_IP"
echo ""

# Test SSH connection
echo "📡 Testing SSH connection..."
if ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'Connection successful'"; then
    echo "✅ SSH connection working"
else
    echo "❌ Cannot connect to server"
    echo "Please ensure:"
    echo "  1. Your SSH key is added to the server"
    echo "  2. Server is running"
    echo "  3. Firewall allows SSH (port 22)"
    exit 1
fi

echo ""
echo "📦 Installing dependencies on server..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
set -e

# Update system
echo "Updating system packages..."
dnf update -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    dnf install -y dnf-plugins-core
    dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl start docker
    systemctl enable docker
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install git
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    dnf install -y git
    echo "✅ Git installed"
else
    echo "✅ Git already installed"
fi

# Create deployment directory
mkdir -p /opt/driveindexer
echo "✅ Deployment directory created"

ENDSSH

echo ""
echo "📤 Copying project files to server..."
# Use rsync to copy the project (excludes .git, .venv, etc.)
rsync -avz --progress \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='node_modules' \
    --exclude='.env' \
    --exclude='secrets/' \
    ./drive-bq-indexer/ $SERVER_USER@$SERVER_IP:/opt/driveindexer/

echo ""
echo "🔐 Setting up environment..."
echo "⚠️  You need to manually copy your .env file and service account JSON"
echo ""
echo "Run these commands:"
echo "  scp drive-bq-indexer/.env $SERVER_USER@$SERVER_IP:/opt/driveindexer/"
echo "  scp gridsmart_service_account.json $SERVER_USER@$SERVER_IP:/opt/driveindexer/secrets/sa.json"
echo ""
read -p "Press Enter when you've copied the credentials, or Ctrl+C to exit..."

echo ""
echo "🐳 Building Docker image on server..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
set -e
cd /opt/driveindexer

echo "Building Docker image..."
docker build -f infra/docker/Dockerfile.runtime -t driveindexer:latest .
echo "✅ Docker image built"

ENDSSH

echo ""
echo "🚀 Starting the application..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
set -e
cd /opt/driveindexer

# Stop existing container if running
docker stop driveindexer 2>/dev/null || true
docker rm driveindexer 2>/dev/null || true

# Start new container
docker run -d \
    --name driveindexer \
    --restart=always \
    --env-file .env \
    -v /opt/driveindexer/secrets:/secrets \
    -p 8080:8080 \
    driveindexer:latest

echo "✅ Container started"

# Wait for health check
echo "Waiting for application to start..."
sleep 5

# Check if running
if docker ps | grep -q driveindexer; then
    echo "✅ Application is running"
    docker logs driveindexer --tail 20
else
    echo "❌ Application failed to start"
    docker logs driveindexer
    exit 1
fi

ENDSSH

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "✅ Application URL: http://$SERVER_IP:8080"
echo "✅ Health check: http://$SERVER_IP:8080/health"
echo "✅ API docs: http://$SERVER_IP:8080/docs"
echo ""
echo "🔧 Useful commands:"
echo "  ssh $SERVER_USER@$SERVER_IP 'docker logs -f driveindexer'  # View logs"
echo "  ssh $SERVER_USER@$SERVER_IP 'docker restart driveindexer'  # Restart"
echo "  ssh $SERVER_USER@$SERVER_IP 'docker stop driveindexer'     # Stop"
echo ""
echo "📊 Test the API:"
echo "  curl http://$SERVER_IP:8080/health"
echo "  curl 'http://$SERVER_IP:8080/search?q=test&k=5'"
echo ""
