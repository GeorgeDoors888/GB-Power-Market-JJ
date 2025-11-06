# 📚 Documentation Index - GB Power Market JJ

**Last Updated**: 31 October 2025  
**Total Documents**: 26 Markdown files (+ 3 Python scripts)  
**Purpose**: Complete index of all project documentation

**🆕 NEW:** Enhanced statistical analysis with 22-month extended range and corrected intraday patterns!

**📄 NEW:** Comprehensive Google Docs report with 5 sections + strategic recommendations!

---

## 🎯 Quick Navigation

### 🚀 Latest Updates (6 Nov 2025)
0. **[AUTO_REFRESH_COMPLETE.md](#auto-refresh-complete)** - 🔄 **Self-refreshing BigQuery pipeline** (NEW!)
1. **[GITHUB_ACTIONS_SETUP.md](#github-actions-setup)** - 🤖 **GitHub Actions auto-deploy guide** (NEW!)
2. **[STOP_DATA_ARCHITECTURE_REFERENCE.md](#stop-architecture)** - ⚠️ **READ FIRST** to stop repeating data issues
3. **[GOOGLE_DOCS_REPORT_SUMMARY.md](#google-docs-report)** - 📄 **22-Month Analysis Report**
4. **[SESSION_SUMMARY_31_OCT_2025.md](#session-summary)** - 📋 Complete session summary
5. **[ENHANCED_ANALYSIS_RESULTS.md](#enhanced-analysis-results)** - ⭐ 22-month analysis results
6. **[CLOCK_CHANGE_ANALYSIS_NOTE.md](#clock-change-note)** - ⚠️ Settlement Period 50 correction
7. **Enhanced Scripts** - `enhanced_statistical_analysis.py`, `check_table_coverage.sh`, `generate_google_docs_report_simple.py`

### 🆕 START HERE: Analysis Ready!
1. **[QUICK_START_ANALYSIS.md](#quick-start-analysis)** - ⚡ Copy-paste commands to run analysis NOW
2. **[CODE_REVIEW_SUMMARY.md](#code-review-summary)** - Complete code review & function guide

### For New Users
1. **[README.md](#readme)** - Project overview and quick start
2. **[PROJECT_IDS.md](#project-ids)** - ⚠️ **CRITICAL:** Google Cloud project IDs (BigQuery vs Sheets)
3. **[PROJECT_CONFIGURATION.md](#project-configuration)** - Essential configuration reference
4. **[UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](#unified-architecture)** - System architecture

### For Development
- **[AUTO_REFRESH_COMPLETE.md](#auto-refresh-complete)** - 🔄 Self-refreshing BigQuery analysis (NEW!)
- **[GITHUB_ACTIONS_SETUP.md](#github-actions-setup)** - GitHub Actions deployment guide (NEW!)
- **[PROJECT_CONFIGURATION.md](#project-configuration)** - BigQuery settings, schemas, templates
- **[SCHEMA_FIX_SUMMARY.md](#schema-fix-summary)** - Schema troubleshooting
- **[CODE_REVIEW_SUMMARY.md](#code-review-summary)** - All analysis functions documented
- **[drive-bq-indexer/API.md](drive-bq-indexer/API.md)** - 🔌 FastAPI endpoints & BigQuery repository details

### For Analysis
- **[QUICK_START_ANALYSIS.md](#quick-start-analysis)** - ⚡ Instant analysis commands
- **[STATISTICAL_ANALYSIS_GUIDE.md](#statistical-analysis-guide)** - Statistical outputs explained
- **[ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)** - Dashboard guide

### For Troubleshooting
- **[DOCUMENTATION_IMPROVEMENT_SUMMARY.md](#documentation-improvement-summary)** - Common issues resolved
- **[SIMPLE_REFRESH_SOLUTIONS.md](#simple-refresh-solutions)** - Dashboard refresh methods

---

## 📖 Core Documentation (Essential Reading)

### STOP_DATA_ARCHITECTURE_REFERENCE.md {#stop-architecture}
**Category**: ⚠️ **CRITICAL - Read First**  
**Status**: ✅ Active - Prevents Recurring Issues  
**Date**: October 31, 2025  
**Size**: 500+ lines

**Summary**:  
**THE SOLUTION to recurring data format/table confusion.** Created after repeatedly discovering that historical and real-time data have different formats, date ranges, and data types. This document exists to STOP wasting time rediscovering these issues.

**Key Content**:
- **Golden Rules**: Check table coverage FIRST, Know your two architectures, Use UNION patterns
- **Table Coverage Matrix**: Which tables have which date ranges (e.g., demand_outturn: only 29 days!)
- **Data Type Fixes**: How to handle DATETIME vs STRING (Cast to DATE)
- **Common Mistakes**: Don't repeat these! (with before/after examples)
- **Pre-Query Checklist**: 6-step checklist to use every time
- **Decision Tree**: Flowchart for choosing right approach
- **Quick Reference Card**: Print and keep visible
- **Why We Keep Repeating**: Root causes identified
- **New Workflow**: Follow this to stop repeating mistakes

**Critical Findings**:
- `bmrs_bod`: 667 days (2024-01-01 to 2025-10-28) - DATETIME ✅
- `demand_outturn`: 29 days (2025-09-27 to 2025-10-25) - STRING ⚠️
- Cannot join DATETIME and STRING directly → Cast to DATE
- Historical tables: `bmrs_*` (full history)
- Real-time tables: `bmrs_*_iris` (recent only)

**Utility Tool**:
- `check_table_coverage.sh TABLE_NAME` - Automatically check date ranges

**When to Use**: **BEFORE WRITING ANY NEW QUERY OR SCRIPT** - This prevents hours of debugging

**Related**: [UNIFIED_ARCHITECTURE](#unified-architecture), [PROJECT_CONFIGURATION](#project-configuration), [PRICE_DEMAND_CORRELATION_FIX](#price-demand-fix)

---

### README.md {#readme}
**Category**: 🏠 Main Entry Point  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Main project README with quick start guide, system overview, and documentation navigation. Perfect starting point for new users.

**Key Content**:
- Quick start verification commands
- Documentation reading order
- System overview (Two pipelines: Historical + IRIS)
- Common tasks with copy-paste commands
- Configuration quick reference table
- Installation instructions

**When to Use**: First time setting up project, need overview of entire system

**Related**: [PROJECT_CONFIGURATION.md](#project-configuration), [UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](#unified-architecture)

---

### PROJECT_CONFIGURATION.md {#project-configuration}
**Category**: 🔧 Configuration Master  
**Status**: ✅ Active (Single Source of Truth)  
**Date**: October 31, 2025  
**Size**: 500+ lines

**Summary**:  
Comprehensive configuration reference containing ALL critical settings. Created to prevent configuration errors like wrong region, project ID, or table names.

**Key Content**:
- Quick reference card (project, region, dataset)
- BigQuery configuration (inner-cinema-476211-u9, US region)
- Complete table schemas (bmrs_bod, bmrs_freq with correct columns)
- Python environment setup
- 3 script templates (BigQuery, Google Sheets, UNION queries)
- 7 common pitfalls with ❌/✅ examples
- 8-point pre-flight checklist

**Critical Settings**:
- Project: `inner-cinema-476211-u9` (NOT jibber-jabber-knowledge)
- Region: `US` (NOT europe-west2)
- Python: `python3` (NOT python)
- Tables: `bmrs_*` (NOT elexon_*)

**When to Use**: Before creating any new script, troubleshooting configuration errors

**Related**: [README.md](#readme), [PROJECT_IDS.md](#project-ids), [DOCUMENTATION_IMPROVEMENT_SUMMARY.md](#documentation-improvement-summary)

---

### AUTO_REFRESH_COMPLETE.md {#auto-refresh-complete}
**Category**: 🔄 **Self-Refreshing Pipeline**  
**Status**: ✅ Active - Production Ready  
**Date**: November 6, 2025  
**Size**: 350+ lines

**Summary**:  
Complete guide to making your BigQuery analysis "always live" through GitHub Actions, Cloud Run, and Cloud Scheduler. Runs automatically daily at 04:00 London time with zero manual intervention.

**Key Content**:
- 5-step quick start (create service accounts → deploy → done)
- Auto-authentication explanation (no JSON keys stored)
- Mobile triggering methods (GitHub app, Cloud Console app, iOS Shortcut)
- Monitoring & debugging commands
- Cost breakdown (~£1-3/month)
- Extension options (Drive, Sheets, email reports)

**Services Used**:
- Cloud Run: Hosts containerized Python + BigQuery client
- Cloud Scheduler: Daily 04:00 trigger with retry logic
- Workload Identity Federation: Secure GitHub → GCP auth
- BigQuery: Queries via Application Default Credentials (auto)

**When to Use**: Want to deploy analysis that runs automatically, need always-fresh data, working on mobile

**Related**: [GITHUB_ACTIONS_SETUP.md](#github-actions-setup), [API.md](drive-bq-indexer/API.md), [PROJECT_IDS.md](#project-ids)

---

### GITHUB_ACTIONS_SETUP.md {#github-actions-setup}
**Category**: 🤖 **CI/CD & Automation**  
**Status**: ✅ Active - Step-by-Step Guide  
**Date**: November 6, 2025  
**Size**: 450+ lines

**Summary**:  
Detailed technical guide for configuring GitHub Actions to build, deploy, and schedule your BigQuery analysis pipeline. Includes all gcloud commands, secret configuration, and troubleshooting.

**Key Content**:
- Workload Identity Federation setup (OIDC tokens)
- Service account creation & IAM permissions
- GitHub Secrets configuration (6 required secrets)
- Dockerfile and requirements.txt templates
- Cloud Run deployment parameters
- Cloud Scheduler JSON configuration
- Monitoring & logging commands
- Common error resolutions

**Files Created by Workflow**:
- `.github/workflows/deploy-cloudrun.yml` (GitHub Actions YAML)
- `cloudscheduler_job.json` (Scheduler configuration)
- `Dockerfile` (Container definition)
- `requirements.txt` (Python dependencies - already exists)

**When to Use**: Setting up automated deployment, troubleshooting GitHub Actions failures, understanding auth flow

**Related**: [AUTO_REFRESH_COMPLETE.md](#auto-refresh-complete), [PROJECT_CONFIGURATION.md](#project-configuration)

---

### PROJECT_IDS.md {#project-ids}
**Category**: ⚠️ **CRITICAL REFERENCE**  
**Status**: ✅ Active - Canonical Source  
**Date**: November 5, 2025  
**Size**: 200+ lines

**Summary**:  
**THE DEFINITIVE GUIDE** to Google Cloud project IDs. Created to permanently solve confusion between `inner-cinema-476211-u9` (BigQuery) and `jibber-jabber-knowledge` (Sheets/Apps Script).

**Key Content**:
- Two separate projects clearly defined
- Decision guide: "When should I use X?"
- Common mistakes with ❌/✅ examples
- Service accounts summary table
- Configuration file examples
- Quick links to both project consoles

**Critical Rules**:
- **BigQuery operations:** ALWAYS use `inner-cinema-476211-u9`
- **Apps Script/Sheets:** ALWAYS use `jibber-jabber-knowledge`
- **Never mix these up!**

**Service Accounts**:
- `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com` - BigQuery access
- `jibber-jabber-knowledge@appspot.gserviceaccount.com` - Sheets/Drive access

**When to Use**: Before enabling APIs, setting up service accounts, configuring Apps Script, or any time you're unsure which project to use

**Related**: [PROJECT_CONFIGURATION.md](#project-configuration), [ENABLE_APPS_SCRIPT_API.md](#enable-apps-script-api), [APPS_SCRIPT_API_GUIDE.md](#apps-script-api-guide)

---

### UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md {#unified-architecture}
**Category**: 🏗️ System Architecture  
**Status**: ✅ Active  
**Date**: October 30, 2025  
**Size**: 501 lines

**Summary**:  
Master architecture document describing the Two-Pipeline design (Historical + Real-Time IRIS) that powers the entire system.

**Key Content**:
- Executive summary (two complementary pipelines)
- Architecture diagrams (data flow)
- Historical Pipeline: Elexon API → BigQuery (174 tables, 391M+ rows)
- Real-Time Pipeline: Azure Service Bus (IRIS) → BigQuery (8+ tables)
- Table naming conventions (bmrs_* vs bmrs_*_iris)
- UNION query patterns for combined timelines
- System status (Historical ✅, IRIS 🟢)
- Future roadmap (Phase 2: unified views)

**When to Use**: Understanding system design, planning new features, architectural decisions

**Related**: [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme), [PROJECT_CONFIGURATION.md](#project-configuration), **[drive-bq-indexer/API.md](drive-bq-indexer/API.md)** - BigQuery data repository & API integration details

---

### GOOGLE_DOCS_REPORT_SUMMARY.md {#google-docs-report}
**Category**: 📄 Analysis Report  
**Status**: ✅ Complete  
**Date**: 31 October 2025  
**Size**: 500+ lines

**Summary**:  
Comprehensive documentation of the 22-month GB Power Market Analysis Report generated as a Google Docs document. Contains all statistical findings, strategic recommendations, and technical methodology from the enhanced analysis.

**Key Content**:
- **Report Access**: Direct link to Google Docs report
- **Executive Summary**: Key findings overview (£126.63/MWh avg spread, 36.1% renewables)
- **5 Main Sections**: 
  1. Bid-Offer Spread Analysis (battery storage arbitrage)
  2. Generation Mix Analysis (16 fuel types, renewable trends)
  3. Demand Pattern Analysis (26,107 MW avg, load factors)
  4. Predictive Trend Analysis (forecasts, scenarios)
  5. Strategic Recommendations (operational strategy, revenue diversification)
- **Technical Appendix**: Data sources, statistical methods, reproducibility
- **Report Metrics**: 27,432 characters, 32,016 settlement periods analyzed
- **Generation Details**: Authentication process, scripts used
- **Next Steps**: How to format, add charts, share report

**Report Contents**:
- Analysis period: January 2024 - October 2025 (22 months)
- Investment case: 50MW/100MWh battery (£555k annual revenue potential)
- Optimal dispatch: Charge 13:00-15:00, Discharge 03:00-05:00
- Market outlook: Upward trend, favorable conditions
- Risk mitigation strategies
- ROI projections: 11-14% IRR, 8-10 year payback

**Scripts Created**:
- `generate_google_docs_report_simple.py` - Main report generator (✅ Working)
- `refresh_token.py` - OAuth token refresh utility (✅ Working)

**When to Use**: Viewing comprehensive analysis findings, sharing results with stakeholders, understanding investment case

**Report URL**: https://docs.google.com/document/d/1S39H_9ZCqdfAUJrbzF-icUkwVMGivSPpbsOegcG4pVU/edit

**Related**: [ENHANCED_ANALYSIS_RESULTS.md](#enhanced-analysis-results), [STATISTICAL_ANALYSIS_GUIDE.md](#statistical-analysis-guide)

---

### ENHANCED_BI_ANALYSIS_README.md {#enhanced-bi-analysis-readme}
**Category**: 📊 Dashboard Implementation  
**Status**: ✅ Active  
**Date**: October 31, 2025  
**Size**: 386 lines

**Summary**:  
Complete guide for the Analysis BI Enhanced Google Sheets dashboard. Documents the 4-section dashboard that combines historical and real-time data.

**Key Content**:
- Dashboard overview (4 sections: Generation, Frequency, Prices, Balancing)
- Data sources (UNION queries combining Historical + IRIS)
- Usage instructions (setup, refresh, analysis)
- Query patterns and examples
- Metrics calculated (renewable %, grid stability, etc.)
- Troubleshooting section
- Future roadmap (Phase 2 unified views)

**Dashboard Sections**:
1. Generation Mix (fuel type breakdown)
2. System Frequency (grid stability monitoring)
3. Market Prices (SBP/SSP with spreads)
4. Balancing Costs (NESO actions)
5. Advanced Calculations (capacity factors, quality scores)

**When to Use**: Using the dashboard, refreshing data, understanding dashboard structure

**Related**: [UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](#unified-architecture), [ENHANCED_BI_SUCCESS.md](#enhanced-bi-success)

---

### STATISTICAL_ANALYSIS_GUIDE.md {#statistical-analysis-guide}
**Category**: 📈 Analytics Guide  
**Status**: ✅ Active  
**Date**: October 31, 2025  
**Size**: 19,000+ words

**Summary**:  
Comprehensive operational guide explaining 9 statistical outputs with business context for battery optimization, solar PV, market modeling, and transmission costs.

**Key Content**:
- Executive summary (use cases for batteries, solar, market)
- 9 detailed analysis sections:
  1. T-test (SSP vs SBP) - Battery arbitrage windows
  2. Temperature regression - Weather-driven scheduling
  3. Multi-factor regression - Price elasticity
  4. Correlation matrix - Variable relationships
  5. ARIMA forecast - 24h SSP prediction
  6. Seasonal decomposition - Trend/pattern/noise
  7. Outage impact - Event stress testing
  8. NESO behavior - Balancing cost linkage
  9. ANOVA - Seasonal pricing regimes
- Each section: What it is, Why it matters, How to read, Pitfalls, 4-5 use cases
- Implementation best practices
- Quick reference card

**When to Use**: Interpreting statistical outputs, planning battery/solar operations, understanding market analysis

**Related**: [advanced_statistical_analysis_enhanced.py script]

---

## 📝 Recent Updates & Improvements

### DOCUMENTATION_IMPROVEMENT_SUMMARY.md {#documentation-improvement-summary}
**Category**: 📋 Process Documentation  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Documents the creation of PROJECT_CONFIGURATION.md and explains how it prevents configuration errors.

**Key Content**:
- Problem statement (5 common configuration errors)
- Solution implemented (centralized configuration)
- Documentation updates made
- Expected benefits (immediate & long-term)
- Usage guidance for new/existing scripts
- Maintenance plan

**When to Use**: Understanding why PROJECT_CONFIGURATION.md was created, learning from past mistakes

**Related**: [PROJECT_CONFIGURATION.md](#project-configuration)

---

### DOCUMENTATION_UPDATE_SUMMARY.md {#documentation-update-summary}
**Category**: 📋 Change Log  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Brief summary of documentation updates to ENHANCED_BI_ANALYSIS_README.md aligning it with actual Two-Pipeline Architecture.

**Key Content**:
- Changes made to README
- Architecture alignment updates

**When to Use**: Tracking documentation changes

**Related**: [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)

---

### SCHEMA_FIX_SUMMARY.md {#schema-fix-summary}
**Category**: 🔧 Technical Fix  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Documents schema issues discovered and fixed on Oct 31, 2025 that prevented advanced calculations from working.

**Key Content**:
- Problem: Advanced calculations showing "No data available"
- Root causes:
  1. bmrs_bod schema different (bid/offer columns vs acceptance columns)
  2. bmrs_freq uses measurementTime (not recordTime)
  3. Missing db-dtypes package
- Solutions implemented (query rewrites, column name fixes)
- Results (balancing stats working, capacity factors calculated)
- Actual BigQuery schemas documented

**When to Use**: Troubleshooting schema issues, understanding table structures

**Related**: [PROJECT_CONFIGURATION.md](#project-configuration)

---

## � Statistical Analysis Documentation (NEW)

### ENHANCED_ANALYSIS_RESULTS.md {#enhanced-analysis-results}
**Category**: 📊 Analysis Results  
**Status**: ⭐ Active - Latest Results  
**Date**: October 31, 2025  
**Size**: 580+ lines

**Summary**:  
Comprehensive results from enhanced statistical analysis covering 22 months (Jan 2024 - Oct 2025) with 32,016 settlement periods analyzed. Key findings for battery storage arbitrage and renewable generation tracking.

**Key Content**:
- **Executive Summary**: £126.63/MWh average spread, 100% profitability, upward trend
- **Bid-Offer Spread Analysis**: 
  - Seasonal patterns (Jan: £141.38, Nov: £112.41)
  - Monthly trends for 12 months
  - Intraday patterns (Peak: 3-5am at £131/MWh)
- **Generation Mix**: 36.1% renewable (Wind 26.8%, on track for 2030)
- **Demand Patterns**: 
  - Weekly (weekends 14% lower)
  - Seasonal (Q4 7.3% higher than Q3)
  - Intraday (Peak 18:30h: 32,672 MW)
- **Predictive Analysis**: 
  - Upward trend (30-day MA > 90-day MA)
  - Lower volatility (more predictable)
- **Strategic Insights**: Battery storage optimization, seasonal strategy, market outlook
- **Investment Case**: ROI indicators, risk assessment

**Critical Findings**:
- 100% of periods profitable for battery storage
- £911.24/MWh max spread observed
- 30% higher spreads in Q1 vs Q4
- Early morning (3-5am) best intraday period

**When to Use**: Understanding market opportunities, planning battery dispatch, investment decisions

**Related**: [CLOCK_CHANGE_ANALYSIS_NOTE.md](#clock-change-note), [STATISTICAL_ANALYSIS_GUIDE.md](#statistical-analysis-guide)

---

### CLOCK_CHANGE_ANALYSIS_NOTE.md {#clock-change-note}
**Category**: ⚠️ Important Correction  
**Status**: ✅ Active - Critical Finding  
**Date**: October 31, 2025  
**Size**: 200+ lines

**Summary**:  
Documents critical correction to intraday pattern analysis. Settlement Periods 49-50 only exist on clock change days (2 days/year), not daily. Initial analysis incorrectly showed "midnight" as peak spread period.

**Key Content**:
- **The Problem**: Period 50 (£153.84 spread) appeared as daily pattern
- **Reality**: Periods 49-50 only occur on Oct clock change days (27 Oct 2024, 26 Oct 2025)
- **Data Verification**: 
  - Period 48: 822,647 occurrences (every day)
  - Period 49: 2,294 occurrences (2 days only)
  - Period 50: 2,126 occurrences (2 days only)
- **UK Clock Change Rules**: 46 periods (spring), 50 periods (autumn)
- **Correction**: Excluded Periods 49-50 from normal intraday analysis
- **Corrected Peak Periods**: 
  - Period 8 (03:30h): £131.59/MWh - every day ✅
  - Period 7 (03:00h): £131.22/MWh - every day ✅
  - NOT Period 50 (midnight) - only 2 days/year ❌

**Trading Implications**:
- ❌ Before: "Target midnight for £153/MWh" (works 2 days/year)
- ✅ After: "Target 3am-5am for £131/MWh" (works 365 days/year)

**Lessons Learned**:
1. Always check data frequency (high averages might be tiny samples)
2. Understand domain specifics (GB market clock change rules)
3. Separate exceptional events from normal patterns
4. Verify assumptions with data

**When to Use**: Understanding intraday patterns, avoiding misleading analysis, validating trading strategies

**Related**: [ENHANCED_ANALYSIS_RESULTS.md](#enhanced-analysis-results)

---

### STATISTICAL_FUNCTIONALITY_FINAL_ANSWER.md {#statistical-functionality}
**Category**: 📈 Analysis Guide  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Comprehensive answer to "what statistical functionality do we have?" - documents all available analysis functions and capabilities.

**Key Content**:
- Overview of statistical analysis capabilities
- Function-by-function breakdown
- Usage examples and code snippets
- Comparison between scripts

**When to Use**: Understanding available analysis tools, choosing right analysis approach

**Related**: [CODE_REVIEW_SUMMARY.md](#code-review-summary), [ANALYSIS_WITH_YOUR_DATA.md](#analysis-with-your-data)

---

### ANALYSIS_WITH_YOUR_DATA.md {#analysis-with-your-data}
**Category**: 📊 Custom Analysis  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Guide for creating custom statistical analysis using actual table structure (bmrs_* tables instead of elexon_* tables).

**Key Content**:
- Custom script creation rationale
- Table name mappings
- Simple analysis examples
- Usage instructions

**When to Use**: Creating new analysis scripts, working with custom data queries

**Related**: [PROJECT_CONFIGURATION.md](#project-configuration), [STATISTICAL_FUNCTIONALITY_FINAL_ANSWER.md](#statistical-functionality)

---

### PRICE_DEMAND_CORRELATION_FIX.md {#price-demand-fix}
**Category**: 🔧 Technical Fix & Learning  
**Status**: ✅ Active - Important Lesson  
**Date**: October 31, 2025  
**Size**: 300+ lines

**Summary**:  
Documents the root cause and fix for price-demand correlation analysis failure. Demonstrates the recurring data format issue this project faces and how to solve it.

**Key Content**:
- **Root Causes**: Data type mismatch (DATETIME vs STRING), Date range mismatch (667 vs 29 days)
- **The Solution**: Cast both to DATE, Limit to overlapping period
- **Results**: Weak negative correlation (-0.128) - low demand = higher spreads!
- **Key Insights**: Counter-intuitive relationship, Demand explains only 1.6% of variance, Time-based patterns are better predictors
- **Why It's Weak**: Market complexity, Multiple factors beyond demand
- **Limitations**: Only 29 days of demand data available
- **Recommendations**: Use time-based patterns (stronger), Don't rely on demand alone
- **Fixed Query**: Complete working SQL with DATE casting

**Critical Finding**:
- Low demand periods (Q1) have **highest spreads** (£145.71/MWh)
- High demand periods (Q4) have lower spreads (£138.32/MWh)
- Confirms 3-5am strategy (low demand = high spread opportunity)

**Technical Details**:
- `bmrs_bod.settlementDate` = DATETIME
- `demand_outturn.settlementDate` = STRING
- Solution: `CAST(settlementDate AS DATE)` for both tables

**When to Use**: Understanding why joins fail, Learning how to handle data type mismatches, Correlation analysis reference

**Related**: [STOP_DATA_ARCHITECTURE_REFERENCE](#stop-architecture), [ENHANCED_ANALYSIS_RESULTS](#enhanced-analysis-results)

---

### SESSION_SUMMARY_31_OCT_2025.md {#session-summary}
**Category**: 📋 Session Summary  
**Status**: ⭐ Complete  
**Date**: October 31, 2025  
**Size**: 600+ lines

**Summary**:  
Comprehensive summary of entire session covering system recovery, code review, statistical analysis execution, and critical discovery/correction of clock change period analysis.

**Key Content**:
- **Session Overview**: What we accomplished (5 major achievements)
- **System Recovery**: Virtual environment recreation, 80+ packages installed
- **Code Review**: 5 scripts reviewed, configuration issues identified and fixed
- **Statistical Analysis**: Two phases (simple + enhanced with 22-month extended range)
- **Critical Discovery**: Settlement Period 50 correction (clock change days)
- **Documentation Updates**: 8 new files created, 1 updated
- **Key Findings**: Battery arbitrage (£126.63/MWh avg), renewable progress (36.1%)
- **Outstanding Items**: 3 minor issues, 6 potential enhancements
- **Lessons Learned**: 4 critical lessons (data validation, domain knowledge, etc.)
- **Files Created**: Complete list of 14 files (5 scripts, 9 docs)
- **Success Metrics**: Quantitative (32,016 periods analyzed) & Qualitative (insights)

**Session Achievements**:
1. ✅ System recovered from crash (virtual environment loss)
2. ✅ All code reviewed and documented (19 functions)
3. ✅ Statistical analysis executed (22 months, 666 days)
4. ✅ Critical correction made (Period 50 clock change)
5. ✅ Comprehensive documentation created (2,500+ lines)

**Key Results**:
- £126.63/MWh average spread (100% profitable)
- £911.24/MWh max spread
- 3-5am optimal for battery dispatch (£131/MWh)
- 36.1% renewable generation (on track for targets)
- Upward trend (favorable market conditions)

**When to Use**: Understanding what happened in this session, quick reference for accomplishments, starting point for next session

**Related**: All other documentation files created this session

---

## 📊 Dashboard Documentation

## �📊 Dashboard Documentation

### ENHANCED_BI_SUCCESS.md {#enhanced-bi-success}
**Category**: ✅ Success Report  
**Status**: ✅ Complete  
**Date**: October 31, 2025

**Summary**:  
Status report showing all 4 sections of Enhanced BI Analysis sheet working with real data.

**Key Content**:
- Generation Mix: 20 fuel types working
- System Frequency: 20 records working
- Market Prices: 20 records working
- Balancing Costs: 20 records working
- Latest metrics (renewable %, grid stability, etc.)

**When to Use**: Verifying dashboard is working correctly

**Related**: [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)

---

### ENHANCED_BI_STATUS.md {#enhanced-bi-status}
**Category**: 📊 Quick Status  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Quick status check document showing what's working in the Enhanced BI Analysis sheet.

**Key Content**:
- Section-by-section status
- Data metrics per section

**When to Use**: Quick verification of dashboard status

**Related**: [ENHANCED_BI_SUCCESS.md](#enhanced-bi-success)

---

### SIMPLE_REFRESH_SOLUTIONS.md {#simple-refresh-solutions}
**Category**: 🔄 Operational Guide  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Documents different methods to refresh the Analysis BI Enhanced dashboard. Google Sheets menu parked due to rendering issues, but terminal refresh working perfectly.

**Key Content**:
- Google Sheets menu status (parked)
- WORKING SOLUTION: Terminal command refresh
  ```bash
  python3 update_analysis_bi_enhanced.py
  ```
- Alternative solutions (if needed)
- What the refresh does (updates 4 sections + metrics)

**When to Use**: Refreshing dashboard data, troubleshooting refresh issues

**Related**: [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)

---

### QUICK_REFERENCE_BI_SHEET.md {#quick-reference-bi-sheet}
**Category**: 📊 Quick Reference  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Quick reference card for Enhanced BI Analysis sheet with current status and data metrics.

**Key Content**:
- Current status (all 4 sections working)
- Latest update timestamp
- Data range
- Section metrics summary

**When to Use**: Quick dashboard status check

**Related**: [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)

---

## 🚀 Getting Started Guides

### README_ANALYSIS_SHEET.md {#readme-analysis-sheet}
**Category**: 🚀 Quick Start  
**Status**: ✅ Active  
**Date**: October 30, 2025

**Summary**:  
Simplified quick start guide for creating the Analysis sheet in one command.

**Key Content**:
- TL;DR single command setup
- What the command does
- What you get (unified dashboard)

**When to Use**: First-time setup of Analysis sheet

**Related**: [ANALYSIS_SHEET_DESIGN.md](#analysis-sheet-design)

---

### SHEET_REFRESH_MENU_GUIDE.md {#sheet-refresh-menu-guide}
**Category**: 🔄 Menu Guide  
**Status**: ⚠️ Parked (Menu rendering issues)  
**Date**: October 31, 2025

**Summary**:  
Guide for Google Sheets menu-based refresh system. Currently parked due to menu not appearing in Google Sheets UI.

**Key Content**:
- What the menu does
- Installation steps for Google Apps Script
- Menu options (Refresh Data, Refresh Generation, etc.)

**When to Use**: If attempting to implement menu-based refresh (not recommended)

**Related**: [SIMPLE_REFRESH_SOLUTIONS.md](#simple-refresh-solutions), [MENU_NOT_APPEARING_SOLUTION.md](#menu-not-appearing-solution)

---

## 📁 Historical/Deprecated Documentation

### ANALYSIS_SHEET_DESIGN.md {#analysis-sheet-design}
**Category**: 🏗️ Design Document  
**Status**: 📦 Reference (Superseded by ENHANCED_BI_ANALYSIS_README.md)  
**Date**: October 30, 2025

**Summary**:  
Original design document for the Analysis sheet with unified historical + real-time data.

**Key Content**:
- Design philosophy
- Data sources and query patterns
- Sheet structure

**When to Use**: Understanding original design decisions

**Related**: [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)

---

### ANALYSIS_SHEET_IMPLEMENTATION_SUMMARY.md {#analysis-sheet-implementation-summary}
**Category**: 📦 Implementation Report  
**Status**: 📦 Historical  
**Date**: October 30, 2025

**Summary**:  
Summary of initial Analysis sheet implementation. Superseded by later enhancements.

**When to Use**: Understanding implementation history

**Related**: [ANALYSIS_SHEET_DESIGN.md](#analysis-sheet-design)

---

### ANALYSIS_SHEET_SIMPLE_SUMMARY.md {#analysis-sheet-simple-summary}
**Category**: ✅ Status Update  
**Status**: 📦 Historical  
**Date**: October 31, 2025

**Summary**:  
Early status update showing simplified working Analysis sheet.

**When to Use**: Historical reference

**Related**: [ENHANCED_BI_SUCCESS.md](#enhanced-bi-success)

---

### ANALYSIS_SHEET_STATUS.md {#analysis-sheet-status}
**Category**: ✅ Status Update  
**Status**: 📦 Historical  
**Date**: October 31, 2025

**Summary**:  
Status document describing what was working in simplified version of Analysis sheet.

**When to Use**: Historical reference

**Related**: [ENHANCED_BI_SUCCESS.md](#enhanced-bi-success)

---

### ANALYSIS_SHEET_WITH_DROPDOWNS.md {#analysis-sheet-with-dropdowns}
**Category**: ✅ Feature Update  
**Status**: 📦 Historical  
**Date**: October 31, 2025

**Summary**:  
Documents addition of dropdown controls to Analysis sheet.

**When to Use**: Historical reference

**Related**: [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)

---

### SHEET_REFRESH_COMPLETE.md {#sheet-refresh-complete}
**Category**: ✅ Completion Report  
**Status**: 📦 Historical  
**Date**: October 31, 2025

**Summary**:  
Documents completion of sheet refresh menu system (later parked due to rendering issues).

**Key Content**:
- Files created (Google Apps Script)
- Menu features
- Usage instructions

**When to Use**: Historical reference for menu implementation

**Related**: [SHEET_REFRESH_MENU_GUIDE.md](#sheet-refresh-menu-guide)

---

### MENU_NOT_APPEARING_SOLUTION.md {#menu-not-appearing-solution}
**Category**: 🐛 Troubleshooting  
**Status**: ⚠️ Issue Documentation  
**Date**: October 31, 2025

**Summary**:  
Documents why Google Sheets menu is not appearing (underlying Google Apps Script rendering issue).

**Key Content**:
- Problem discovered (menu renders in editor but not in Google Sheets)
- Why it happens (Google Apps Script limitation)
- Workaround (use terminal command instead)

**When to Use**: Understanding why menu-based refresh was parked

**Related**: [SIMPLE_REFRESH_SOLUTIONS.md](#simple-refresh-solutions)

---

### GOOGLE_SHEET_INFO.md {#google-sheet-info}
**Category**: ℹ️ Reference  
**Status**: 📦 Reference  
**Date**: October 31, 2025

**Summary**:  
Basic information about the Analysis BI Enhanced Google Sheet.

**Key Content**:
- Sheet ID
- Basic data sources
- Section information

**When to Use**: Quick reference for sheet details

**Related**: [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)

---

### GEMINI_AI_SETUP.md {#gemini-ai-setup}
**Category**: 🤖 AI Integration  
**Status**: 📦 Reference  
**Date**: Earlier

**Summary**:  
Guide for setting up Gemini AI analysis features (if implemented).

**When to Use**: If implementing AI-powered analysis features

---

## 📊 Documentation Statistics

### By Category
| Category | Count | Status |
|----------|-------|--------|
| 🏠 Main Entry | 1 | ✅ Active |
| 🔧 Configuration | 3 | ✅ Active |
| 🏗️ Architecture | 1 | ✅ Active |
| 📊 Dashboard | 7 | ✅ Active |
| 📈 Analytics | 1 | ✅ Active |
| 🚀 Getting Started | 1 | ✅ Active |
| 📋 Process/Updates | 2 | ✅ Active |
| 🔄 Operational | 2 | ✅ Active |
| 📦 Historical | 6 | 📦 Reference |
| ⚠️ Issues | 1 | ⚠️ Documented |

### By Status
| Status | Count | Description |
|--------|-------|-------------|
| ✅ Active | 14 | Current, actively maintained |
| 📦 Reference | 7 | Historical, for reference |
| ⚠️ Issue | 1 | Documents known issue |

### By Date
| Date | Documents Created/Updated |
|------|---------------------------|
| Oct 30, 2025 | Architecture, initial dashboard docs |
| Oct 31, 2025 | Configuration, schema fixes, analytics guide, dashboard enhancements |

---

## 🗺️ Documentation Roadmap

### Reading Order for New Users

**Phase 1: Setup & Understanding (30 minutes)**
1. [README.md](#readme) - Project overview
2. [PROJECT_CONFIGURATION.md](#project-configuration) - Configuration essentials
3. [UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](#unified-architecture) - System design

**Phase 2: Using the Dashboard (15 minutes)**
4. [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme) - Dashboard guide
5. [SIMPLE_REFRESH_SOLUTIONS.md](#simple-refresh-solutions) - How to refresh data

**Phase 3: Advanced Analysis (as needed)**
6. [STATISTICAL_ANALYSIS_GUIDE.md](#statistical-analysis-guide) - Statistical outputs
7. [SCHEMA_FIX_SUMMARY.md](#schema-fix-summary) - Schema reference

### Reading Order for Developers

**Phase 1: Configuration (15 minutes)**
1. [PROJECT_CONFIGURATION.md](#project-configuration) - All critical settings
2. [DOCUMENTATION_IMPROVEMENT_SUMMARY.md](#documentation-improvement-summary) - Common mistakes to avoid

**Phase 2: Architecture (30 minutes)**
3. [UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](#unified-architecture) - System design
4. [SCHEMA_FIX_SUMMARY.md](#schema-fix-summary) - Table schemas

**Phase 3: Implementation (as needed)**
5. [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme) - Dashboard implementation
6. [STATISTICAL_ANALYSIS_GUIDE.md](#statistical-analysis-guide) - Analytics implementation

---

## 🔍 How to Find What You Need

### By Use Case

**"I'm new to the project"**
→ [README.md](#readme) → [PROJECT_CONFIGURATION.md](#project-configuration)

**"I need to refresh the dashboard"**
→ [SIMPLE_REFRESH_SOLUTIONS.md](#simple-refresh-solutions)

**"I'm getting configuration errors"**
→ [PROJECT_CONFIGURATION.md](#project-configuration) → [DOCUMENTATION_IMPROVEMENT_SUMMARY.md](#documentation-improvement-summary)

**"I need to query BigQuery"**
→ [PROJECT_CONFIGURATION.md](#project-configuration) (templates section)

**"I need to understand table schemas"**
→ [PROJECT_CONFIGURATION.md](#project-configuration) → [SCHEMA_FIX_SUMMARY.md](#schema-fix-summary)

**"I need to interpret statistical outputs"**
→ [STATISTICAL_ANALYSIS_GUIDE.md](#statistical-analysis-guide)

**"I need to understand the architecture"**
→ [UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](#unified-architecture)

**"I need to use the dashboard"**
→ [ENHANCED_BI_ANALYSIS_README.md](#enhanced-bi-analysis-readme)

**"Something broke, need to troubleshoot"**
→ [PROJECT_CONFIGURATION.md](#project-configuration) (Common Pitfalls) → [SCHEMA_FIX_SUMMARY.md](#schema-fix-summary)

---

## 📚 Documentation Maintenance

### Adding New Documentation

1. Create new .md file
2. Add summary section at top with date, status, purpose
3. Update this index with new entry
4. Link from related documents
5. Add to appropriate category

### Updating Existing Documentation

1. Update the document
2. Change "Last Updated" date
3. Add entry to document's change log (if exists)
4. Update this index if summary changed
5. Check related documents for consistency

### Deprecating Documentation

1. Change status to 📦 Historical or 📦 Reference
2. Add note about which document supersedes it
3. Update this index with new status
4. Keep file for historical reference (don't delete)

---

## 🔗 External Resources

| Resource | URL |
|----------|-----|
| Google Sheet Dashboard | https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/ |
| GitHub Repository | https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop |
| BigQuery Console | https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9 |
| FastAPI Search Service | http://94.237.55.15:8080 |
| FastAPI Health Check | http://94.237.55.15:8080/health |

---

## 🔌 API & Integration Documentation

### drive-bq-indexer/API.md
**Category**: 🔌 API & Data Integration  
**Status**: ✅ Production  
**Date**: November 5, 2025  
**Size**: 702 lines

**Summary**:  
Comprehensive documentation for the FastAPI search service and BigQuery data repository. Covers all endpoints, query capabilities, data architecture, and ChatGPT integration.

**Key Content**:
- **FastAPI Endpoints**: `/health` (health check), `/search` (semantic search)
- **BigQuery Datasets**: 
  - `uk_energy_insights` - 153K documents, embeddings, semantic search
  - `uk_energy_prod` - 391M+ rows, 200+ tables, 3.8 years of GB power market data
- **Query Examples**: 5 categories (Operational Performance, Market Analytics, Real-Time Monitoring, Historical Trends, Document Intelligence)
- **Statistics & Metrics**: Data volume, coverage, storage costs
- **Data Architecture**: ChatGPT ↔ BigQuery integration flow
- **Major Tables Documented**: bmrs_bod (391M rows), bmrs_fuelinst (5.7M), bmrs_mid, IRIS real-time tables
- **Deployment**: Docker, GitHub Actions, environment configuration
- **Testing**: Health checks, search tests, error handling
- **Troubleshooting**: API issues, search problems, common errors

**When to Use**: 
- Setting up API access
- Understanding BigQuery data structure
- Writing queries for energy market data
- Integrating with ChatGPT/AI platform
- Troubleshooting search functionality

**Related**: [ARCHITECTURE_VERIFIED.md](#architecture-verified), [UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](#unified-architecture)

---

## 📝 Index Metadata

**Created**: 31 October 2025  
**Last Updated**: 31 October 2025  
**Total Documents Indexed**: 22  
**Active Documents**: 14  
**Historical/Reference**: 8  
**Maintainer**: GB Power Market Team

---

**Need help?** Start with [README.md](#readme) or [PROJECT_CONFIGURATION.md](#project-configuration)

---

## 🆕 Latest Additions (October 31, 2025 - Post-Crash Recovery)

### QUICK_START_ANALYSIS.md {#quick-start-analysis}
**Category**: ⚡ Analysis Commands  
**Status**: ✅ Active  
**Date**: October 31, 2025

**Summary**:  
Copy-paste commands for running all data analysis functions. Created after environment fix and comprehensive testing.

**Key Content**:
- Instant commands (no thinking, just run)
- Statistical analysis outputs explained
- Common analysis workflows (battery optimization, dashboard export, AI insights)
- Troubleshooting quick fixes
- Success checklist

**When to Use**: Want to run analysis NOW, need quick command reference

**Related**: CODE_REVIEW_SUMMARY.md, STATISTICAL_ANALYSIS_GUIDE.md

---

### CODE_REVIEW_SUMMARY.md {#code-review-summary}
**Category**: 🔍 Code Documentation  
**Status**: ✅ Active  
**Date**: October 31, 2025  
**Size**: 450+ lines

**Summary**:  
Complete code review of all analysis functions after fixing the Python virtual environment crash. Documents all 19 statistical functions, configuration settings, and usage patterns.

**Key Content**:
- Environment status (fixed issues + remaining)
- 19 analysis functions documented with inputs/outputs/purpose/runtime
- Configuration inconsistencies identified
- Code quality assessment
- Next steps with specific commands
- Analysis function summary table

**When to Use**: Understanding what each analysis function does, troubleshooting code issues, learning the codebase

**Related**: QUICK_START_ANALYSIS.md, STATISTICAL_ANALYSIS_GUIDE.md

---

### test_analysis_functions.py {#test-script}
**Category**: 🧪 Test Script  
**Status**: ✅ Active  
**Type**: Python Script (not markdown)  
**Date**: October 31, 2025

**Summary**:  
Comprehensive test suite that verifies all analysis functions, imports, and connections work correctly.

**When to Use**: Verifying environment setup, troubleshooting dependencies

---

**Total Documents Now**: 25 markdown files + 1 test script  
**Environment Status**: ✅ Fully operational after crash recovery
