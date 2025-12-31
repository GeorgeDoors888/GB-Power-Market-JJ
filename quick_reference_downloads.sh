#!/bin/bash
# Quick Reference - Automated Daily Downloads
# Run this script to see all essential commands

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════╗
║           AUTOMATED DAILY DOWNLOADS - QUICK REFERENCE                    ║
║                  P114 + NESO Data Automation                             ║
╚══════════════════════════════════════════════════════════════════════════╝

📅 SCHEDULE
───────────────────────────────────────────────────────────────────────────
  P114 Settlement Data:         Daily at 2:00 AM
  NESO Constraint Costs:        Daily at 3:00 AM

🔍 CHECK STATUS
───────────────────────────────────────────────────────────────────────────
  python3 /home/george/GB-Power-Market-JJ/check_automated_downloads.py

📊 VIEW LOGS (REAL-TIME)
───────────────────────────────────────────────────────────────────────────
  tail -f ~/GB-Power-Market-JJ/logs/p114_daily.log
  tail -f ~/GB-Power-Market-JJ/logs/neso_daily.log
  tail -f ~/GB-Power-Market-JJ/logs/{p114,neso}_daily.log

🧪 MANUAL TEST
───────────────────────────────────────────────────────────────────────────
  python3 ~/GB-Power-Market-JJ/auto_download_p114_daily.py
  python3 ~/GB-Power-Market-JJ/auto_download_neso_daily.py

⚙️  CRON MANAGEMENT
───────────────────────────────────────────────────────────────────────────
  # View installed cron jobs
  crontab -l | grep 'auto_download'

  # Edit cron jobs
  crontab -e

  # Re-install cron jobs
  ~/GB-Power-Market-JJ/install_daily_download_crons.sh

📈 DATA FRESHNESS CHECK
───────────────────────────────────────────────────────────────────────────
  # P114 latest date
  python3 -c "
  from google.cloud import bigquery
  c = bigquery.Client(project='inner-cinema-476211-u9', location='US')
  q = 'SELECT MAX(settlement_date) FROM \`inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi\`'
  print(c.query(q).to_dataframe())
  "

  # NESO table counts
  python3 -c "
  from google.cloud import bigquery
  c = bigquery.Client(project='inner-cinema-476211-u9', location='US')
  for t in ['neso_constraint_breakdown', 'neso_mbss', 'neso_constraint_forecast']:
      try:
          q = f'SELECT COUNT(*) as cnt FROM \`inner-cinema-476211-u9.uk_energy_prod.{t}\`'
          r = c.query(q).to_dataframe()
          print(f'{t}: {r[\"cnt\"][0]:,} rows')
      except: print(f'{t}: Not found')
  "

📂 IMPORTANT FILES
───────────────────────────────────────────────────────────────────────────
  Scripts:
    ~/GB-Power-Market-JJ/auto_download_p114_daily.py
    ~/GB-Power-Market-JJ/auto_download_neso_daily.py
    ~/GB-Power-Market-JJ/check_automated_downloads.py

  Logs:
    ~/GB-Power-Market-JJ/logs/p114_daily.log
    ~/GB-Power-Market-JJ/logs/neso_daily.log

  Documentation:
    ~/GB-Power-Market-JJ/AUTOMATED_DAILY_DOWNLOADS.md
    ~/GB-Power-Market-JJ/DEPLOYMENT_SUMMARY.md

  Crontab Backup:
    ~/GB-Power-Market-JJ/crontab_backup_*.txt

🔧 TROUBLESHOOTING
───────────────────────────────────────────────────────────────────────────
  # Check if cron service is running
  systemctl status crond

  # View system cron logs
  journalctl -u crond -n 50

  # Test BigQuery connection
  python3 -c "from google.cloud import bigquery; bigquery.Client(project='inner-cinema-476211-u9'); print('✅ OK')"

  # Check NESO API
  curl -s "https://api.neso.energy/api/3/action/package_list" | head -20

📖 FULL DOCUMENTATION
───────────────────────────────────────────────────────────────────────────
  cat ~/GB-Power-Market-JJ/AUTOMATED_DAILY_DOWNLOADS.md

🎯 INTEGRATION
───────────────────────────────────────────────────────────────────────────
  # After daily downloads complete, run NGSEA detection:
  python3 ~/GB-Power-Market-JJ/detect_ngsea_statistical.py --start 2025-12-01 --end 2025-12-31

  # Update dashboard with new data:
  python3 ~/GB-Power-Market-JJ/update_analysis_bi_enhanced.py

  # Analyze VLP revenue with latest P114 data:
  python3 ~/GB-Power-Market-JJ/analyze_vlp_bm_revenue.py

╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ FULLY AUTOMATED - No manual downloads needed                         ║
║  📅 Next run: Tomorrow at 2:00 AM (P114) and 3:00 AM (NESO)             ║
╚══════════════════════════════════════════════════════════════════════════╝

EOF
