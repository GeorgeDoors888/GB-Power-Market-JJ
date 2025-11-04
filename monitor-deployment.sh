#!/bin/bash

# 🔍 UpCloud Deployment Monitoring Script
# Checks deployment status and health of drive-bq-indexer

set -e

SERVER_IP="94.237.55.15"
SERVER_USER="root"
CONTAINER_NAME="driveindexer"
API_PORT="8080"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "🔍 Monitoring UpCloud Deployment"
echo "=================================="
echo ""

# 1. Check SSH connectivity
echo -e "${BLUE}📡 Checking SSH connection...${NC}"
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} "echo ''" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ SSH connection failed${NC}"
    exit 1
fi
echo ""

# 2. Check Docker installation
echo -e "${BLUE}🐳 Checking Docker...${NC}"
if ssh ${SERVER_USER}@${SERVER_IP} "command -v docker" >/dev/null 2>&1; then
    DOCKER_VERSION=$(ssh ${SERVER_USER}@${SERVER_IP} "docker --version")
    echo -e "${GREEN}✅ Docker installed: ${DOCKER_VERSION}${NC}"
else
    echo -e "${YELLOW}⚠️  Docker not installed yet${NC}"
fi
echo ""

# 3. Check if project directory exists
echo -e "${BLUE}📁 Checking project directory...${NC}"
if ssh ${SERVER_USER}@${SERVER_IP} "test -d /opt/driveindexer" 2>/dev/null; then
    echo -e "${GREEN}✅ Project directory exists: /opt/driveindexer${NC}"
    
    # Check for credentials
    if ssh ${SERVER_USER}@${SERVER_IP} "test -f /opt/driveindexer/.env" 2>/dev/null; then
        echo -e "${GREEN}   ✅ .env file present${NC}"
    else
        echo -e "${YELLOW}   ⚠️  .env file missing${NC}"
    fi
    
    if ssh ${SERVER_USER}@${SERVER_IP} "test -f /opt/driveindexer/secrets/sa.json" 2>/dev/null; then
        echo -e "${GREEN}   ✅ Service account JSON present${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Service account JSON missing${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Project directory not created yet${NC}"
fi
echo ""

# 4. Check Docker container
echo -e "${BLUE}🐳 Checking Docker container...${NC}"
CONTAINER_STATUS=$(ssh ${SERVER_USER}@${SERVER_IP} "docker ps -a --filter name=${CONTAINER_NAME} --format '{{.Status}}'" 2>/dev/null || echo "NOT_FOUND")

if [ "$CONTAINER_STATUS" = "NOT_FOUND" ]; then
    echo -e "${YELLOW}⚠️  Container '${CONTAINER_NAME}' not found${NC}"
elif [[ "$CONTAINER_STATUS" == Up* ]]; then
    echo -e "${GREEN}✅ Container running: ${CONTAINER_STATUS}${NC}"
    
    # Get container details
    UPTIME=$(ssh ${SERVER_USER}@${SERVER_IP} "docker ps --filter name=${CONTAINER_NAME} --format '{{.Status}}'")
    echo -e "${GREEN}   Uptime: ${UPTIME}${NC}"
else
    echo -e "${RED}❌ Container exists but not running: ${CONTAINER_STATUS}${NC}"
fi
echo ""

# 5. Check container logs (last 20 lines)
echo -e "${BLUE}📋 Recent container logs:${NC}"
if ssh ${SERVER_USER}@${SERVER_IP} "docker ps --filter name=${CONTAINER_NAME}" | grep -q "${CONTAINER_NAME}"; then
    echo -e "${YELLOW}---${NC}"
    ssh ${SERVER_USER}@${SERVER_IP} "docker logs ${CONTAINER_NAME} --tail 20 2>&1" || echo "No logs available"
    echo -e "${YELLOW}---${NC}"
else
    echo -e "${YELLOW}⚠️  Container not running, no logs available${NC}"
fi
echo ""

# 6. Check API health endpoint
echo -e "${BLUE}🏥 Checking API health...${NC}"
if curl -s --connect-timeout 5 http://${SERVER_IP}:${API_PORT}/health >/dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s http://${SERVER_IP}:${API_PORT}/health)
    echo -e "${GREEN}✅ API responding: ${HEALTH_RESPONSE}${NC}"
    echo -e "${GREEN}   URL: http://${SERVER_IP}:${API_PORT}/health${NC}"
else
    echo -e "${RED}❌ API not responding on port ${API_PORT}${NC}"
    echo -e "${YELLOW}   This could mean:${NC}"
    echo -e "${YELLOW}   - Container not started yet${NC}"
    echo -e "${YELLOW}   - Firewall blocking port ${API_PORT}${NC}"
    echo -e "${YELLOW}   - Application error (check logs above)${NC}"
fi
echo ""

# 7. Check available API endpoints
echo -e "${BLUE}🌐 Available endpoints:${NC}"
if curl -s --connect-timeout 5 http://${SERVER_IP}:${API_PORT}/health >/dev/null 2>&1; then
    echo -e "${GREEN}   http://${SERVER_IP}:${API_PORT}/health${NC}"
    echo -e "${GREEN}   http://${SERVER_IP}:${API_PORT}/docs${NC}"
    echo -e "${GREEN}   http://${SERVER_IP}:${API_PORT}/redoc${NC}"
    echo -e "${GREEN}   http://${SERVER_IP}:${API_PORT}/search?q=your_query${NC}"
else
    echo -e "${YELLOW}⚠️  API not accessible yet${NC}"
fi
echo ""

# 8. Check port accessibility
echo -e "${BLUE}🔌 Checking port ${API_PORT}...${NC}"
if nc -z -w5 ${SERVER_IP} ${API_PORT} 2>/dev/null; then
    echo -e "${GREEN}✅ Port ${API_PORT} is open and accessible${NC}"
else
    echo -e "${RED}❌ Port ${API_PORT} is not accessible${NC}"
    echo -e "${YELLOW}   Run: ssh root@${SERVER_IP} 'firewall-cmd --add-port=${API_PORT}/tcp --permanent && firewall-cmd --reload'${NC}"
fi
echo ""

# 9. Summary
echo -e "${BLUE}📊 Deployment Summary${NC}"
echo "=================================="

if [[ "$CONTAINER_STATUS" == Up* ]] && curl -s --connect-timeout 5 http://${SERVER_IP}:${API_PORT}/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Visit API docs: http://${SERVER_IP}:${API_PORT}/docs"
    echo "2. Run indexing: ssh root@${SERVER_IP} 'docker exec ${CONTAINER_NAME} python -m src.cli index-drive'"
    echo "3. Extract content: ssh root@${SERVER_IP} 'docker exec ${CONTAINER_NAME} python -m src.cli extract'"
    echo "4. Build embeddings: ssh root@${SERVER_IP} 'docker exec ${CONTAINER_NAME} python -m src.cli build-embeddings'"
elif [ "$CONTAINER_STATUS" = "NOT_FOUND" ]; then
    echo -e "${YELLOW}⚠️  DEPLOYMENT IN PROGRESS${NC}"
    echo ""
    echo "Container not created yet. Deployment script may still be running."
else
    echo -e "${RED}❌ DEPLOYMENT NEEDS ATTENTION${NC}"
    echo ""
    echo "Check the logs above for errors."
fi
echo ""
