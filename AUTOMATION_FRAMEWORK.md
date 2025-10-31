# Automation Framework - GB Power Market Analysis

**Date**: 31 October 2025  
**Purpose**: Comprehensive automation strategy for dashboards, reports, and data pipelines

---

## 📋 Automation Capabilities Matrix

| Area | Automation | Script Type | Status | Priority |
|------|-----------|-------------|--------|----------|
| **Data Import** | Pull live data from APIs (Elexon, NESO, Ofgem) | Python | ✅ Partial | HIGH |
| **Chart Generation** | Auto-create charts from analysis data | Python | 🆕 Ready | HIGH |
| **Formatting** | Auto-format, color, freeze rows | Apps Script | ⏭️ Planned | MEDIUM |
| **Chart Refresh** | Auto-update charts on trigger | Apps Script | ⏭️ Planned | MEDIUM |
| **Dropdown Filters** | Interactive dashboard controls | Apps Script | ✅ Implemented | HIGH |
| **BigQuery Integration** | Query and write to Sheets | Python | ✅ Active | HIGH |
| **Scheduled Reports** | Email PDFs of dashboards | Apps Script | ⏭️ Planned | MEDIUM |
| **Logging** | Track API usage, errors | Both | ⚠️ Basic | LOW |
| **Data Analysis** | Z-score, regression, classification | Python | ✅ Active | HIGH |
| **File Automation** | Upload charts/files to Drive | Python | 🆕 Ready | MEDIUM |
| **Doc Generation** | Auto-generate reports | Python | ✅ Complete | HIGH |

---

## 🚀 Quick Start - Chart Automation

### Prerequisites
```bash
# Ensure credentials are fresh
python refresh_token.py

# Verify Sheets API access
python -c "from googleapiclient.discovery import build; print('✅ Ready')"
```

### Create Charts Automatically
```bash
# Generate charts from current data
python create_automated_charts.py
```

### Expected Output
```
📊 Creating: Bid-Offer Spread Trend (LINE)
   ✅ Bid-Offer Spread Trend created
📊 Creating: Generation Mix Distribution (PIE)
   ✅ Generation Mix Distribution created
📊 Creating: Intraday Spread Pattern (COLUMN)
   ✅ Intraday Spread Pattern created
📊 Creating: Demand Profile (AREA)
   ✅ Demand Profile created

✅ Charts created: 4
```

---

## 📊 Chart Types Available

### 1. Line Charts
**Use Case**: Time series data (spreads, prices, demand)

**Configuration**:
```python
{
    "type": "LINE",
    "data_range": {
        "dates": {"startRow": 10, "endRow": 100, "startCol": 0},
        "values": {"startRow": 10, "endRow": 100, "startCol": 1}
    },
    "axes": {
        "bottom": "Date",
        "left": "Value (£/MWh)"
    }
}
```

**Best For**: Trends, forecasts, moving averages

### 2. Pie Charts
**Use Case**: Composition analysis (generation mix, market share)

**Configuration**:
```python
{
    "type": "PIE",
    "data_range": {
        "labels": {"startRow": 10, "endRow": 30, "startCol": 0},
        "values": {"startRow": 10, "endRow": 30, "startCol": 1}
    }
}
```

**Best For**: Fuel mix, market segments, percentage breakdowns

### 3. Column Charts
**Use Case**: Categorical comparisons (settlement periods, monthly averages)

**Configuration**:
```python
{
    "type": "COLUMN",
    "data_range": {
        "categories": {"startRow": 10, "endRow": 58, "startCol": 0},
        "values": {"startRow": 10, "endRow": 58, "startCol": 1}
    }
}
```

**Best For**: Intraday patterns, seasonal comparisons, rankings

### 4. Area Charts
**Use Case**: Volume data (demand, generation capacity)

**Configuration**:
```python
{
    "type": "AREA",
    "data_range": {
        "time": {"startRow": 10, "endRow": 100, "startCol": 0},
        "values": {"startRow": 10, "endRow": 100, "startCol": 1}
    }
}
```

**Best For**: Demand profiles, stacked generation, cumulative totals

### 5. Scatter Charts
**Use Case**: Correlation analysis (price vs demand)

**Configuration**:
```python
{
    "type": "SCATTER",
    "data_range": {
        "x_values": {"startRow": 10, "endRow": 100, "startCol": 0},
        "y_values": {"startRow": 10, "endRow": 100, "startCol": 1}
    }
}
```

**Best For**: Correlation studies, regression analysis

### 6. Combo Charts
**Use Case**: Multiple series with different scales

