# ELEXON IRIS Notification Monitor
Documentation for monitoring and storing ELEXON's Insights Real-Time Information Service (IRIS) notifications

## Overview
This system monitors ELEXON's IRIS service for real-time notifications about the GB electricity system, including power station outages, system warnings, and capacity margins. All notifications are stored in BigQuery for analysis.

## Setup Requirements

### Credentials Required
1. ELEXON IRIS Credentials:
   - Client ID: 5ac22e4f-fcfa-4be8-b513-a6dc767d6312
   - Service Bus namespace: elexon-insights-iris
   - Tenant ID: 4203b7a0-7773-4de5-b830-8b263a20426e
   - Queue name: iris.047b7f5d-7cc1-4f3d-a454-fe188a9f42f3

2. Google Cloud Credentials:
   - Set GOOGLE_APPLICATION_CREDENTIALS environment variable
   - Set GOOGLE_CLOUD_PROJECT environment variable

### Python Dependencies
```bash
pip install azure-servicebus azure-identity google-cloud-bigquery pandas
```

## Usage Instructions

### 1. Live Monitoring
Monitor notifications in real-time:
```bash
python monitor_iris_notifications.py
```

Monitor specific notification types:
```bash
python monitor_iris_notifications.py --notification-types REMIT SYSTEM_WARN
```

### 2. Historical Data Download
Download all notifications for a specific year:
```bash
python monitor_iris_notifications.py --download-year 2025
```

## BigQuery Schema
The notifications are stored in BigQuery with the following schema:

1. timestamp (TIMESTAMP) - When the notification was received
2. notification_id (STRING) - Unique identifier
3. type (STRING) - Notification type (REMIT, SYSTEM_WARN, etc.)
4. status (STRING) - Current status
5. message (STRING) - Full notification message
6. affected_units (REPEATED STRING) - List of affected generating units
7. start_time (TIMESTAMP) - Event start time
8. end_time (TIMESTAMP) - Event end time
9. capacity_affected_mw (FLOAT64) - Amount of capacity affected
10. raw_payload (STRING) - Complete JSON payload

## Example Queries

### 1. Alert Counts by Type
```sql
SELECT
  type,
  COUNT(*) as alert_count
FROM `your-project.uk_energy_insights.bmrs_notifications`
WHERE EXTRACT(YEAR FROM timestamp) = 2025
GROUP BY type
ORDER BY alert_count DESC;
```

### 2. Monthly Capacity Impact
```sql
SELECT
  FORMAT_DATE('%Y-%m', DATE(timestamp)) as month,
  SUM(capacity_affected_mw) as total_affected_capacity
FROM `your-project.uk_energy_insights.bmrs_notifications`
WHERE EXTRACT(YEAR FROM timestamp) = 2025
GROUP BY month
ORDER BY month;
```

### 3. Longest Outages
```sql
SELECT
  notification_id,
  type,
  status,
  message,
  TIMESTAMP_DIFF(end_time, start_time, HOUR) as duration_hours,
  capacity_affected_mw
FROM `your-project.uk_energy_insights.bmrs_notifications`
WHERE EXTRACT(YEAR FROM timestamp) = 2025
  AND start_time IS NOT NULL
  AND end_time IS NOT NULL
ORDER BY duration_hours DESC
LIMIT 10;
```

## Data Retention
- Data is stored in BigQuery, partitioned by day
- Full message content is preserved in raw_payload
- No automatic cleanup is implemented (retain all historical data)

## Alert Types
1. REMIT Messages
   - Power station outages
   - Planned maintenance
   - Capacity changes

2. System Warnings
   - SYSWARN
   - NISM (Notification of Inadequate System Margin)
   - HIST (High Risk of Demand Reduction)
   - DEMMW (Demand Control Imminent)

3. Capacity Margins
   - Current system capacity
   - Expected margins
   - Risk levels

## Troubleshooting
1. If no data appears:
   - Check IRIS_CLIENT_SECRET is set
   - Verify Azure credentials
   - Check BigQuery permissions

2. If notifications aren't storing:
   - Check BigQuery project and dataset exist
   - Verify Google Cloud credentials
   - Check table permissions

## Support
For issues with:
- IRIS connectivity: Contact ELEXON support
- BigQuery storage: Check Google Cloud Console
- Script functionality: Check the GitHub repository

## Future Enhancements
Possible improvements:
1. Add alert notifications (email/Slack)
2. Create automated reports
3. Add visualization dashboards
4. Implement data aggregation
