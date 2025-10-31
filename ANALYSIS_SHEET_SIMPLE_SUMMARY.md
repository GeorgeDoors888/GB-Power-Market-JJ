# ✅ Analysis Sheet - Simple & Working

**Status:** 🟢 LIVE NOW  
**Link:** https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

---

## 📊 What You Have

### Working Analysis Sheet
- ✅ Last 7 days generation data
- ✅ 50 rows displayed
- ✅ Historical + IRIS real-time combined
- ✅ Summary statistics
- ❌ No dropdowns (keeping it simple)

### Data Shown
- Timestamp
- Fuel Type (CCGT, WIND, NUCLEAR, etc.)
- Generation (MW)
- Source (historical/real-time)
- Settlement Date & Period
- Total Generation (GWh)

---

## 🔄 To Update

```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 simple_analysis_sheet.py
```

---

## 📝 Other Issues (To Sort Later)

**Schema mismatches on other views:**
- `bmrs_freq_unified` - need to check IRIS column names
- `bmrs_mid_unified` - need to check IRIS column names
- `bmrs_bod_unified` - need to check IRIS column names
- `bmrs_boalf_unified` - need to check IRIS column names

**Solution:** When ready, inspect IRIS table schemas and rewrite views to match actual columns.

---

## ✅ Summary

**What works now:** Simple Analysis sheet with generation data  
**How to update:** Run `python3 simple_analysis_sheet.py`  
**Other issues:** Schema fixes can wait - not urgent  

---

**Created:** October 31, 2025  
**Status:** ✅ Working, No Dropdowns, Keep It Simple
