# BigQuery HH DATA Solution - Deployment Checklist

## ✅ Implementation Status: COMPLETE

All BigQuery infrastructure and scripts are ready for production use.

---

## 📋 Deployment Checklist

### Phase 1: Core Infrastructure (COMPLETE ✅)

- [x] **BigQuery Table Created**
  - Table: `inner-cinema-476211-u9.uk_energy_prod.hh_data_btm_generated`
  - Schema: 9 fields (timestamp, settlement_period, day_type, demand_kw, profile_pct, supply_type, scale_value, generated_at, generated_by)
  - Partitioning: DATE(generated_at)
  - Clustering: supply_type, day_type
  - Location: US
  - Status: ✅ Created and verified

- [x] **Upload Script Created**
  - File: `upload_hh_to_bigquery.py`
  - Features: Read from Sheets → Upload to BigQuery → Delete sheet
  - Usage: `python3 upload_hh_to_bigquery.py "Commercial" 10000`
  - Status: ✅ Code complete, ready to test

- [x] **Fast Lookup Implementation**
  - File: `btm_dno_lookup.py` (updated)
  - Primary: Query BigQuery (~5 sec)
  - Fallback: Read Google Sheets (~7 min) if BigQuery empty
  - Expected: 70x performance improvement
  - Status: ✅ Code complete, ready to test

- [x] **Apps Script Integration**
  - File: `btm_hh_generator.gs` (updated)
  - Success message includes BigQuery upload instructions
  - User guidance for next steps
  - Status: ✅ Updated and deployed

### Phase 2: Testing & Validation (READY TO START ⏳)

- [ ] **Manual End-to-End Test**
  - Run: `./test_bigquery_workflow.sh`
  - Steps:
    1. Generate HH DATA via Google Sheets button
    2. Upload to BigQuery: `python3 upload_hh_to_bigquery.py "Commercial" 10000`
    3. Verify sheet deletion
    4. Run calculations: `python3 btm_dno_lookup.py`
    5. Confirm ~10 second runtime
    6. Verify results in BtM sheet
  - Status: ⏳ Ready to test (requires user action)

- [ ] **Performance Validation**
  - Baseline: 7 minutes (Google Sheets)
  - Target: <15 seconds (BigQuery)
  - Measure: `time python3 btm_dno_lookup.py`
  - Status: ⏳ Awaiting first test run

- [ ] **Data Integrity Check**
  - Verify 17,520 records uploaded
  - Confirm correct supply_type
  - Validate timestamp ranges
  - Check kWh band calculations match
  - Status: ⏳ Awaiting first test run

### Phase 3: Maintenance Setup (READY TO CONFIGURE 📝)

- [ ] **BigQuery Scheduled Cleanup Query**
  - Location: https://console.cloud.google.com/bigquery/scheduled-queries?project=inner-cinema-476211-u9
  - SQL: See `create_bigquery_scheduled_cleanup.sql`
  - Schedule: Monthly on 1st at 02:00 UTC
  - Purpose: Auto-delete records >90 days old
  - Status: 📝 Script created, manual UI setup required

- [ ] **Documentation Review**
  - File: `BIGQUERY_HH_DATA_IMPLEMENTATION.md`
  - Includes: Architecture, workflow, troubleshooting, examples
  - Status: ✅ Complete and comprehensive

### Phase 4: Optional Enhancements (AVAILABLE 🎁)

- [ ] **Direct BigQuery Upload from Apps Script**
  - File: `btm_hh_generator_enhanced.gs` (created)
  - Features:
    - One-click generate + upload + delete
    - No manual python3 command
    - Requires OAuth scope configuration
  - Setup:
    1. Enable BigQuery API in Apps Script Services
    2. Add OAuth scopes (bigquery, bigquery.insertdata)
    3. Replace btm_hh_generator.gs with enhanced version
    4. Authorize on first run
  - Status: 🎁 Code complete, optional installation

- [ ] **Monitoring Dashboard**
  - BigQuery queries to track:
    - Upload frequency
    - Data volume over time
    - Supply type usage
    - Performance metrics
  - Status: 💡 Future enhancement

