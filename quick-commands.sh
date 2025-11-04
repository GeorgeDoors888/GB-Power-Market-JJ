#!/bin/bash

# 🚀 Quick Commands for UpCloud Deployment
# Copy-paste these commands as needed

SERVER="root@94.237.55.15"

echo "==================================="
echo "🚀 UpCloud Deployment Quick Commands"
echo "==================================="
echo ""

# Health check
echo "📊 HEALTH CHECK:"
echo "curl http://94.237.55.15:8080/health"
echo ""

# API docs
echo "📚 OPEN API DOCS:"
echo "open http://94.237.55.15:8080/docs"
echo ""

# Indexing pipeline
echo "🔄 RUN FULL INDEXING PIPELINE:"
echo "ssh $SERVER 'docker exec driveindexer python -m src.cli index-drive'"
echo "ssh $SERVER 'docker exec driveindexer python -m src.cli extract'"
echo "ssh $SERVER 'docker exec driveindexer python -m src.cli build-embeddings'"
echo ""

# Management
echo "🔧 MANAGEMENT:"
echo "# View logs"
echo "ssh $SERVER 'docker logs -f driveindexer'"
echo ""
echo "# Restart container"
echo "ssh $SERVER 'docker restart driveindexer'"
echo ""
echo "# Check status"
echo "ssh $SERVER 'docker ps'"
echo ""
echo "# Resource usage"
echo "ssh $SERVER 'docker stats driveindexer --no-stream'"
echo ""

# Monitoring
echo "🔍 MONITORING:"
echo "./monitor-deployment.sh"
echo ""

echo "==================================="
