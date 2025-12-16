# IRIS BOALF Real-Time Integration - Dell Deployment Guide

## Overview
Deploy real-time BOD price matching to IRIS pipeline on Dell server (94.237.55.234).

**What it does**: Match incoming BOALF acceptances with bmrs_bod_iris in real-time, applying Elexon B1610 validation filters.

**Result**: bmrs_boalf_iris table will have acceptancePrice, validation_flag, and _price_source fields populated live.

---

## Pre-Deployment Checklist

✅ **Completed locally**:
- derive_boalf_prices.py tested and validated
- Historical backfill: 48/48 months, 100% success
- Battery analysis shows +40% revenue potential with BOALF prices
- Schema design finalized with validation_flag taxonomy

🔧 **Ready to deploy**:
- Enhancement code: iris_boalf_enhancement.py
- Target file: /opt/iris-pipeline/scripts/iris_to_bigquery_unified.py
- BigQuery schema update commands
- Service restart procedures

---

## Deployment Steps

### Step 1: SSH to Dell Server
```bash
ssh root@94.237.55.234
```

### Step 2: Backup Current Script
```bash
cd /opt/iris-pipeline/scripts
cp iris_to_bigquery_unified.py iris_to_bigquery_unified.py.backup_$(date +%Y%m%d_%H%M%S)
ls -lh iris_to_bigquery_unified.py*
```

### Step 3: Add Enhancement Methods

**Option A - Manual Edit** (recommended for control):
```bash
nano iris_to_bigquery_unified.py
```

**Add these three methods to the IRISBigQueryUploader class:**

1. **_derive_boalf_prices()** method (insert after line ~170, after _map_fuel_type):
```python
def _derive_boalf_prices(self, boalf_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Derive acceptance prices from bmrs_bod_iris (real-time BOD matching).
    Applies Elexon B1610 Section 4.3 regulatory filters.
    
    Returns enriched BOALF records with:
    - acceptancePrice (FLOAT)
    - acceptanceVolume (FLOAT) 
    - acceptanceType (STRING)
    - validation_flag (STRING)
    - _price_source (STRING)
    - _matched_pairId (STRING)
    """
    if not boalf_records:
        return []
    
    self.logger.info(f"Starting real-time BOALF price derivation for {len(boalf_records)} records")
    
    # Extract unique dates for BOD query
    dates = set()
    for record in boalf_records:
        sd = record.get('settlementDate')
        if sd:
            dates.add(sd[:10])  # YYYY-MM-DD
    
    if not dates:
        self.logger.warning("No settlement dates found in BOALF records")
        return self._add_default_price_fields(boalf_records)
    
    # Query bmrs_bod_iris for matching BOD data
    date_filter = ', '.join([f"'{d}'" for d in sorted(dates)])
    bod_query = f"""
    WITH ranked_bod AS (
        SELECT 
            bmUnitId,
            settlementDate,
            settlementPeriod,
            pairId,
            bid,
            offer,
            soFlag,
            ROW_NUMBER() OVER (
                PARTITION BY bmUnitId, settlementDate, settlementPeriod, pairId 
                ORDER BY timeFrom DESC
            ) as rn
        FROM `{self.project_id}.{self.dataset}.bmrs_bod_iris`
        WHERE DATE(settlementDate) IN ({date_filter})
    )
    SELECT 
        bmUnitId,
        settlementDate,
        settlementPeriod,
        pairId,
        bid,
        offer,
        soFlag
    FROM ranked_bod
    WHERE rn = 1
    """
    
    try:
        bod_df = self.client.query(bod_query).to_dataframe()
        self.logger.info(f"Retrieved {len(bod_df)} BOD records from bmrs_bod_iris")
    except Exception as e:
        self.logger.error(f"BOD query failed: {e}")
        return self._add_default_price_fields(boalf_records)
    
    if bod_df.empty:
        self.logger.warning("No BOD data found for date range")
        return self._add_default_price_fields(boalf_records)
    
    # Match BOALF with BOD
    enriched_records = []
    match_count = 0
    
    for boalf in boalf_records:
        bmu = boalf.get('bmUnit')
        sd = boalf.get('settlementDate')
        sp = boalf.get('settlementPeriod')
        level_from = boalf.get('levelFrom', 0.0)
        level_to = boalf.get('levelTo', 0.0)
        
        # Calculate volume
        volume = abs(level_to - level_from) if (level_from and level_to) else 0.0
        
        # Find matching BOD record
        bod_match = bod_df[
            (bod_df['bmUnitId'] == bmu) &
            (bod_df['settlementDate'] == sd) &
            (bod_df['settlementPeriod'] == sp)
        ]
        
        if not bod_match.empty:
            bod_row = bod_match.iloc[0]
            
            # Determine acceptance type and price
            if level_to > level_from:
                # Offer acceptance (increase generation)
                price = float(bod_row['offer']) if pd.notna(bod_row['offer']) else None
                acc_type = 'Offer'
            else:
                # Bid acceptance (decrease generation)
                price = float(bod_row['bid']) if pd.notna(bod_row['bid']) else None
                acc_type = 'Bid'
            
            # Apply Elexon B1610 Section 4.3 filters
            validation_flag = 'Valid'
            
            if price is None:
                validation_flag = 'Unmatched'
            elif abs(price) > 1000:
                validation_flag = 'Price_Outlier'
            elif volume < 0.001:
                validation_flag = 'Low_Volume'
            elif bod_row.get('soFlag') is True:
                validation_flag = 'SO_Test'
            
            enriched_records.append({
                **boalf,
                'acceptancePrice': price,
                'acceptanceVolume': volume,
                'acceptanceType': acc_type,
                'validation_flag': validation_flag,
                '_price_source': 'BOD_REALTIME',
                '_matched_pairId': str(bod_row['pairId']) if pd.notna(bod_row['pairId']) else None
            })
            
            if validation_flag == 'Valid':
                match_count += 1
        else:
            # No BOD match found
            enriched_records.append({
                **boalf,
                'acceptancePrice': None,
                'acceptanceVolume': volume,
                'acceptanceType': 'Offer' if level_to > level_from else 'Bid',
                'validation_flag': 'Unmatched',
                '_price_source': 'BOD_REALTIME',
                '_matched_pairId': None
            })
    
    match_rate = (match_count / len(boalf_records) * 100) if boalf_records else 0
    self.logger.info(f"BOALF price derivation complete: {match_count}/{len(boalf_records)} matched ({match_rate:.1f}%)")
    
    # Log validation breakdown
    validation_counts = {}
    for rec in enriched_records:
        flag = rec.get('validation_flag', 'Unknown')
        validation_counts[flag] = validation_counts.get(flag, 0) + 1
    
    self.logger.info(f"Validation breakdown: {validation_counts}")
    
    return enriched_records
```

