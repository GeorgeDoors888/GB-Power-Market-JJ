# BESS Future Enhancements - TODO List

**Last Updated:** 29 November 2025  
**Status:** Planning Phase

---

## 🎯 Priority 1 - Core Functionality

### 1. HH Profile Generator
**Status:** 🔴 Not Started  
**Priority:** HIGH  
**Complexity:** Medium

**Description:**  
Generate 48 half-hourly consumption values based on Min/Avg/Max kW parameters and time bands.

**Implementation:**
- [ ] Create `generate_hh_profile.py` script
- [ ] Read parameters from B17:B19
- [ ] Generate 48 rows (00:00-23:30) in A22:D69
- [ ] Apply time band logic (Red/Amber/Green)
- [ ] Add variance/randomization for realistic profile
- [ ] Hook up to "Generate HH Profile" menu item

**Technical Notes:**
- Red (Peak): 16:00-19:00 → Max kW
- Amber (Mid): 08:00-16:00, 19:30-22:00 → Avg kW
- Green (Off-Peak): 00:00-08:00, 22:00-23:59, Weekends → Min kW

---

### 2. Real-Time DUoS Rate Lookup
**Status:** 🟡 Partially Complete  
**Priority:** HIGH  
**Complexity:** Medium

**Description:**  
Currently using hardcoded rates. Connect to BigQuery for real-time tariff lookup.

**Implementation:**
- [ ] Fix BigQuery table schema for `duos_rates_complete`
- [ ] Update `bess_dno_lookup.gs` to query correct table
- [ ] Add voltage level to query (LV/HV/EHV)
- [ ] Add effective date filtering
- [ ] Cache results to avoid API limits
- [ ] Handle missing tariff data gracefully

**Current Issue:**
- Table `duos_rates_complete` not found or has wrong schema
- Using fallback rates: 1.764/0.205/0.011 p/kWh

---

### 3. Postcode to DNO Lookup
**Status:** 🔴 Not Started  
**Priority:** MEDIUM  
**Complexity:** High

**Description:**  
Allow users to enter postcode in A6 and auto-populate DNO details.

**Implementation:**
- [ ] Obtain postcode → GSP mapping dataset
- [ ] Upload to BigQuery table
- [ ] Update `bess_dno_lookup.gs` postcode function
- [ ] Add postcode validation regex
- [ ] Handle edge cases (split postcodes, multiple DNOs)

**Blockers:**
- Need reliable postcode → GSP data source
- Possible source: ONS Postcode Directory or Energy Networks Association

---

## 🎯 Priority 2 - Data Export & Reports

### 4. Export to CSV
**Status:** 🔴 Not Started  
**Priority:** MEDIUM  
**Complexity:** Low

**Description:**  
Export BESS data to CSV file for external analysis.

**Implementation:**
- [ ] Create `export_bess_csv.py` script
- [ ] Export DNO details (Row 6)
- [ ] Export rates (Row 10)
- [ ] Export HH profile (Rows 22-69) if exists
- [ ] Add timestamp to filename
- [ ] Hook up to "Export to CSV" menu item
- [ ] Add download prompt in Apps Script

**File Format:**
```csv
Export Date, DNO Key, DNO Name, Voltage, Red Rate, Amber Rate, Green Rate
2025-11-29 17:30, NGED-WM, National Grid..., HV, 1.764, 0.205, 0.011
```

---

### 5. PDF Report Generation
**Status:** 🔴 Not Started  
**Priority:** LOW  
**Complexity:** High

**Description:**  
Generate professional PDF report with DNO details, rates, and HH profile chart.

**Implementation:**
- [ ] Use Python library (reportlab or weasyprint)
- [ ] Design report template
- [ ] Include: Header, DNO details, Rate table, HH profile chart
- [ ] Add company branding/logo
- [ ] Generate filename with timestamp
- [ ] Hook up to "Generate PDF Report" menu item

---

## 🎯 Priority 3 - Advanced Features

### 6. Metrics Dashboard
**Status:** 🔴 Not Started  
**Priority:** MEDIUM  
**Complexity:** Medium

**Description:**  
Show calculated metrics based on HH profile and DUoS rates.

**Implementation:**
- [ ] Calculate total consumption (kWh per day)
- [ ] Calculate cost by time band (Red/Amber/Green breakdown)
- [ ] Calculate total daily DUoS cost
- [ ] Calculate potential savings from load shifting
- [ ] Display in modal dialog or sidebar
- [ ] Add visualization (pie chart for cost breakdown)

**Metrics to Show:**
- Daily consumption: XX kWh
- Red band cost: £XX (YY% of total)
- Amber band cost: £XX (YY% of total)
- Green band cost: £XX (YY% of total)
- Total DUoS cost: £XX/day
- Potential savings: £XX/day (shift 30% to Green)

---

### 7. Settings Panel
**Status:** 🔴 Not Started  
**Priority:** LOW  
**Complexity:** Low

**Description:**  
Configurable settings for BESS calculations.

**Implementation:**
- [ ] Create settings modal dialog (HTML + Apps Script)
- [ ] Add settings: API endpoint, refresh interval, decimal places
- [ ] Store settings in sheet Properties
- [ ] Add "Reset to Defaults" button
- [ ] Hook up to "Settings" menu item

