#!/bin/bash
# Dell-IRIS Coordinator Script
# Manages workload distribution between Dell R630 (128GB) and IRIS server (2GB)
# Author: George Major
# Date: Dec 21, 2025

set -e

DELL_HOME="/home/george/GB-Power-Market-JJ"
IRIS_HOST="iris"
IRIS_PATH="/opt/iris-pipeline"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Dell-IRIS Infrastructure Coordinator               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to check IRIS server health
check_iris_health() {
    echo -e "${YELLOW}Checking IRIS server health...${NC}"

    if ssh -o ConnectTimeout=5 $IRIS_HOST 'true' 2>/dev/null; then
        echo -e "${GREEN}✅ IRIS server reachable${NC}"

        # Check memory
        IRIS_MEM=$(ssh $IRIS_HOST "free -m | awk 'NR==2{printf \"%d\", \$7}'")
        echo "   Memory available: ${IRIS_MEM} MB"

        # Check IRIS process
        if ssh $IRIS_HOST "ps aux | grep -v grep | grep iris" >/dev/null 2>&1; then
            echo -e "${GREEN}   ✅ IRIS client running${NC}"
        else
            echo -e "${RED}   ❌ IRIS client NOT running${NC}"
            return 1
        fi

        # Check disk space
        IRIS_DISK=$(ssh $IRIS_HOST "df -h /opt | awk 'NR==2{print \$5}' | sed 's/%//'")
        if [ "$IRIS_DISK" -gt 80 ]; then
            echo -e "${RED}   ⚠️  Disk usage high: ${IRIS_DISK}%${NC}"
        else
            echo "   Disk usage: ${IRIS_DISK}%"
        fi

        return 0
    else
        echo -e "${RED}❌ IRIS server UNREACHABLE${NC}"
        return 1
    fi
}

# Function to check Dell resources
check_dell_resources() {
    echo -e "\n${YELLOW}Checking Dell resources...${NC}"

    # RAM
    DELL_MEM_AVAIL=$(free -m | awk 'NR==2{printf "%d", $7}')
    DELL_MEM_TOTAL=$(free -m | awk 'NR==2{printf "%d", $2}')
    DELL_MEM_PCT=$((100 * DELL_MEM_AVAIL / DELL_MEM_TOTAL))

    echo "   RAM: ${DELL_MEM_AVAIL} MB available / ${DELL_MEM_TOTAL} MB total (${DELL_MEM_PCT}% free)"

    if [ "$DELL_MEM_AVAIL" -lt 10240 ]; then
        echo -e "${RED}   ⚠️  Low memory warning (<10 GB)${NC}"
    else
        echo -e "${GREEN}   ✅ Memory healthy${NC}"
    fi

    # CPU load
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo "   CPU load: ${LOAD_AVG}"

    # Disk space
    DELL_DISK=$(df -h ~ | awk 'NR==2{print $5}' | sed 's/%//')
    echo "   Disk usage: ${DELL_DISK}%"

    # Active Python processes
    PYTHON_COUNT=$(ps aux | grep python3 | grep -v grep | wc -l)
    echo "   Active Python processes: ${PYTHON_COUNT}"
}

# Function to check BigQuery data freshness
check_bigquery_status() {
    echo -e "\n${YELLOW}Checking BigQuery data status...${NC}"

    python3 -c "
from google.cloud import bigquery
import os
from datetime import datetime, timedelta

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '${DELL_HOME}/inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

tables = {
    'boalf_complete': 'SELECT MAX(DATE(acceptanceTime)) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete\`',
    'boav': 'SELECT MAX(DATE(settlementDate)) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_boav\`',
    'mid_iris': 'SELECT MAX(DATE(settlementDate)) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris\`'
}

today = datetime.now().date()
issues = []

for name, query in tables.items():
    result = client.query(query).result()
    latest_date = list(result)[0][0]
    days_old = (today - latest_date).days

    status = '✅' if days_old <= 1 else '❌'
    print(f'   {status} {name}: {latest_date} ({days_old} days old)')

    if days_old > 1:
        issues.append(name)

if issues:
    print(f\"\n   ⚠️  Data gaps detected in: {', '.join(issues)}\")
    exit(1)
else:
    print(f\"\n   ✅ All tables current\")
    exit(0)
"
}

# Function to offload IRIS work to Dell
offload_to_dell() {
    echo -e "\n${YELLOW}Offloading IRIS collection to Dell...${NC}"

    # Check if IRIS client is already running on Dell
    if ps aux | grep -v grep | grep "client.py" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ IRIS client already running on Dell${NC}"
    else
        echo "Starting IRIS client on Dell..."
        cd /opt/iris-pipeline
        nohup python3 client.py > ~/logs/iris_client_dell.log 2>&1 &
        echo -e "${GREEN}✅ IRIS client started on Dell (PID: $!)${NC}"
        echo "   Log: ~/logs/iris_client_dell.log"
    fi
}

# Function to restart IRIS server
restart_iris_server() {
    echo -e "\n${YELLOW}Restarting IRIS server...${NC}"

    ssh $IRIS_HOST "cd ${IRIS_PATH} && pkill -f client.py; sleep 2; nohup python3 client.py > logs/iris_client.log 2>&1 &"

    sleep 3

    if ssh $IRIS_HOST "ps aux | grep -v grep | grep client.py" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ IRIS client restarted successfully${NC}"
    else
        echo -e "${RED}❌ Failed to restart IRIS client${NC}"
        return 1
    fi
}

# Function to run backfill on Dell
run_backfill() {
    echo -e "\n${YELLOW}Running backfill on Dell...${NC}"

    cd $DELL_HOME

    # Calculate date range (last 3 days)
    START_DATE=$(date -d '3 days ago' +%Y-%m-%d)
    END_DATE=$(date +%Y-%m-%d)

    echo "   Period: ${START_DATE} to ${END_DATE}"

    # Run backfill
    python3 backfill_missing_dec19_20.py

    # Run price derivation
    python3 derive_boalf_prices.py --start $START_DATE --end $END_DATE

    echo -e "${GREEN}✅ Backfill complete${NC}"
}

# Main menu
show_menu() {
    echo ""
    echo "Commands:"
    echo "  1) Full health check"
    echo "  2) Check IRIS server only"
    echo "  3) Check Dell resources"
    echo "  4) Check BigQuery status"
    echo "  5) Restart IRIS server"
    echo "  6) Offload IRIS to Dell"
    echo "  7) Run backfill on Dell"
    echo "  8) View IRIS logs"
    echo "  9) Emergency: Full failover to Dell"
    echo "  q) Quit"
    echo ""
}

# Main execution
case "${1:-menu}" in
    health|1)
        check_iris_health
        check_dell_resources
        check_bigquery_status
        ;;
    iris|2)
        check_iris_health
        ;;
    dell|3)
        check_dell_resources
        ;;
    bigquery|4)
        check_bigquery_status
        ;;
    restart|5)
        restart_iris_server
        ;;
    offload|6)
        offload_to_dell
        ;;
    backfill|7)
        run_backfill
        ;;
    logs|8)
        echo "IRIS Server logs:"
        ssh $IRIS_HOST "tail -50 ${IRIS_PATH}/logs/iris_client.log"
        ;;
    failover|9)
        echo -e "${RED}EMERGENCY FAILOVER TO DELL${NC}"
        check_iris_health || true
        offload_to_dell
        check_bigquery_status
        ;;
    menu)
        show_menu
        ;;
    *)
        echo "Usage: $0 {health|iris|dell|bigquery|restart|offload|backfill|logs|failover|menu}"
        exit 1
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════════"