**Configuration**:
```python
{
    "type": "COMBO",
    "series": [
        {"type": "LINE", "axis": "LEFT"},
        {"type": "COLUMN", "axis": "RIGHT"}
    ]
}
```

**Best For**: Price + volume, spread + demand

---

## 🔄 Automation Workflows

### Workflow 1: Daily Dashboard Update
**Frequency**: Every day at 6:00 AM  
**Steps**:
1. Python: Fetch latest data from BigQuery
2. Python: Update Google Sheets with new data
3. Apps Script: Refresh charts (on edit trigger)
4. Apps Script: Send email notification

**Implementation**:
```bash
# Cron job
0 6 * * * cd ~/GB\ Power\ Market\ JJ && python update_analysis_bi_enhanced.py
```

### Workflow 2: Weekly Report Generation
**Frequency**: Every Monday at 8:00 AM  
**Steps**:
1. Python: Run statistical analysis
2. Python: Generate Google Docs report
3. Python: Create charts
4. Apps Script: Email PDF to stakeholders

**Implementation**:
```bash
# Cron job
0 8 * * 1 cd ~/GB\ Power\ Market\ JJ && ./generate_weekly_report.sh
```

### Workflow 3: Real-Time Alert System
**Frequency**: Continuous monitoring  
**Steps**:
1. Python: Check for extreme values (spreads >£200/MWh)
2. Python: Log to tracking sheet
3. Apps Script: Send instant email/SMS alert

**Trigger**: Data threshold exceeded

### Workflow 4: Monthly Comprehensive Report
**Frequency**: 1st of month at 9:00 AM  
**Steps**:
1. Python: Run enhanced 22-month analysis
2. Python: Generate Google Docs report with all sections
3. Python: Create 10+ charts automatically
4. Python: Upload to Drive folder
5. Apps Script: Email to distribution list

---

## 🐍 Python Automation Scripts

### Current Scripts (✅ Ready)

#### 1. create_automated_charts.py
**Purpose**: Automatically generate charts in Google Sheets  
**Charts**: Line, Pie, Column, Area  
**Status**: ✅ Ready to use

**Usage**:
```bash
python create_automated_charts.py
```

#### 2. generate_google_docs_report_simple.py
**Purpose**: Generate comprehensive analysis report  
**Output**: Google Docs with 5 sections  
**Status**: ✅ Production ready

**Usage**:
```bash
python generate_google_docs_report_simple.py
```

#### 3. update_analysis_bi_enhanced.py
**Purpose**: Refresh dashboard data from BigQuery  
**Target**: Analysis BI Enhanced sheet  
**Status**: ✅ Active

**Usage**:
```bash
python update_analysis_bi_enhanced.py
```

#### 4. enhanced_statistical_analysis.py
**Purpose**: Run comprehensive 22-month analysis  
**Output**: Statistical results + CSV export  
**Status**: ✅ Production ready

**Usage**:
```bash
python enhanced_statistical_analysis.py
```

### Planned Scripts (⏭️ To Create)

#### 5. schedule_email_reports.py
**Purpose**: Email dashboard PDFs to stakeholders  
**Features**:
- Export sheets as PDF
- Attach to email
- Distribution list management
- Scheduling via cron

#### 6. realtime_alert_monitor.py
**Purpose**: Monitor for extreme market conditions  
**Triggers**:
- Spreads >£200/MWh
- Frequency <49.8 Hz
- Demand spikes >40 GW
**Action**: Instant email/SMS alert

#### 7. automated_data_quality.py
**Purpose**: Validate data integrity  
**Checks**:
- Missing values detection
- Outlier identification
- Date range verification
- Schema validation

