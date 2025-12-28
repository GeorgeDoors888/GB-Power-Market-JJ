# NESO Data Download - Quick Browser Guide

**Created**: 28 December 2025  
**Status**: URGENT - Updated for NESO rebrand

## 🚨 BREAKING CHANGE: NESO Rebrand

**National Grid ESO → NESO (National Energy System Operator)**

- ❌ **OLD**: `data.nationalgrideso.com` (no longer works)
- ✅ **NEW**: `www.neso.energy/data-portal` (active)

---

## 🎯 WHAT YOU NEED TO OPEN NOW

Copy these exact URLs into your browser tabs:

### Tab 1: Constraint Breakdown (PRIORITY 1)
```
https://www.neso.energy/search-data
```

**Search for**: `historic constraint breakdown`  
**What to download**: 48 monthly CSV files (Jan 2022 - Dec 2025)  
**Time**: ~2 hours (click download 48 times)

**Alternative direct link** (may work):
```
https://www.neso.energy/data-portal/constraint-management/historic-constraint-breakdown
```

### Tab 2: Interconnectors (PRIORITY 2)
```
https://www.neso.energy/search-data
```

**Search for**: `interconnector` or `IFA` or `BritNed`  
**What to find**: Resource IDs for 7 interconnectors  
**Time**: ~1 hour (research URLs)

**Alternative direct link** (may work):
```
https://www.neso.energy/data-portal/interconnectors
```

### Tab 3: MBSS Balancing Services
```
https://www.neso.energy/search-data
```

**Search for**: `MBSS` or `mandatory balancing services`  
**What to download**: Daily cost CSV files  
**Time**: ~30 minutes

### Tab 4: Annual Reports
```
https://www.neso.energy/search-content
```

**Search for**: `balancing services annual report`  
**What to download**: 2022, 2023, 2024 Excel data tables  
**Time**: ~15 minutes

### Tab 5: Other Datasets
```
https://www.neso.energy/search-data
```

**Search terms to try**:
- `24 month constraint forecast`
- `modelled constraint costs`
- `skip rate`

---

## 🔍 SEARCH STRATEGY (If Direct Links Don't Work)

NESO has a powerful search interface:

1. **Go to**: https://www.neso.energy/search-data
2. **Type search term** in search box
3. **Filter by**:
   - Category: "Constraint Management" or "Balancing Services"
   - File type: "CSV" or "Excel"
   - Date range: 2022-2025
4. **Click dataset name** to open detail page
5. **Find "Download" or "Resources" section**
6. **Right-click download link** → Copy URL (for interconnectors)
7. **Click download** to save file (for constraint data)

---

## 📦 WHERE TO SAVE FILES

All downloads go to:
```
~/GB-Power-Market-JJ/neso_downloads/constraint_costs/
```

**Folder structure**:
```
constraint_costs/
├── constraint_breakdown/    ← Constraint CSV files go here (48 files)
├── mbss/                    ← MBSS CSV files go here
├── annual_reports/          ← Excel tables go here
├── forecast/                ← Forecast CSV goes here
├── modelled_costs/          ← Modelled costs CSV goes here
└── skip_rates/              ← Skip rate CSVs go here
```

---

## ⚡ QUICK START CHECKLIST

- [ ] Open Tab 1: https://www.neso.energy/search-data
- [ ] Search: "historic constraint breakdown"
- [ ] Download 48 monthly CSV files to `constraint_breakdown/`
- [ ] Open Tab 2: https://www.neso.energy/search-data
- [ ] Search: "interconnector" 
- [ ] Find 7 interconnector datasets, copy resource IDs
- [ ] Search: "MBSS" → Download to `mbss/`
- [ ] Search: "balancing services annual report" → Download Excel to `annual_reports/`
- [ ] Search: "24 month constraint forecast" → Download to `forecast/`
- [ ] Search: "modelled constraint costs" → Download to `modelled_costs/`
- [ ] Search: "skip rate" → Download to `skip_rates/`
- [ ] Run verification: `ls -R ~/GB-Power-Market-JJ/neso_downloads/constraint_costs/`

---

## 🆘 TROUBLESHOOTING

### Problem: "Page not found" or 404 error
**Solution**: Use search interface instead of direct links:
- Go to https://www.neso.energy/search-data
- Enter search term from list above
- Filter results to find exact dataset

### Problem: Too many results in search
**Solution**: Add more specific terms:
- "historic constraint breakdown monthly" (not just "constraint")
- "interconnector flow data" (not just "interconnector")
- Use date filters: 2022-2025

### Problem: Can't find download button
**Solution**: 
- Look for "Resources" tab on dataset page
- Look for "Data and Resources" section
- Try "Export" or "CSV" buttons
- Check for year-specific downloads (2022, 2023, 2024, 2025)

### Problem: Need API access instead
**Solution**: See Todo #8 (Research NESO Constraint Costs API)
- NESO data portal likely has DKAN/CKAN API
- API endpoint format: `/api/3/action/datastore_search?resource_id=XXXXX`
- This is FUTURE work (manual download works for now)

---

## 💡 PRO TIPS

1. **Use browser download manager**: Right-click links → "Save Link As" for bulk downloads
2. **Keep track**: Check off each file as you download (48 constraint files!)
3. **Verify size**: Constraint CSVs should be 100KB-5MB each
4. **Don't close tabs**: Keep search results open while downloading
5. **Check folder**: Verify files landed in correct subfolder before closing browser

---

## 📞 NEXT STEPS AFTER DOWNLOAD

Once downloads complete:

1. **Verify files downloaded**:
   ```bash
   ls -R ~/GB-Power-Market-JJ/neso_downloads/constraint_costs/
   ```

2. **Run ingestion script**:
   ```bash
   python3 ingest_neso_constraint_costs.py \
     --data-dir ~/GB-Power-Market-JJ/neso_downloads/constraint_costs \
     --test  # Test first!
   
   python3 ingest_neso_constraint_costs.py \
     --data-dir ~/GB-Power-Market-JJ/neso_downloads/constraint_costs  # Production
   ```

3. **Update interconnector script**:
   - Edit `ingest_interconnector_flows.py`
   - Replace `{resource_id}` placeholders with actual IDs you copied

4. **Run interconnector ingestion**:
   ```bash
   python3 ingest_interconnector_flows.py --start-year 2022 --end-year 2025
   ```

---

**Estimated Total Time**: 3-4 hours manual work  
**Priority**: HIGH (blocks NGSEA Feature D validation)  
**Status**: Ready to start NOW

**Good luck! 🚀**
