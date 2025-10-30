# 🧠 CLAUDE.md — Energy Dashboard v1.0  
**Maintainer:** George Major (Upowerenergy)  
**Last Updated:** 28 Oct 2025  

---

## 📘 Overview
This file provides persistent context for **Claude Code** within the *Energy Dashboard* repository.  
It defines all technical, workflow, and behavioral parameters for maintaining, expanding, and automating the UK energy data dashboard ecosystem.

---

## ⚙️ System Context

| Layer | Technology | Notes |
|-------|-------------|-------|
| **Frontend** | Google Sheets Dashboard | Interactive charts, KPIs, and dropdown filters |
| **Middleware** | Google Apps Script | Data processing, triggers, and visual updates |
| **Backend** | BigQuery (`jibber-jabber-knowledge.uk_energy_insights`) | Master dataset (Elexon + NESO) |
| **Automation** | Python (`gpt_tools.py`) | Fetches BigQuery data, processes it, and updates dashboard |
| **Storage** | Google Drive | Stores raw data, processed outputs, and metadata logs |
| **Scheduler** | Cron & Google Time Triggers | Nightly data refresh and summary generation |

Default region: `europe-west2`  
Date format: `DD/MM/YYYY`  
Currency: `GBP (£)`

---

## 🗂️ File Structure

```
/energy-dashboard/
│
├── gpt_tools.py
├── apps_script/
│   ├── Code.gs
│   ├── System Calculations DNUoS.gs
│   └── UI.gs
│
├── data/
│   ├── queries/
│   ├── outputs/
│   └── schema/
│
├── dashboards/
│   ├── Dashboard_Main.gsheets
│   └── Chart_Templates/
│
└── docs/
    └── CLAUDE.md  ← (this file)
```

---

## 🧩 Linked Resources

### BigQuery Tables
- `elexon_demand_outturn`  
- `elexon_generation_outturn`  
- `elexon_market_index`  
- `elexon_bid_offer_acceptances`  
- `neso_balancing_services`  
- `elexon_frequency`

### Google Drive Folders
- **Primary Workspace:** [Energy Dashboard Workspace](https://drive.google.com/drive/folders/13n_7C-2TMxBnRlqNiucdyFvcV2B6D0GI)  
- **Data Index:** [Energy Jibber Jabber Big Dig Index](https://docs.google.com/spreadsheets/d/1A10-Qhqp9FZng0cv5Il68TrP3R3RNb1Ihdm2bfVY9c4/edit)  
- **Converted Sheets:** [Processed Output Folder](https://drive.google.com/drive/folders/1CK6baEkzEol1m-X-6mSLpes554M0T0Jt)

---

## 🧮 Core Workflow

### 1. **Data Pipeline**
- Python (`gpt_tools.py`) queries BigQuery and formats outputs.  
- Results saved to `/data/outputs/` or directly to Google Sheets.  

### 2. **Sheet Synchronization**
- Apps Script imports data into `Processed Data` tab.  
- Triggers update KPI metrics and generate fresh charts.

### 3. **Charge Calculations**
- Unified charge calculator in `Code.gs` computes:  
  - DUoS, BSUoS, TNUoS  
  - FiT, RO, CfD, ECO, WHD, AAHEDC  
- Outputs stored in Dashboard and Logs tabs.

### 4. **Automation**
- Nightly refresh (22:00 GMT) updates all sources.  
- Trigger chain:
  - `refreshBigQueryData()`
  - `updateChartsAndKPIs()`
  - `sendSummaryToDocs()`

---

## 🧠 Claude Usage Rules

1. Prioritize the UK energy context (Elexon, NESO, Ofgem).  
2. Keep responses **concise, technical, and schema-accurate**.  
3. Do **not** regenerate sensitive logic or authentication files.  
4. When generating SQL, target `uk_energy_insights.*` tables.  
5. Maintain strict format standards:
   - Dates: `DD/MM/YYYY`
   - Currency: `£`
   - Numbers: 2 decimal places
6. When updating documentation, maintain this file’s structure.

---

## 🚫 Restricted Areas
Do **not modify or overwrite:**
- `Service Account Keys`  
- `DUoS Charges` static tables  
- `BigQuery schema`  
- `Drive folder IDs`  
- Trigger configurations  

---

## 🧾 Example Prompts

```
“Summarize BSUoS volatility for the past 14 days.”
“Run DUoS + BSUoS + TNUoS cost analysis for current date range.”
“Generate a demand and price correlation chart.”
“Refresh BigQuery → Sheets → Dashboard pipeline.”
```

---

## 🧭 Version History

| Version | Date | Summary |
|----------|------|----------|
| v1.0 | 28 Oct 2025 | Initial release linked to BigQuery + Drive |
| v1.1 (planned) | Nov 2025 | Add carbon intensity + forecast module |

---

✅ **Ready for Claude Code Context Loading**  
This file provides a complete and safe operating context for Claude within the Energy Dashboard workspace.  
