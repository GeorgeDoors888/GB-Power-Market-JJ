#!/bin/bash
# Screen Session Manager - Manage long-running processes

ACTION=$1
SESSION=$2

case "$ACTION" in
    start)
        case "$SESSION" in
            iris-client)
                screen -dmS iris-client bash -c "cd /opt/iris-pipeline/scripts && export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json && python3 client.py 2>&1 | tee -a /opt/iris-pipeline/logs/client/screen.log"
                echo "✅ Started iris-client in screen"
                ;;
            iris-uploader)
                screen -dmS iris-uploader bash -c "cd /opt/iris-pipeline/scripts && export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json && python3 iris_to_bigquery_unified.py --continuous 2>&1 | tee -a /opt/iris-pipeline/logs/uploader/screen.log"
                echo "✅ Started iris-uploader in screen"
                ;;
            dashboard)
                screen -dmS dashboard bash -c "cd /home/george/GB-Power-Market-JJ && export GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json && python3 realtime_dashboard_updater.py 2>&1 | tee -a logs/dashboard/screen.log"
                echo "✅ Started dashboard in screen"
                ;;
            bigquery-audit)
                screen -dmS bigquery-audit bash -c "cd /home/george/GB-Power-Market-JJ && export GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json && python3 DATA_COMPREHENSIVE_AUDIT_DEC20_2025.py 2>&1 | tee logs/queries/audit_$(date +%Y%m%d_%H%M%S).log"
                echo "✅ Started bigquery-audit in screen"
                ;;
            *)
                echo "Unknown session: $SESSION"
                echo "Available: iris-client, iris-uploader, dashboard, bigquery-audit"
                exit 1
                ;;
        esac
        ;;
    
    list)
        echo "Active screen sessions:"
        screen -ls
        ;;
    
    attach)
        if [ -z "$SESSION" ]; then
            echo "Usage: $0 attach <session-name>"
            exit 1
        fi
        screen -r "$SESSION"
        ;;
    
    stop)
        if [ -z "$SESSION" ]; then
            echo "Usage: $0 stop <session-name>"
            exit 1
        fi
        screen -S "$SESSION" -X quit
        echo "✅ Stopped $SESSION"
        ;;
    
    stopall)
        for sess in iris-client iris-uploader dashboard bigquery-audit; do
            screen -S "$sess" -X quit 2>/dev/null && echo "Stopped $sess" || true
        done
        echo "✅ All sessions stopped"
        ;;
    
    restart)
        if [ -z "$SESSION" ]; then
            echo "Usage: $0 restart <session-name>"
            exit 1
        fi
        $0 stop "$SESSION"
        sleep 2
        $0 start "$SESSION"
        ;;
    
    *)
        echo "GB Power Market - Screen Session Manager"
        echo "========================================"
        echo "Usage: $0 <action> [session-name]"
        echo ""
        echo "Actions:"
        echo "  start <session>   - Start a screen session"
        echo "  stop <session>    - Stop a screen session"
        echo "  stopall           - Stop all sessions"
        echo "  restart <session> - Restart a session"
        echo "  list              - List active sessions"
        echo "  attach <session>  - Attach to session (Ctrl-A D to detach)"
        echo ""
        echo "Sessions:"
        echo "  iris-client       - IRIS Azure downloader"
        echo "  iris-uploader     - BigQuery uploader"
        echo "  dashboard         - Dashboard auto-updater"
        echo "  bigquery-audit    - Run data audit"
        echo ""
        echo "Examples:"
        echo "  $0 start iris-client"
        echo "  $0 list"
        echo "  $0 attach iris-client"
        echo "  $0 stop dashboard"
        exit 1
        ;;
esac