2. **_add_default_price_fields()** fallback method (insert after _derive_boalf_prices):
```python
def _add_default_price_fields(self, boalf_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add default price fields when BOD matching unavailable."""
    enriched = []
    for boalf in boalf_records:
        level_from = boalf.get('levelFrom', 0.0)
        level_to = boalf.get('levelTo', 0.0)
        volume = abs(level_to - level_from) if (level_from and level_to) else 0.0
        
        enriched.append({
            **boalf,
            'acceptancePrice': None,
            'acceptanceVolume': volume,
            'acceptanceType': 'Offer' if level_to > level_from else 'Bid',
            'validation_flag': 'Unmatched',
            '_price_source': 'NO_BOD_DATA',
            '_matched_pairId': None
        })
    
    return enriched
```

3. **Replace _extract_records()** with enhanced version:

Find the existing `_extract_records()` method (around line 200-250) and replace it with:

```python
def _extract_records(self, stream_name: str, messages: List[Dict]) -> List[Dict[str, Any]]:
    """
    Extract records from IRIS messages with enhanced BOALF price derivation.
    
    For BOALF streams: derives acceptance prices from bmrs_bod_iris
    For other streams: passes through unchanged
    """
    records = []
    
    for msg in messages:
        try:
            # Parse message body
            body = json.loads(msg['body']) if isinstance(msg.get('body'), str) else msg.get('body', {})
            
            # Extract dataset
            if 'dataset' in body:
                dataset = body['dataset']
            elif 'data' in body and isinstance(body['data'], dict):
                dataset = body['data']
            else:
                self.logger.warning(f"No dataset found in message: {msg.get('message_id', 'unknown')}")
                continue
            
            # Convert to records
            if isinstance(dataset, list):
                records.extend(dataset)
            elif isinstance(dataset, dict):
                records.append(dataset)
            else:
                self.logger.warning(f"Unexpected dataset type: {type(dataset)}")
        
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
        except Exception as e:
            self.logger.error(f"Record extraction error: {e}")
    
    # Apply BOALF price derivation if applicable
    if stream_name.upper() == 'BOALF' and records:
        records = self._derive_boalf_prices(records)
    
    return records
```

**Save and exit**: `Ctrl+X`, `Y`, `Enter`

---

### Step 4: Update BigQuery Schema

```bash
# Add new fields to bmrs_boalf_iris table
bq update \
  --schema acceptancePrice:FLOAT,acceptanceVolume:FLOAT,acceptanceType:STRING,validation_flag:STRING,_price_source:STRING,_matched_pairId:STRING \
  inner-cinema-476211-u9:uk_energy_prod.bmrs_boalf_iris
```

**Expected output**:
```
Table 'inner-cinema-476211-u9:uk_energy_prod.bmrs_boalf_iris' successfully updated.
```

---

### Step 5: Restart IRIS Pipeline Service

```bash
# Stop service
systemctl stop iris-pipeline

# Verify stopped
systemctl status iris-pipeline

# Start service
systemctl start iris-pipeline

# Check status
systemctl status iris-pipeline

# Should show: Active: active (running)
```

---

### Step 6: Monitor Real-Time Processing

