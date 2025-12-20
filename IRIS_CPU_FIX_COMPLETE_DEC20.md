# IRIS CPU Performance Fix - COMPLETE ✅

**Date**: December 20, 2025
**Issue**: IRIS uploader consuming 48% CPU on powerful Dell server
**Result**: Reduced to 4.4% total CPU (91% reduction)

---

## Problem Summary

The IRIS uploader was continuously consuming 48% CPU due to:
1. **Rescanning ALL files every 5 seconds** - no state tracking, processed 4,242 files per scan
2. **60+ unsupported IRIS message types** - files with unknown types stayed in directory and were rescanned
3. **No automatic archiving** - successfully processed files accumulated in data directory
4. **Variable name bug** - archive code used `file_path` instead of `filepath`, causing crashes

## Solution Implemented

### 1. Expanded TABLE_MAPPING Support
**Before**: 13 IRIS message types supported
**After**: 40 IRIS message types supported

Added support for:
- **Forecast types**: FOU2T14D, FOU2T3YW, UOU2T3YW, UOU2T14D, NOU2T3YW, NOU2T14D
- **Margin forecasts**: OCNMFW, OCNMFW2, OCNMFD2, OCNMF3Y2
- **System data**: FUELHH, QPN, NETBSAD, ITSDO, SIL, IMBALNGC, SOSO
- **Unit limits**: MELS, MILS, SEL, RURE, NDZ
- **Balancing**: AOBE, CBS, TSDF, AGWS, ATL

### 2. Created 25 New BigQuery Tables
Created tables for all new IRIS message types:
```
✅ bmrs_fuelhh_iris      ✅ bmrs_fou2t14d_iris    ✅ bmrs_fou2t3yw_iris
✅ bmrs_uou2t3yw_iris    ✅ bmrs_uou2t14d_iris    ✅ bmrs_nou2t3yw_iris
✅ bmrs_nou2t14d_iris    ✅ bmrs_ocnmfw_iris      ✅ bmrs_ocnmfw2_iris
✅ bmrs_ocnmfd2_iris     ✅ bmrs_ocnmf3y2_iris    ✅ bmrs_qpn_iris
✅ bmrs_netbsad_iris     ✅ bmrs_itsdo_iris       ✅ bmrs_sil_iris
✅ bmrs_aobe_iris        ✅ bmrs_cbs_iris         ✅ bmrs_tsdf_iris
✅ bmrs_sel_iris         ✅ bmrs_rure_iris        ✅ bmrs_imbalngc_iris
✅ bmrs_soso_iris        ✅ bmrs_ndz_iris         ✅ bmrs_agws_iris
✅ bmrs_atl_iris
```

### 3. Fixed Archive Bug
**Problem**: Code used `file_path` but variable was `filepath`
**Fix**: Corrected variable names in archive section (lines 222, 225, 227)

### 4. Time-Based Filtering (Already Applied)
Files modified > 2 hours ago are ignored by scanner:
```python
cutoff_time = time.time() - 7200  # 2 hours ago
```

## Results

### CPU Usage
- **Before**: 48.5% (uploader alone)
- **After**: 4.4% (uploader + client combined)
- **Reduction**: 91% decrease

### File Processing
- **Before**: "Successfully processed 0/1408 files" every scan
- **After**: "No files to process" (all recent files processed immediately)
- **Old files**: 3,171 files moved to `/opt/iris-pipeline/archive/`

### Current Status
```
IRIS Client (PID 47172):     1.6% CPU, 49 MB RAM  - Downloading from Azure
IRIS Uploader (PID 46608):   2.8% CPU, 155 MB RAM - Processing to BigQuery
Total Resource Usage:        4.4% CPU, 0.1% Memory
```

### Data Coverage
- **Historical tables**: 63 tables (2020-present, Elexon API)
- **IRIS tables**: 40 tables (last 24-48h, Azure streaming)
- **Total BMRS coverage**: 103 tables across both pipelines

## Files Modified

1. `/opt/iris-pipeline/scripts/iris_to_bigquery_unified.py`
   - Expanded TABLE_MAPPING from 13 → 40 types (lines 35-77)
   - Fixed archive variable names (lines 222, 225, 227)

2. Created `/home/george/GB-Power-Market-JJ/create_missing_iris_tables.py`
   - Script to create 25 new BigQuery tables
   - Successfully executed, all tables created

## Verification Commands

```bash
# Check CPU usage
ps aux | grep -E "iris_to_bigquery|client.py" | grep -v grep

# Check file counts
echo "Active: $(find /opt/iris-pipeline/data -name '*.json' -mmin -120 | wc -l)"
echo "Archived: $(find /opt/iris-pipeline/archive -name '*.json' | wc -l)"

# Monitor logs
tail -f /opt/iris-pipeline/logs/iris_uploader_$(date +%Y%m%d).log
tail -f /opt/iris-pipeline/logs/iris_client.log

# Check BigQuery tables
bq ls inner-cinema-476211-u9:uk_energy_prod | grep iris | wc -l  # Should show 40
```

## Key Insights

1. **State tracking is critical** - Rescanning processed files wastes massive CPU
2. **Complete type coverage matters** - Unknown types create a processing backlog
3. **Time-based filtering helps** - But doesn't solve root cause if types are missing
4. **Archive on success** - Files should be removed/archived after successful upload
5. **Variable naming bugs** - Can cause crashes even when logic is correct

## Future Improvements

### Recommended
1. **State file tracking** - Maintain list of processed file hashes to avoid reprocessing
2. **Monitoring alerts** - Alert if CPU > 10% for more than 5 minutes
3. **Unknown type handling** - Log unknown types once, then blacklist to reduce spam
4. **Automatic schema detection** - Dynamically create tables for new IRIS types

### Optional
1. **Systemd services** - Deploy proper systemd units for auto-start/restart
2. **Batch processing** - Process files in batches of 100 instead of one-by-one
3. **Compression** - Compress archived JSON files to save disk space
4. **Retention policy** - Delete archived files older than 30 days

## References

- **Copilot Instructions**: `.github/copilot-instructions.md`
- **Architecture Guide**: `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`
- **IRIS Deployment**: `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`
- **Original CPU Issue Doc**: `IRIS_UPLOADER_CPU_ISSUE_FIX.md`

---

**Status**: ✅ COMPLETE - Production deployment successful
**Next Steps**: Monitor for 24 hours, then mark as stable

*Generated: December 20, 2025 11:13 UTC*
