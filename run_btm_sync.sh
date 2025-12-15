#!/bin/bash
# Wrapper script for cron execution
export HOME=/home/george
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games

cd /home/george/GB-Power-Market-JJ

# Run the sync script and log output
echo "Starting sync at $(date)" >> /home/george/GB-Power-Market-JJ/logs/btm_sync.log
/usr/bin/python3 sync_btm_bess_to_sheets.py >> /home/george/GB-Power-Market-JJ/logs/btm_sync.log 2>&1
echo "Finished sync at $(date)" >> /home/george/GB-Power-Market-JJ/logs/btm_sync.log
