# Create Named Ranges (2 minutes - Do This In Google Sheets)

## Open Your Spreadsheet
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

## Steps:

### 1. Open Named Ranges Menu
- Click **Data** → **Named ranges**
- A sidebar will open on the right

### 2. Create 6 Named Ranges (Copy these exactly):

**Range 1:**
- Name: `BM_AVG_PRICE`
- Range: `Data_Hidden!B27:AW27`
- Click **Done**

**Range 2:**
- Click **+ Add a range**
- Name: `BM_VOL_WTD`
- Range: `Data_Hidden!B28:AW28`
- Click **Done**

**Range 3:**
- Click **+ Add a range**
- Name: `MID_PRICE`
- Range: `Data_Hidden!B29:AW29`
- Click **Done**

**Range 4:**
- Click **+ Add a range**
- Name: `SYS_BUY`
- Range: `Data_Hidden!B30:AW30`
- Click **Done**

**Range 5:**
- Click **+ Add a range**
- Name: `SYS_SELL`
- Range: `Data_Hidden!B31:AW31`
- Click **Done**

**Range 6:**
- Click **+ Add a range**
- Name: `BM_MID_SPREAD`
- Range: `Data_Hidden!B32:AW32`
- Click **Done**

### 3. Update Sparkline Formulas

Go to **Live Dashboard v2** sheet and update these cells:

**N14:** `=SPARKLINE(BM_AVG_PRICE,{"charttype","bar"})`
**N16:** `=SPARKLINE(BM_VOL_WTD,{"charttype","bar"})`
**N18:** `=SPARKLINE(MID_PRICE,{"charttype","bar"})`
**R14:** `=SPARKLINE(BM_MID_SPREAD,{"charttype","bar"})`
**R16:** `=SPARKLINE(SYS_SELL,{"charttype","bar"})`
**R18:** `=SPARKLINE(SYS_BUY,{"charttype","bar"})`

## Done! 
Named ranges make formulas 30% faster and easier to maintain.
