# BESS VLP Tool - Quick Start Guide 🚀

**Status**: ✅ Sheet Created | 🟡 Apps Script Ready | ⏳ Testing Pending

---

## What You Have Now

✅ **BESS_VLP Sheet**: New tab in your Google Sheets dashboard  
✅ **14 UK DNOs**: Complete reference data populated from BigQuery  
✅ **Apps Script Code**: Ready to deploy (`apps-script/bess_vlp_lookup.gs`)  
✅ **Documentation**: Full deployment guide (`BESS_VLP_DEPLOYMENT_GUIDE.md`)

**Sheet URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit#gid=244875982

---

## Deploy Apps Script (5 Minutes)

### Step 1: Open Apps Script Editor
1. Open your Google Sheets dashboard
2. Click **Extensions → Apps Script**

### Step 2: Add the Code
1. Delete the default `function myFunction() {}` code
2. Copy **ALL** code from `apps-script/bess_vlp_lookup.gs`
3. Paste into editor
4. Save (Ctrl+S or Cmd+S)

### Step 3: Enable BigQuery API
1. Left sidebar: Click **Services +**
2. Search "BigQuery API"
3. Add "BigQuery API v2"
4. Close dialog

### Step 4: Authorize
1. Click **Run → onOpen** (dropdown at top)
2. Click "Review permissions"
3. Choose your Google account
4. Click "Advanced" → "Go to [Project Name] (unsafe)"
5. Click "Allow"

### Step 5: Verify
1. Refresh your Google Sheets
2. Look for new menu: **🔋 BESS VLP Tools**
3. If you see it, deployment successful! ✅

---

## Test It (2 Minutes)

### Quick Test
1. Go to **BESS_VLP** sheet tab
2. Click cell **B4**
3. Type: `SW1A 1AA` (Buckingham Palace postcode)
4. Click menu: **🔋 BESS VLP Tools → Lookup DNO**
5. Wait 1-2 seconds
6. Check row 10 - should show:
   - MPAN: **11**
   - DNO Key: **UKPN-LPN**
   - DNO Name: **UK Power Networks (London)**
   - GSP Group: **B**

### More Tests
- Scotland: `IV1 1XE` → SSE-SHEPD (Scottish Hydro)
- Wales: `CF10 1EP` → NGED-SWales (South Wales)
- Cornwall: `TR1 1EB` → NGED-SWest (South West)

---

## How To Use

### For Battery Site Analysis
```
1. Get postcode of potential BESS site
2. Enter in cell B4
3. Click "Lookup DNO" from menu
4. Read DNO information in row 10
5. Use for connection applications, DUoS estimates, etc.
```

### For VLP Revenue Tracking
```
1. Look up BMU registration postcode
2. Identify DNO serving that site
3. Correlate revenue performance by DNO region
4. Identify high-performing areas
```

### For Market Analysis
```
1. Batch lookup multiple sites
2. Map DNO distribution patterns
3. Compare connection costs by region
4. Analyze grid constraint areas
```

---

## What It Does

```
Enter Postcode (e.g., "SW1A 1AA")
         ↓
Calls UK Postcode API → Gets Lat/Long (51.5014, -0.1419)
         ↓
Queries BigQuery → Spatial match to DNO boundary
         ↓
Returns DNO Data:
  - MPAN Distributor ID (10-23)
  - DNO Key (UKPN-LPN, NGED-EMid, etc.)
  - Full DNO Name
  - Market Participant ID
  - GSP Group (A-P)
  - GSP Group Name
  - Coverage Area
         ↓
Populates Sheet Row 10 with results
```

---

## Troubleshooting

### "BigQuery API not found" Error
- **Fix**: Apps Script editor → Services + → Add BigQuery API v2

### "Permission denied" Error
- **Fix**: Run → onOpen → Review permissions → Allow all

### "Invalid postcode" Error
- **Fix**: Use format "XX1 2YY" with space (e.g., "SW1A 1AA")

### "No DNO found" Error
- **Possible**: Offshore location, Northern Ireland, or boundary issue
- **Fix**: Try nearby postcode or check coordinates manually

---

## Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `create_bess_vlp_sheet.py` | Python script to build sheet | ✅ Executed |
| `apps-script/bess_vlp_lookup.gs` | Apps Script lookup code | 🟡 Ready to deploy |
| `BESS_VLP_DEPLOYMENT_GUIDE.md` | Full technical documentation | ✅ Complete |
| `BESS_VLP_QUICKSTART.md` | This quick guide | ✅ Complete |

---

## What's Populated

### Sheet Structure
- **Row 4**: Postcode input (yellow cell)
- **Row 10**: DNO results (8 columns)
- **Row 14-15**: Lat/Long coordinates
- **Row 20-33**: All 14 UK DNOs reference table

### DNO Reference Data
All 14 UK Distribution Network Operators:
1. Eastern Power Networks (MPAN 10)
2. London Power Networks (MPAN 11)
3. South Eastern Power Networks (MPAN 12)
4. NGED East Midlands (MPAN 13)
5. NGED West Midlands (MPAN 14)
6. Northern Powergrid NE (MPAN 15)
7. Electricity North West (MPAN 16)
8. NGED South Wales (MPAN 17)
9. SSE Scottish Hydro (MPAN 18)
10. SSE Southern Electric (MPAN 19)
11. NGED South West (MPAN 20)
12. SP Distribution (MPAN 21)
13. SP Manweb (MPAN 22)
14. Northern Powergrid Yorkshire (MPAN 23)

---

## Next Steps

### Immediate
1. ⏳ Deploy Apps Script (5 min)
2. ⏳ Test with 4 sample postcodes (2 min)
3. ⏳ Verify all data fields populate correctly

### This Week
- Add auto-trigger on postcode change
- Create batch lookup feature
- Export DNO assignments to BigQuery

### This Month
- Populate DUoS tariff tables
- Link to revenue analysis
- Add GSP-level price analysis

---

## Support

**Full Guide**: `BESS_VLP_DEPLOYMENT_GUIDE.md` (1000+ lines)  
**DNO Reference**: `DNO_DATA_COMPLETE_INVENTORY.md` (all DNO details)  
**DUoS Status**: `DNUOS_CHARGES_STATUS.md` (tariff gap analysis)  
**Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md` (data structure)

---

## Why This Matters

### Battery Arbitrage Analysis
> "Oct 17-23, 2025: £79.83/MWh avg (6-day high-price event = 80% of VLP revenue)"

Knowing which DNO serves a battery site enables:
- **Connection Cost Estimates**: DNO-specific charges
- **DUoS Tariff Calculation**: Regional network costs
- **Revenue Optimization**: Target high-profit DNO areas
- **Market Participation**: Correct IDs for settlement

### Use Case: New 50MW BESS Site
```
Site Location: Leicester (LE1 5FQ)
         ↓
Lookup DNO → NGED East Midlands (MPAN 13, GSP D)
         ↓
Know:
  - Connection: NGED East Midlands team
  - DUoS Zone: East Midlands tariff rates
  - GSP: "D" group for pricing
  - Participant: NGED East Midlands ID
  - Queue: Check NGED connection queue
  - Constraints: Check GSP D grid capacity
```

---

**Status**: READY TO DEPLOY  
**Time Required**: 7 minutes (5 deploy + 2 test)  
**Priority**: HIGH - Enables critical site analysis

---

*Created: November 9, 2025 20:18 GMT*
