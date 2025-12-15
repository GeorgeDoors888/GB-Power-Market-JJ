# GB Live Dashboard v2.1 - Technical Documentation

**Date**: December 10, 2025  
**Version**: v2.1 (Frequency Deviation & Constraints Update)  
**Status**: ✅ Production Ready

---

## 🏗️ System Architecture: How It Works

The dashboard operates on a **"Publish-Subscribe"** model to ensure speed and reliability. Instead of the Google Sheet querying raw data tables directly (which is slow and complex), a Python script pre-calculates everything into a single "Publication Table". The Sheet then just reads this one row.

### The Data Flow
1.  **Source Data (BigQuery)**:
    *   **Historical Data**: `bmrs_fuelinst`, `bmrs_mid`, `bmrs_freq`, etc. (Data < Today)
    *   **Real-Time Data (IRIS)**: `bmrs_fuelinst_iris`, `bmrs_mid_iris`, `bmrs_freq_iris` (Data >= Today)
    
2.  **The Aggregator (Python)**:
    *   **Script**: `build_publication_table_current.py`
    *   **Action**: It joins Historical + Real-Time data, handles deduplication, calculates averages, and formats complex arrays (like 48-period intraday profiles).
    *   **Output**: A single table `publication_dashboard_live` containing **one row** with all dashboard data nested in JSON-like arrays.

3.  **The Frontend (Apps Script)**:
    *   **Script**: `src/Data.gs`
    *   **Action**: Fetches that single row from BigQuery.
    *   **Rendering**: `src/Dashboard.gs` and `src/Charts.gs` draw the UI and sparklines.

---

## 🐍 The Backend: Python ETL
**File**: `build_publication_table_current.py`

This script is the "brain" of the operation. It performs several critical tasks:

### 1. Data Unification
It automatically detects the "Cutoff Date" to switch between Historical and IRIS data.
```sql
-- Example Pattern
SELECT * FROM bmrs_fuelinst WHERE date < cutoff
UNION ALL
SELECT * FROM bmrs_fuelinst_iris WHERE date >= cutoff
```

### 2. Intraday Profile Alignment
To ensure charts (Sparklines) always look correct, the script forces all intraday arrays (Price, Wind, Frequency) to have exactly **48 Settlement Periods**.
*   **Missing Data**: If future periods are empty, it inserts a sentinel value (`-999`) or `null`.
*   **Result**: Charts always start at SP 1 (00:00) and fill left-to-right.

### 3. Key Data Sources
*   **Wholesale Price**: Now uses `bmrs_mid` + `bmrs_mid_iris` (Market Index Data) for accurate live pricing.
*   **Frequency**: Uses `bmrs_freq` + `bmrs_freq_iris` to calculate average frequency per settlement period.
*   **Constraints**: Joins `bmrs_boalf` (Bid-Offer Acceptances) with `bmu_registration_data` to map BM Units to Fuel Types and DNO Areas.

---

## 📊 The Frontend: Apps Script & Visualizations
**Project**: `clasp-gb-live-2`

### 1. Frequency Deviation Graph (`src/Charts.gs`)
*   **Goal**: Show grid stability relative to 50Hz.
*   **Logic**: `Deviation = Value - 50`.
*   **Visualization**: A Column Chart Sparkline.
    *   **Green Bars**: Positive deviation (>50Hz).
    *   **Red Bars**: Negative deviation (<50Hz).
    *   **Zero Line**: Explicitly set to show the baseline.
*   **Handling Nulls**: Future periods are set to `0` deviation to prevent formula errors.

### 2. Constraint Analysis Table (`src/Dashboard.gs`)
*   **Location**: Row 55+.
*   **Features**:
    *   **Emojis**: Automatically maps fuel types to icons (🌬️, 🏭, 🔋).
    *   **Visual Bar**: A blue sparkline bar showing the `% Share` of total constraints.
    *   **Safety**: Includes error handling for undefined data rows.

### 3. Robust Sparklines
*   **Problem**: Google Sheets `SPARKLINE` formulas break if given `null` or `NA()` in an array literal.
*   **Solution**: The parser (`src/Data.gs`) converts `-999` (from Python) to `null`. The chart renderer (`src/Charts.gs`) converts `null` to `0` (or empty string) to ensure valid formulas like `=SPARKLINE({10, 20, 0, 0}, ...)`

---

## 🚀 Deployment Guide

### 1. Updating the Backend (Data)
To refresh the data in BigQuery:
```bash
cd ~/GB-Power-Market-JJ
python3 build_publication_table_current.py
```
*This updates the `publication_dashboard_live` table.*

### 2. Updating the Frontend (Code)
To deploy changes to the Apps Script (Script ID: `1b2dOZ...`):
```bash
cd ~/GB-Power-Market-JJ/clasp-gb-live-2
./deploy_gb_live_v2.sh
```
*This safely pushes `src/` files to the correct Google Apps Script project.*

### 3. Viewing the Dashboard
1.  Open the Google Sheet.
2.  Menu: **GB Live Dashboard** > **Force Refresh Dashboard**.
3.  Check the "Last Updated" timestamp in cell A2.

---

## 🛠️ Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| **Wholesale Price is 0** | Using `bmrs_costs` (empty for today) instead of `bmrs_mid`. | Fixed in v2.1. Ensure Python script uses `bmrs_mid_iris`. |
| **Sparklines show #ERROR** | Formula has invalid syntax (e.g. `{1,,2}`). | Fixed in v2.1. Code now replaces nulls with `0`. |
| **Frequency Graph Flat** | Data not parsed correctly. | Check `src/Data.gs` maps `row[13]` correctly. |
| **Constraint Table Empty** | No BOALF actions for today yet. | Wait for market activity or check `bmrs_boalf_iris`. |