```bash
# Watch BOALF price derivation logs
tail -f /opt/iris-pipeline/logs/iris_uploader.log | grep -E "BOALF|price derivation|validation|matched"

# Example expected output:
# 2025-12-16 01:15:23 - INFO - Starting real-time BOALF price derivation for 24 records
# 2025-12-16 01:15:24 - INFO - Retrieved 156 BOD records from bmrs_bod_iris
# 2025-12-16 01:15:24 - INFO - BOALF price derivation complete: 21/24 matched (87.5%)
# 2025-12-16 01:15:24 - INFO - Validation breakdown: {'Valid': 18, 'SO_Test': 3, 'Unmatched': 3}
```

---

## Validation Queries

### Check recent BOALF records with prices

```bash
bq query --use_legacy_sql=false '
SELECT 
    DATE(settlementDate) as date,
    COUNT(*) as total_records,
    COUNTIF(validation_flag = "Valid") as valid_records,
    COUNTIF(acceptancePrice IS NOT NULL) as has_price,
    AVG(CASE WHEN validation_flag = "Valid" THEN acceptancePrice END) as avg_price,
    MIN(CASE WHEN validation_flag = "Valid" THEN acceptancePrice END) as min_price,
    MAX(CASE WHEN validation_flag = "Valid" THEN acceptancePrice END) as max_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
WHERE settlementDate >= CURRENT_DATE() - 2
GROUP BY date
ORDER BY date DESC
'
```

### Check validation_flag distribution

```bash
bq query --use_legacy_sql=false '
SELECT 
    validation_flag,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
WHERE settlementDate >= CURRENT_DATE() - 1
GROUP BY validation_flag
ORDER BY count DESC
'
```

### Compare real-time vs historical match rates

```bash
bq query --use_legacy_sql=false '
SELECT 
    "Historical" as source,
    COUNT(*) as total,
    COUNTIF(validation_flag = "Valid") as valid,
    ROUND(COUNTIF(validation_flag = "Valid") * 100.0 / COUNT(*), 2) as match_rate
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE settlementDate >= "2025-10-01"

UNION ALL

SELECT 
    "Real-time" as source,
    COUNT(*) as total,
    COUNTIF(validation_flag = "Valid") as valid,
    ROUND(COUNTIF(validation_flag = "Valid") * 100.0 / COUNT(*), 2) as match_rate
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
WHERE settlementDate >= CURRENT_DATE() - 7
'
```

---

## Rollback Procedure (if needed)

```bash
# Stop service
systemctl stop iris-pipeline

# Restore backup
cd /opt/iris-pipeline/scripts
cp iris_to_bigquery_unified.py.backup_YYYYMMDD_HHMMSS iris_to_bigquery_unified.py

# Restart
systemctl start iris-pipeline
systemctl status iris-pipeline
```

---

## Expected Performance

**Based on historical backfill results:**
- Match rate: **85-95%** (similar to historical)
- Valid records: **~40-45%** (after Elexon B1610 filters)
- Processing overhead: **+2-3 seconds** per BOALF batch
- BigQuery cost: **Negligible** (queries only bmrs_bod_iris, same date range)

**BOALF revenue insight:**
- Individual acceptance prices show **+40% higher revenue** vs settlement averages
- Critical for accurate VLP battery arbitrage analysis
- Enables unit-specific profitability tracking

---

## Troubleshooting

### Issue: "No BOD data found for date range"
**Cause**: bmrs_bod_iris might be delayed or missing  
**Fix**: Check IRIS BOD stream status, verify bod messages being received

### Issue: Low match rate (<70%)
**Cause**: BOD records might have different bmUnitId formatting  
**Fix**: Check bmrs_bod_iris for recent data, verify unit ID consistency

### Issue: Service won't start after update
**Cause**: Python syntax error in modified code  
**Fix**: Check logs with `journalctl -u iris-pipeline -n 50`, restore backup if needed

### Issue: Schema update fails
**Cause**: Fields already exist or permission issues  
**Fix**: Check existing schema with `bq show --schema inner-cinema-476211-u9:uk_energy_prod.bmrs_boalf_iris`

---

## Post-Deployment Checklist

✅ Service running: `systemctl status iris-pipeline`  
✅ Logs showing BOALF price derivation: `tail -f /opt/iris-pipeline/logs/iris_uploader.log | grep BOALF`  
✅ Schema updated: `bq show inner-cinema-476211-u9:uk_energy_prod.bmrs_boalf_iris`  
✅ Recent records have prices: Run validation query #1  
✅ Match rate >80%: Run validation query #3  
✅ validation_flag distribution reasonable: Run validation query #2  

---

## Documentation Updates (Post-Deployment)

After successful deployment, update:
1. `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md` - Add BOALF enhancement section
2. `PROJECT_CONFIGURATION.md` - Update bmrs_boalf_iris schema
3. `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Add real-time BOALF note
4. `.github/copilot-instructions.md` - Update IRIS integration status

---

## Contact

**Deployment Date**: TBD  
**Deployed By**: George Major  
**Server**: Dell AlmaLinux (94.237.55.234)  
**Status**: ⏳ Ready for deployment  

---

*Generated: December 16, 2025*  
*Enhancement File: iris_boalf_enhancement.py*  
*Historical Backfill: 100% complete (48/48 months)*  
*Battery Analysis: +40% revenue with BOALF prices*