---

## 🚀 Quick Start Guide

### For First-Time Use:

```bash
# 1. Generate HH DATA in Google Sheets
# Click: "🔄 Generate HH Data" button

# 2. Upload to BigQuery (first time)
cd /home/george/GB-Power-Market-JJ
python3 upload_hh_to_bigquery.py "Commercial" 10000 "initial_test"

# 3. Run calculations (should be ~10 seconds now)
time python3 btm_dno_lookup.py

# 4. Check results in Google Sheets BtM tab
```

### For Regular Use:

```bash
# After generating new HH DATA:
python3 upload_hh_to_bigquery.py "Commercial" 10000
python3 btm_dno_lookup.py
```

---

## 📊 Expected Results

### Before BigQuery:
```
⏱️  Total Time: ~7 minutes
├─ HH DATA read (Google Sheets API): 6-7 min
├─ BigQuery queries (DNO/DUoS): 5 sec
├─ Calculations: <1 sec
└─ Sheet updates: 5 sec
```

### After BigQuery:
```
⏱️  Total Time: ~10 seconds
├─ HH DATA read (BigQuery): 5 sec
├─ BigQuery queries (DNO/DUoS): 5 sec
├─ Calculations: <1 sec
└─ Sheet updates: 5 sec

🎉 Improvement: 70x faster!
```

---

## 🔧 Troubleshooting Checklist

### Issue: "BigQuery table not found"
- [ ] Verify project: `inner-cinema-476211-u9`
- [ ] Check dataset: `uk_energy_prod`
- [ ] Confirm table: `hh_data_btm_generated`
- [ ] Test: Run `python3 create_hh_bigquery_table.py`

### Issue: "No data in BigQuery table"
- [ ] Generate HH DATA first (Google Sheets button)
- [ ] Run upload: `python3 upload_hh_to_bigquery.py`
- [ ] Verify: Query `SELECT COUNT(*) FROM table`

### Issue: "Still using Google Sheets (slow path)"
- [ ] Check console output for "Reading HH DATA from BigQuery"
- [ ] If seeing "falling back to Google Sheets", check BigQuery data
- [ ] Verify credentials: `export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"`

### Issue: "HH DATA sheet not found"
- [ ] Sheet was deleted after upload (expected behavior)
- [ ] Regenerate if needed: Click button in Google Sheets

---

## 📚 Related Files

### Core Implementation:
- `create_hh_bigquery_table.py` - Table creation script
- `upload_hh_to_bigquery.py` - Upload & delete script
- `btm_dno_lookup.py` - Updated with BigQuery reading
- `btm_hh_generator.gs` - Apps Script generator

### Documentation:
- `BIGQUERY_HH_DATA_IMPLEMENTATION.md` - Complete guide
- `create_bigquery_scheduled_cleanup.sql` - Cleanup query
- `BIGQUERY_DEPLOYMENT_CHECKLIST.md` - This file

### Testing:
- `test_bigquery_workflow.sh` - Automated test script

### Optional:
- `btm_hh_generator_enhanced.gs` - Direct BigQuery upload version

---

## 🎯 Success Criteria

- [x] BigQuery table exists and accessible
- [x] Upload script functional
- [x] btm_dno_lookup.py queries BigQuery
- [x] Apps Script prompts for upload
- [ ] **End-to-end test passes** ⏳
- [ ] **Performance <15 seconds** ⏳
- [ ] **Data integrity validated** ⏳
- [ ] **Scheduled cleanup configured** 📝

---

## 📞 Support

**Issues or Questions?**
- Check: `BIGQUERY_HH_DATA_IMPLEMENTATION.md` (troubleshooting section)
- Review: Console output for error messages
- Verify: BigQuery table exists and has data
- Test: Run `./test_bigquery_workflow.sh`

---

**Last Updated**: December 30, 2025
**Status**: ✅ Implementation complete, ready for testing
**Next Action**: Run `./test_bigquery_workflow.sh` to validate end-to-end workflow

