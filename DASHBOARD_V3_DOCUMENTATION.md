# GB Power Market Dashboard V3 - Technical Documentation

## 1. Overview
The **GB Power Market Dashboard V3** is a real-time analytics interface built in Google Sheets, powered by a BigQuery backend. It provides a comprehensive view of the UK energy market, focusing on Battery Energy Storage Systems (BESS), Virtual Lead Parties (VLP), and general grid health.

The system uses a "Hybrid" architecture:
- **Backend**: Google BigQuery (IRIS Real-time tables).
- **Frontend**: Google Sheets (Visuals, Sparklines, KPIs).
- **Middleware**: Python scripts using `google-cloud-bigquery` and `google-api-python-client`.

---

## 2. Visual Architecture (Graphics & Layout)

The dashboard is designed with a "Card" aesthetic using a light grey background and white content areas.

### A. KPI Strip (Rows 10-15)
A high-impact visual row displaying critical market metrics.
- **Merged Cells**: Value cells (Rows 10-11) and Sparkline cells (Rows 12-15) are merged for visibility.
- **Metrics**:
    - **VLP Revenue**: Average revenue for flexibility providers.
    - **Wholesale Price**: Current market price (£/MWh).
    - **Market Volatility**: Standard deviation of price.
    - **Grid Frequency**: Real-time Hz (target 50.0).
    - **Total Gen**: Live total generation in GW.
- **Sparklines**: 7-day trend lines (Line/Column charts) embedded directly in cells using Google Sheets `=SPARKLINE()` formulas.

### B. Intraday Section (Rows 17-21)
Focused on "Today's" performance (Last 24h).
- **Metrics**: Wind Generation, System Demand, Market Price.
- **Visuals**: Larger sparklines (merged Rows 18-21) showing the intraday profile.
- **Styling**: Distinct header with black text on light grey for separation.

### C. Data Tables
1.  **Fuel Mix (Left Panel)**: Live breakdown of generation sources (Wind, Solar, Nuclear, Gas) with emojis and percentage share.
2.  **Active Outages (Middle Panel)**: List of current plant failures.
    - Includes a **Plant Lookup** to convert BM Unit IDs (e.g., `T_DRAXX-1`) to human-readable names (`Drax Unit 1`).
    - Summarizes **Total GW Unavailable** at the bottom.
3.  **ESO Actions (Bottom Panel)**: Real-time "Market Depth" showing the latest Bids and Offers accepted or placed in the Balancing Mechanism.

---

## 3. Code Structure & Functions

The system relies on two primary Python scripts.

### A. Design Script: `python/apply_dashboard_design.py`
Responsible for the visual layout, formatting, and static formulas.

| Function | Description |
| :--- | :--- |
| `apply_dashboard_design()` | Main orchestrator. Connects to Sheets API and executes batch updates. |
| `build_values_payload()` | Generates the 2D array of text labels, headers, and `=SPARKLINE()` formulas. Defines the grid structure. |
| `build_formatting_requests()` | Constructs the JSON payload for the Sheets API `batchUpdate` method. Handles: <br>• **Merging Cells** (KPIs, Sparklines)<br>• **Column Widths** (Expanded to 160px for graphs)<br>• **Colors** (Orange header, Grey background)<br>• **Borders** (Card outlines) |

### B. Data Population Script: `python/populate_dashboard_tables.py`
Responsible for fetching data from BigQuery and writing it to "Backing Sheets" (hidden sheets that feed the dashboard).

| Function | Source Table | Description |
| :--- | :--- | :--- |
| `load_chart_data()` | `bmrs_bod_iris`, `bmrs_mid_iris` | Aggregates core metrics (Price, Gen, Demand) for the main charts. |
| `load_outages()` | `bmrs_remit_unavailability` | Fetches active outages. Applies `PLANT_LOOKUP` dictionary to map IDs to names. Calculates Total GW lost. |
| `load_eso_actions()` | `bmrs_bod_iris` | Fetches the last 20 Bid-Offer pairs. Shows Market Depth (Price vs Volume). |
| `load_vlp_data()` | `bmrs_boalf_iris` | Estimates revenue for Virtual Lead Parties based on acceptance volumes and spreads. |
| `load_fuel_mix...()` | `bmrs_fuelinst_iris` | Gets the latest generation mix. Calculates `Total Gen (GW)` for the KPI. |
| `load_frequency_data()` | `bmrs_freq_iris` | Fetches high-resolution frequency data (last 60 mins). |
| `load_intraday_data()` | `bmrs_fuelinst_iris`, `bmrs_indo_iris`, `bmrs_mid_iris` | Joins Wind, Demand, and Price data for the current day to feed Intraday Sparklines. |

---

## 4. Key Data Sources (BigQuery)

All data is sourced from the `inner-cinema-476211-u9` project, specifically the `uk_energy_prod` dataset.

- **`bmrs_bod_iris`**: Real-time Bid-Offer Data. Used for ESO Actions and Market Depth.
- **`bmrs_mid_iris`**: Real-time Market Index Data. Used for Wholesale Prices.
- **`bmrs_fuelinst_iris`**: Real-time Fuel Mix (Generation by type).
- **`bmrs_indo_iris`**: Real-time Initial National Demand Outturn (System Demand).
- **`bmrs_remit_unavailability`**: REMIT messages for plant outages.

---

## 5. Next Steps & Roadmap

1.  **Automation**:
    - Deploy `populate_dashboard_tables.py` to a cloud scheduler (e.g., GitHub Actions or Google Cloud Run) to run every 5-15 minutes.
    
2.  **Alerting**:
    - Add a script to check for "Price Spikes" (>£100/MWh) or "Frequency Deviations" (<49.8Hz) and send email/Slack alerts.

3.  **Historical Integration**:
    - Currently, the dashboard focuses on *Live* (IRIS) data. Merging this with the deep historical archive (`bmrs_bod`, `bmrs_mid`) would allow for "Year-on-Year" comparison charts.

4.  **Interactive Elements**:
    - Add Google Sheets "Slicers" or Dropdowns to allow users to filter the ESO Actions table by specific Fuel Type or DNO Region.