---

### 8. MPAN Validator
**Status:** 🟡 Partially Complete  
**Priority:** LOW  
**Complexity:** Low

**Description:**  
Currently validates format only. Add check digit validation.

**Implementation:**
- [ ] Implement Luhn algorithm for MPAN check digit
- [ ] Validate profile class (digits 1-2)
- [ ] Validate DNO ID (digits 3-4)
- [ ] Add validation feedback in UI
- [ ] Show validation status in Row 4

---

### 9. Batch MPAN Processing
**Status:** 🔴 Not Started  
**Priority:** LOW  
**Complexity:** Medium

**Description:**  
Process multiple MPANs at once for comparison or portfolio analysis.

**Implementation:**
- [ ] Add "Batch Mode" sheet
- [ ] Input: List of MPANs in column A
- [ ] Output: DNO details + rates for each MPAN
- [ ] Add comparison metrics (cheapest/most expensive)
- [ ] Export batch results to CSV

---

## 🎯 Priority 4 - Integration & Automation

### 10. Webhook Integration
**Status:** 🟡 Partially Complete  
**Priority:** LOW  
**Complexity:** Medium

**Description:**  
Deploy webhook server for external API calls to BESS DNO lookup.

**Implementation:**
- [ ] Use existing `dno_webhook_server_upcloud.py`
- [ ] Deploy to UpCloud or similar
- [ ] Add authentication (API keys)
- [ ] Add rate limiting
- [ ] Document API endpoints
- [ ] Add CORS headers for web apps

**Existing Files:**
- `dno_webhook_server_upcloud.py` (needs deployment)
- `bess_webapp_api.gs` (partially implemented)

---

### 11. Scheduled Data Updates
**Status:** 🔴 Not Started  
**Priority:** LOW  
**Complexity:** Low

**Description:**  
Auto-update DUoS rates monthly from BigQuery.

**Implementation:**
- [ ] Create time-driven trigger in Apps Script
- [ ] Schedule monthly update (1st of month)
- [ ] Pull latest rates from BigQuery
- [ ] Update all BESS sheet rates
- [ ] Send email notification on update
- [ ] Log update history

---

### 12. Historical Rate Tracking
**Status:** 🔴 Not Started  
**Priority:** LOW  
**Complexity:** Medium

**Description:**  
Track DUoS rate changes over time for trend analysis.

**Implementation:**
- [ ] Create "Rate History" sheet
- [ ] Log rate changes with timestamp
- [ ] Add chart showing rate trends
- [ ] Calculate year-over-year changes
- [ ] Export historical data

---

## 🛠️ Technical Improvements

### 13. Error Handling & Logging
**Status:** 🟡 Partially Complete  
**Priority:** MEDIUM  
**Complexity:** Low

**Implementation:**
- [ ] Add comprehensive try/catch blocks
- [ ] Create error log sheet
- [ ] Log all API calls with timestamp
- [ ] Add user-friendly error messages
- [ ] Add retry logic for transient failures

---

### 14. Performance Optimization
**Status:** 🔴 Not Started  
**Priority:** LOW  
**Complexity:** Medium

**Implementation:**
- [ ] Cache BigQuery results (1 hour TTL)
- [ ] Batch Google Sheets API calls
- [ ] Minimize Apps Script execution time
- [ ] Add loading indicators for slow operations
- [ ] Profile and optimize slow functions

---

### 15. Testing Suite
**Status:** 🟡 Partially Complete  
**Priority:** MEDIUM  
**Complexity:** Medium

**Implementation:**
- [ ] Create `test_bess_complete.py` suite
- [ ] Test all Python scripts
- [ ] Test Apps Script functions (via clasp)
- [ ] Add integration tests
- [ ] Add CI/CD pipeline
- [ ] Document test coverage

**Existing Tests:**
- `test_bess_vlp_lookup.py`
- `test_mpan_details.py`
- `verify_bess_dropdowns.py`

---

## 📋 Implementation Roadmap

### Phase 1 (Next 1-2 weeks)
1. ✅ Fix DUoS rate lookup (BigQuery schema)
2. ✅ Implement HH Profile Generator
3. ✅ Add Export to CSV

### Phase 2 (Next 1 month)
4. ✅ Implement Metrics Dashboard
5. ✅ Add Postcode lookup
6. ✅ Improve error handling

### Phase 3 (Next 2-3 months)
7. ✅ Add PDF Report generation
8. ✅ Implement batch processing
9. ✅ Deploy webhook server

### Phase 4 (Future)
10. ✅ Historical rate tracking
11. ✅ Advanced analytics
12. ✅ Machine learning for load forecasting

---

## 📝 Notes

- Most menu items are placeholders that show "coming soon" messages
- Core functionality (DNO lookup, dropdowns, auto-triggers) is fully working
- BigQuery table schema needs verification for real-time rate lookup
- Postcode lookup requires external dataset

**Next Action:** Start with Priority 1 items (HH Profile Generator and Real-Time Rates)

---

**Maintained by:** GitHub Copilot  
**Project:** GB Power Market Dashboard V2 - BESS Sheet
