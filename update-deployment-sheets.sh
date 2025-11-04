#!/bin/bash

# 📊 Deploy Google Sheets Exporter to UpCloud
# This updates the existing deployment with Sheets export capability

set -e

SERVER_IP="94.237.55.15"
SERVER_USER="root"
CONTAINER_NAME="driveindexer"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "📊 Updating Deployment with Google Sheets Exporter"
echo "=================================================="
echo ""

# 1. Copy new files to server
echo -e "${BLUE}📁 Copying new files to server...${NC}"
rsync -avz --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
    scripts/export_to_sheets.py \
    requirements-sheets.txt \
    ${SERVER_USER}@${SERVER_IP}:/opt/driveindexer/

echo -e "${GREEN}✅ Files copied${NC}"
echo ""

# 2. Stop existing container
echo -e "${BLUE}🛑 Stopping existing container...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} "docker stop ${CONTAINER_NAME} || true"
ssh ${SERVER_USER}@${SERVER_IP} "docker rm ${CONTAINER_NAME} || true"
echo -e "${GREEN}✅ Container stopped${NC}"
echo ""

# 3. Rebuild image with Sheets dependencies
echo -e "${BLUE}🔨 Rebuilding Docker image with Sheets support...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/driveindexer

# Install Sheets dependencies in the existing image
docker run --rm \
    -v /opt/driveindexer:/app \
    -w /app \
    driveindexer:latest \
    pip install gspread gspread-formatting || true

# Rebuild image with new dependencies
cat > Dockerfile.sheets <<'EOF'
FROM driveindexer:latest

# Install Google Sheets libraries
RUN pip install --no-cache-dir \
    gspread>=6.0.0 \
    gspread-formatting>=1.2.0

# Copy new scripts
COPY scripts/export_to_sheets.py /app/scripts/

WORKDIR /app
EOF

docker build -f Dockerfile.sheets -t driveindexer:sheets .
docker tag driveindexer:sheets driveindexer:latest

echo "✅ Image rebuilt"
ENDSSH

echo -e "${GREEN}✅ Image rebuilt${NC}"
echo ""

# 4. Restart container
echo -e "${BLUE}🚀 Starting updated container...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
docker run -d \
    --name driveindexer \
    --restart unless-stopped \
    -p 8080:8080 \
    -v /opt/driveindexer/.env:/app/.env:ro \
    -v /opt/driveindexer/secrets:/secrets:ro \
    driveindexer:latest
ENDSSH

echo -e "${GREEN}✅ Container started${NC}"
echo ""

# 5. Wait for container to be ready
echo -e "${BLUE}⏳ Waiting for container to start...${NC}"
sleep 5

# 6. Verify
echo -e "${BLUE}🔍 Verifying deployment...${NC}"
if curl -s http://${SERVER_IP}:8080/health | grep -q "ok"; then
    echo -e "${GREEN}✅ API responding${NC}"
else
    echo -e "${YELLOW}⚠️  API not responding yet${NC}"
fi

# Check if script exists
if ssh ${SERVER_USER}@${SERVER_IP} "docker exec ${CONTAINER_NAME} test -f /app/scripts/export_to_sheets.py"; then
    echo -e "${GREEN}✅ Export script installed${NC}"
else
    echo -e "${YELLOW}⚠️  Export script not found${NC}"
fi

echo ""
echo "=" * 50
echo -e "${GREEN}✅ Update Complete!${NC}"
echo "=" * 50
echo ""
echo "To export Drive metadata to Google Sheets, run:"
echo ""
echo "  ssh ${SERVER_USER}@${SERVER_IP} 'docker exec ${CONTAINER_NAME} python scripts/export_to_sheets.py'"
echo ""
