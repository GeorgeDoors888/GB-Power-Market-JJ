# Outstanding TODOs - Priority Summary

**Generated:** 28 December 2025  
**Context:** Post CHATGPT_DATA_ACCESS.md documentation

---

## 🔴 CRITICAL - Blocking User Functionality

### 1. Fix ChatGPT Data Access (Vercel 404)
**Status:** ❌ BROKEN - User cannot query data via ChatGPT  
**Why Outstanding:** Vercel proxy returns 404, ChatGPT configured to use broken URL  
**Impact:** ChatGPT cannot access 1.13B BigQuery rows + 35,168 PDF chunks  
**Solution Documented:** CHATGPT_DATA_ACCESS.md (3 options)  
**Quickest Fix:** Update ChatGPT GPT schema to use Railway directly  
**Time Estimate:** 5 minutes  
**Blocker:** User needs to update ChatGPT Custom GPT configuration

**Current State:**
```
❌ Vercel: https://gb-power-market-jj.vercel.app/api/proxy-v2 → 404 NOT FOUND
✅ Railway: https://jibber-jabber-production.up.railway.app → Healthy
✅ BigQuery: 296 tables, 1.13B rows accessible
✅ PDFs: 1,117 documents, 35,168 chunks indexed
```

**Why Not Done:**
- Requires manual update in ChatGPT interface (not scriptable)
- User has documentation but hasn't implemented
- Needs decision: Railway direct (simple) vs Fix Vercel (secure) vs Use Dell (powerful)

---

## 🟡 HIGH PRIORITY - Feature Gaps

### 2. Google My Maps Auto-Upload
**Status:** 🔄 SEMI-AUTOMATED - Dell generates KML, manual import required  
**Why Outstanding:** Google My Maps has no programmatic API for layer updates  
**Impact:** DNO boundary map shows stale data, requires manual refresh  
**Solution Created:** auto_update_google_my_maps.py (uploads to Drive)  
**Time Estimate:** 30 min setup (OAuth credentials) + 2 min per update  
**Blocker:** Needs OAuth client credentials from Google Cloud Console

**Current State:**
```
✅ KML Generation: dno_boundaries.kml (2.2MB, 14 DNO regions, £130.5M costs)
✅ Script Created: auto_update_google_my_maps.py
❌ OAuth Setup: Need client_credentials.json from Google Cloud Console
❌ Cron Job: Not scheduled for automatic uploads
```

**Why Not Done:**
- Google My Maps has NO API for programmatic layer updates
- Semi-automated solution reduces manual work but still requires 2-click import
- Fully automated option requires Google Maps JS API (different product)
- User hasn't chosen preferred approach (semi-auto vs full rebuild)

---

### 3. BESS Real-Time DUoS Lookup
**Status:** 🔄 HARDCODED RATES - Not connected to BigQuery  
**Why Outstanding:** duos_rates_complete table schema issues  
**Impact:** BESS sheet uses static rates instead of live tariff data  
**Solution:** Fix BigQuery table, update bess_dno_lookup.gs  
**Time Estimate:** 1-2 hours  
**Blocker:** Need to verify correct BigQuery table name/schema

**Current State:**
```
✅ Postcode Lookup: Working via postcodes.io API
✅ MPAN Parsing: Working via mpan_generator_validator
✅ DNO Details: Working via neso_dno_reference table
❌ DUoS Rates: Hardcoded in script, need live BigQuery lookup
❌ Table Issue: duos_rates_complete not found or wrong schema
```

**Why Not Done:**
- BigQuery table schema mismatch or missing table
- Need to map voltage level (LV/HV/EHV) to query parameters
- Requires API rate limiting/caching strategy
- Not critical: Hardcoded rates work for current demo purposes

---

## 🟢 MEDIUM PRIORITY - Enhancement Features

### 4. BESS HH Profile Generator
**Status:** ❌ NOT STARTED - Menu item exists but no script  
**Why Outstanding:** Complex logic for realistic time-series generation  
**Impact:** Users cannot generate half-hourly consumption profiles  
**Solution:** Create generate_hh_profile.py with time band logic  
**Time Estimate:** 3-4 hours  
**Blocker:** None (straightforward implementation)

**Requirements:**
```
Inputs:  Min kW (B17), Avg kW (B18), Max kW (B19)
Outputs: 48 half-hourly periods (A22:D69) with time, kW, kWh, cost
Logic:   Red (16:00-19:00) = Max kW
         Amber (08:00-16:00, 19:30-22:00) = Avg kW
         Green (00:00-08:00, 22:00-23:59, weekends) = Min kW
         Add variance for realistic profile
```

**Why Not Done:**
- Not critical for current functionality
- Requires domain knowledge of realistic consumption patterns
- Need to decide: Use fixed patterns vs ML-generated profiles
- Lower priority than data access fixes

---

### 5. Dashboard V3 Design Reconciliation
**Status:** ⚠️ CONFLICTING IMPLEMENTATIONS  
**Why Outstanding:** Two separate designs exist with different specs  
**Impact:** Confusion about canonical design, potential merge conflicts  
**Solution:** Choose Apps Script OR Python implementation as canonical  
**Time Estimate:** 2-3 hours review + decision + merge  
**Blocker:** Need architectural decision from user

**Conflict Summary:**
```
Apps Script:  Dark slate header, 6 KPIs, sparklines, simplified
Python:       Orange header, 7 KPIs, DNO filtering, complex automation
Files:        buildDashboardV3() vs apply_dashboard_design.py
Decision:     Which is canonical? Merge both? Deprecate one?
```

**Why Not Done:**
- Both implementations partially work
- No clear directive on preferred approach
- Merge would require significant refactoring
- Not blocking current operations (both dashboards functional)

---

## 📊 Summary Statistics

**Critical Issues:** 1 (ChatGPT access broken)  
**High Priority:** 2 (Maps auto-upload, DUoS lookup)  
**Medium Priority:** 2 (HH profile generator, Dashboard design)  
**Total Outstanding:** 5 todos

**Completion Blockers:**
- 2 require user action (ChatGPT config, OAuth setup)
- 2 require technical work (BigQuery schema, Python script)
- 1 requires architectural decision (Dashboard design)

**Estimated Total Time:**
- Quick wins: 35 min (ChatGPT fix + Maps OAuth)
- Technical work: 5-7 hours (DUoS lookup + HH generator + Dashboard merge)
- **Total:** ~6-8 hours development + user configuration steps

---

## 🎯 Recommended Priority Order

1. **ChatGPT Fix** (5 min) - Immediate user impact, full documentation exists
2. **Google My Maps OAuth** (30 min) - Quick win, reduces manual work
3. **BESS DUoS Lookup** (1-2 hrs) - High value, removes hardcoded data
4. **BESS HH Generator** (3-4 hrs) - New feature, user requested
5. **Dashboard Design Decision** (2-3 hrs) - Technical debt, not blocking

**Next Immediate Action:** User should update ChatGPT GPT schema per CHATGPT_DATA_ACCESS.md guide.