#### 8. batch_chart_updater.py
**Purpose**: Refresh all charts with latest data  
**Features**:
- Update existing charts (don't recreate)
- Adjust ranges automatically
- Maintain formatting

---

## 📱 Google Apps Script Automations

### Current Scripts (✅ Implemented)

#### 1. google_sheets_menu.gs
**Purpose**: Custom menu for data refresh  
**Location**: Spreadsheet Tools menu  
**Functions**:
- Refresh Data
- Format Sheet
- Export to PDF

**Status**: ✅ Active

### Planned Scripts (⏭️ To Create)

#### 2. auto_formatter.gs
**Purpose**: Automatic formatting on edit  
**Features**:
- Freeze headers
- Color coding (red/green for positive/negative)
- Number formatting (£, MW, %)
- Conditional formatting rules

**Trigger**: onEdit()

#### 3. chart_auto_refresh.gs
**Purpose**: Update charts when data changes  
**Trigger**: onEdit(), time-based trigger

**Implementation**:
```javascript
function onEdit(e) {
  var range = e.range;
  if (range.getSheet().getName() === "Analysis BI Enhanced") {
    refreshAllCharts();
  }
}

function refreshAllCharts() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  var charts = sheet.getSheets()[0].getCharts();
  
  charts.forEach(function(chart) {
    // Force chart refresh
    sheet.updateChart(chart);
  });
}
```

#### 4. scheduled_pdf_email.gs
**Purpose**: Email PDF reports on schedule  
**Frequency**: Daily, Weekly, Monthly

**Implementation**:
```javascript
function sendDailyReport() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  var pdf = sheet.getAs('application/pdf');
  
  MailApp.sendEmail({
    to: "stakeholders@example.com",
    subject: "GB Power Market Daily Report",
    body: "Attached is today's market analysis.",
    attachments: [pdf]
  });
}
```

**Trigger**: Time-driven (daily at 8:00 AM)

#### 5. data_validation.gs
**Purpose**: Validate data entry and imports  
**Checks**:
- Date format validation
- Numeric range checks
- Required fields populated

#### 6. interactive_filters.gs
**Purpose**: Dynamic dropdown filters  
**Features**:
- Date range selector
- Fuel type filter
- Settlement period filter
- Auto-update dependent cells

---

## 🔗 API Integration Patterns

### Pattern 1: BigQuery → Sheets (Current)
**Flow**: BigQuery → Python → Google Sheets API → Spreadsheet  
**Frequency**: On-demand, scheduled  
**Scripts**: update_analysis_bi_enhanced.py

### Pattern 2: Sheets → Analysis → Docs (New)
**Flow**: Sheets data → Python analysis → Google Docs report  
**Frequency**: Weekly, monthly  
**Scripts**: generate_google_docs_report_simple.py

### Pattern 3: Elexon API → BigQuery → Sheets (Planned)
**Flow**: Elexon BMRS → Python → BigQuery → Sheets  
**Frequency**: Real-time, 15-min intervals  
**Purpose**: Latest market data ingestion

### Pattern 4: Sheets → Email (Planned)
**Flow**: Sheets → Apps Script → Gmail API → Stakeholders  
**Frequency**: Daily, on-trigger  
**Purpose**: Automated reporting

---

## 📊 Chart Data Mapping

### Current Sheet Structure: Analysis BI Enhanced

#### Columns Available:
- **A**: Date/Time (settlementDate)
- **B**: Settlement Period
- **C**: Bid Price (£/MWh)
- **D**: Offer Price (£/MWh)
- **E**: Spread (£/MWh)
- **F**: Fuel Type
- **G**: Generation (MW)
- **H**: System Frequency (Hz)
- **I**: SBP (£/MWh)
- **J**: SSP (£/MWh)

### Chart Mappings:

**Chart 1: Bid-Offer Spread Trend**
- X-axis: Column A (Date)
- Y-axis: Column E (Spread)
- Type: Line chart
- Range: Last 100 rows

**Chart 2: Generation Mix**
- Labels: Column F (Fuel Type)
- Values: Column G (Generation)
- Type: Pie chart
- Range: Aggregated by fuel type

**Chart 3: Intraday Pattern**
- X-axis: Column B (Settlement Period 1-48)
- Y-axis: Column E (Average Spread)
- Type: Column chart
- Range: Aggregated by period

**Chart 4: Price Comparison**
- X-axis: Column A (Date)
- Y-axis: Columns I & J (SBP & SSP)
- Type: Combo chart (2 lines)
- Range: Last 100 rows

**Chart 5: Demand Profile**
- X-axis: Column A (Time)
- Y-axis: Demand column (if added)
- Type: Area chart
- Range: 24 hours

---

## 🔐 Authentication Setup

### OAuth Token (Current Method)
**File**: token.pickle  
**Scopes**:
- spreadsheets
- drive
- documents

**Refresh**:
```bash
python refresh_token.py
```

### Service Account (Alternative)
**File**: service.json  
**Advantages**:
- No user interaction needed
- Better for automation
- No token expiration issues

**Setup**:
1. Create service account in Google Cloud Console
2. Download JSON key
3. Share spreadsheet with service account email
4. Use in scripts:
```python
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    'service.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
```

**Recommendation**: Switch to service account for production automations

---

## 🔔 Alert System Design

### Alert Types

#### 1. Price Alerts
**Trigger**: Spread >£200/MWh or <£50/MWh  
**Action**: Instant email  
**Recipients**: Trading team  
**Data**: Current spread, timestamp, historical context

#### 2. Frequency Alerts
**Trigger**: System frequency <49.8 Hz or >50.2 Hz  
**Action**: SMS + email  
**Recipients**: Operations team  
**Data**: Frequency, timestamp, severity level

#### 3. Data Quality Alerts
**Trigger**: Missing data, API failures, schema changes  
**Action**: Email to tech team  
**Recipients**: Data engineers  
**Data**: Error logs, affected tables, last successful update

#### 4. Performance Alerts
**Trigger**: Query time >60s, API timeout  
**Action**: Log to monitoring sheet  
**Recipients**: Tech team (daily summary)

### Implementation Example
```python
def check_price_alerts(spread_value, timestamp):
    if spread_value > 200:
        send_alert(
            type="HIGH_SPREAD",
            severity="HIGH",
            message=f"Spread alert: £{spread_value}/MWh at {timestamp}",
            recipients=["trading@example.com"]
        )
    elif spread_value < 50:
        send_alert(
            type="LOW_SPREAD",
            severity="MEDIUM",
            message=f"Low spread alert: £{spread_value}/MWh at {timestamp}",
            recipients=["trading@example.com"]
        )
```

---

## 📈 Advanced Automation Ideas

### 1. Machine Learning Integration
**Purpose**: Predict next-day spreads  
**Flow**: Historical data → Python ML model → Forecast → Sheets → Chart  
**Libraries**: scikit-learn, TensorFlow  
**Update**: Daily

### 2. Real-Time Dashboard
**Purpose**: Live updating dashboard (no refresh needed)  
**Technology**: Google Sheets + Apps Script + Web App  
**Update**: Every 30 seconds via IRIS pipeline  
**Display**: Embedded iframe on internal website

### 3. Slack/Teams Integration
**Purpose**: Post daily summaries to team channels  
**Flow**: Python analysis → Slack API → Channel post  
**Frequency**: Daily at 9:00 AM  
**Content**: Key metrics, charts, alerts

### 4. Voice Assistant Integration
**Purpose**: "Alexa, what's today's average spread?"  
**Technology**: AWS Lambda + Alexa Skills Kit  
**Data Source**: BigQuery via API  
**Responses**: Current metrics, forecasts, alerts

### 5. Mobile App Dashboard
**Purpose**: View dashboards on phone  
**Technology**: Google Sheets API + React Native  
**Features**: Real-time data, push notifications, offline mode

---

## 🛠️ Implementation Priorities

### Phase 1: Core Automation (Week 1) ✅
- [x] Chart generation script (create_automated_charts.py)
- [x] Google Docs report generation
- [x] OAuth token refresh utility
- [x] Documentation complete

### Phase 2: Enhanced Charting (Week 2) ⏭️
- [ ] Add combo charts
- [ ] Add scatter plots (correlation analysis)
- [ ] Implement chart updater (vs recreate)
- [ ] Add formatting options (colors, styles)

### Phase 3: Email Automation (Week 3) ⏭️
- [ ] PDF export script
- [ ] Email distribution script
- [ ] Schedule with cron
- [ ] Create stakeholder distribution list

### Phase 4: Apps Script Integration (Week 4) ⏭️
- [ ] Auto-formatting on edit
- [ ] Chart refresh triggers
- [ ] Data validation rules
- [ ] Interactive filters

### Phase 5: Alert System (Week 5) ⏭️
- [ ] Real-time monitoring script
- [ ] Email alert system
- [ ] SMS integration (Twilio)
- [ ] Alert logging

### Phase 6: Advanced Features (Week 6+) ⏭️
- [ ] Machine learning forecasts
- [ ] Slack integration
- [ ] Service account migration
- [ ] Mobile dashboard API

---

## 📚 Related Documentation

- **[GOOGLE_DOCS_REPORT_SUMMARY.md](GOOGLE_DOCS_REPORT_SUMMARY.md)** - Report generation details
- **[ENHANCED_BI_ANALYSIS_README.md](ENHANCED_BI_ANALYSIS_README.md)** - Dashboard guide
- **[PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md)** - System configuration
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Complete index

---

## 🆘 Troubleshooting

### Issue: Charts not appearing
**Solution**: Check data ranges, verify sheet ID, ensure data exists in specified ranges

### Issue: Authentication errors
**Solution**: Run `python refresh_token.py`, check token.pickle exists

### Issue: Charts overlapping
**Solution**: Adjust anchor positions in create_automated_charts.py (change anchor_row/col values)

### Issue: Wrong data in charts
**Solution**: Verify column mappings match your actual sheet structure

---

**Last Updated**: 31 October 2025  
**Status**: Framework documented, Phase 1 complete  
**Next**: Implement Phase 2 (Enhanced Charting)
