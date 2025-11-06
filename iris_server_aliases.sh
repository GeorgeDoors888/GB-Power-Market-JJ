# IRIS Pipeline Server Aliases
# Add to ~/.zshrc for quick access to IRIS server management

# IRIS Server Connection
export IRIS_SERVER="83.136.250.239"
alias iris-ssh="ssh root@$IRIS_SERVER"

# IRIS Service Management
alias iris-status="ssh root@$IRIS_SERVER 'systemctl status iris-pipeline.service --no-pager'"
alias iris-restart="ssh root@$IRIS_SERVER 'systemctl restart iris-pipeline.service' && echo '✅ IRIS service restarted'"
alias iris-stop="ssh root@$IRIS_SERVER 'systemctl stop iris-pipeline.service' && echo '⏹️  IRIS service stopped'"
alias iris-start="ssh root@$IRIS_SERVER 'systemctl start iris-pipeline.service' && echo '▶️  IRIS service started'"

# IRIS Logs
alias iris-logs="ssh root@$IRIS_SERVER 'tail -50 /opt/iris-pipeline/logs/pipeline.log'"
alias iris-logs-live="ssh root@$IRIS_SERVER 'tail -f /opt/iris-pipeline/logs/pipeline.log'"
alias iris-logs-client="ssh root@$IRIS_SERVER 'tail -50 /opt/iris-pipeline/logs/pipeline.log.client'"
alias iris-logs-service="ssh root@$IRIS_SERVER 'tail -50 /opt/iris-pipeline/logs/service.log'"

# IRIS Monitoring
alias iris-files="ssh root@$IRIS_SERVER 'find /opt/iris-pipeline/data -type f | wc -l'"
alias iris-disk="ssh root@$IRIS_SERVER 'df -h /opt/iris-pipeline/'"
alias iris-memory="ssh root@$IRIS_SERVER 'free -h'"
alias iris-processes="ssh root@$IRIS_SERVER 'ps aux | grep -E \"(iris|client.py|iris_to_bigquery)\" | grep -v grep'"

# IRIS Health Check (comprehensive)
alias iris-health="echo '🔍 IRIS Pipeline Health Check' && \
  echo '' && \
  echo '📊 Service Status:' && \
  ssh root@$IRIS_SERVER 'systemctl is-active iris-pipeline.service' && \
  echo '' && \
  echo '📁 Files Pending:' && \
  ssh root@$IRIS_SERVER 'find /opt/iris-pipeline/data -type f 2>/dev/null | wc -l' && \
  echo '' && \
  echo '💾 Disk Usage:' && \
  ssh root@$IRIS_SERVER 'df -h /opt/iris-pipeline/ | tail -1' && \
  echo '' && \
  echo '🧠 Memory:' && \
  ssh root@$IRIS_SERVER 'free -h | grep Mem' && \
  echo '' && \
  echo '📝 Last 5 Log Entries:' && \
  ssh root@$IRIS_SERVER 'tail -5 /opt/iris-pipeline/logs/pipeline.log'"

# BigQuery IRIS Data Checks
alias iris-bq-check="bq ls inner-cinema-476211-u9:uk_energy_prod | grep '_iris'"
alias iris-bq-today="bq query --use_legacy_sql=false \"SELECT DATE(settlementDate) as date, COUNT(*) as rows FROM \\\`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris\\\` WHERE DATE(settlementDate) = CURRENT_DATE() GROUP BY date\""
alias iris-bq-fresh="bq query --use_legacy_sql=false \"SELECT MAX(timestamp) as last_update, TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(timestamp), MINUTE) as minutes_ago FROM \\\`inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris\\\`\""

# All Servers Quick Status
alias servers-status="echo '🖥️  UpCloud Servers Status' && \
  echo '' && \
  echo '1️⃣  Document Indexer (94.237.55.15):' && \
  ssh root@94.237.55.15 'systemctl is-active extraction.service' && \
  echo '' && \
  echo '2️⃣  Power Map (94.237.55.234):' && \
  ssh root@94.237.55.234 'systemctl is-active nginx' && \
  echo '' && \
  echo '3️⃣  IRIS Pipeline (83.136.250.239):' && \
  ssh root@$IRIS_SERVER 'systemctl is-active iris-pipeline.service' && \
  echo '' && \
  echo '✅ All servers checked!'"

# Installation Instructions
# To install these aliases, run:
# cat iris_server_aliases.sh >> ~/.zshrc && source ~/.zshrc
