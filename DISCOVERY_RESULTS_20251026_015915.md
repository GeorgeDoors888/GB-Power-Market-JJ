# Dynamic Dataset Discovery Results

**Date**: 2025-10-26 01:59:15  
**Method**: Dynamic metadata query (no hardcoded lists)

---

## 📊 Summary

| Metric | Value |
|--------|-------|
| Total datasets in API | 82 |
| Successfully discovered | 44 |
| Failed/unavailable | 38 |
| Success rate | 53.7% |

---

## ✅ Available Datasets (44)

- **BOALF**: /datasets/BOALF/stream ⚠️ Bid Offer Acceptance Level - requires 1-day max range
- **BOD**: /datasets/BOD/stream
- **DISBSAD**: /datasets/DISBSAD/stream
- **FREQ**: /datasets/FREQ/stream
- **FUELHH**: /datasets/FUELHH/stream
- **FUELINST**: /datasets/FUELINST/stream
- **IMBALNGC**: /datasets/IMBALNGC/stream
- **INDDEM**: /datasets/INDDEM/stream
- **INDGEN**: /datasets/INDGEN/stream
- **MDP**: /datasets/MDP/stream
- **MDV**: /datasets/MDV/stream
- **MELNGC**: /datasets/MELNGC/stream
- **MELS**: /datasets/MELS/stream ⚠️ Maximum Export Limit - requires 1-hour max range
- **MID**: /datasets/MID/stream
- **MILS**: /datasets/MILS/stream ⚠️ Maximum Import Limit - requires 1-hour max range
- **MNZT**: /datasets/MNZT/stream
- **MZT**: /datasets/MZT/stream
- **NDF**: /datasets/NDF/stream
- **NDFD**: /datasets/NDFD/stream
- **NDFW**: /datasets/NDFW/stream
- **NDZ**: /datasets/NDZ/stream
- **NETBSAD**: /datasets/NETBSAD/stream
- **NONBM**: /datasets/NONBM/stream ⚠️ Non-BM STOR - requires 1-day max range
- **NTB**: /datasets/NTB/stream
- **NTO**: /datasets/NTO/stream
- **OCNMF3Y**: /datasets/OCNMF3Y/stream
- **OCNMF3Y2**: /datasets/OCNMF3Y2/stream
- **OCNMFD**: /datasets/OCNMFD/stream
- **OCNMFD2**: /datasets/OCNMFD2/stream
- **PN**: /datasets/PN/stream
- **QAS**: /datasets/QAS/stream
- **QPN**: /datasets/QPN/stream
- **RDRE**: /datasets/RDRE/stream
- **RDRI**: /datasets/RDRI/stream
- **RURE**: /datasets/RURE/stream
- **RURI**: /datasets/RURI/stream
- **SEL**: /datasets/SEL/stream
- **SIL**: /datasets/SIL/stream
- **TSDF**: /datasets/TSDF/stream
- **TSDFD**: /datasets/TSDFD/stream
- **TSDFW**: /datasets/TSDFW/stream
- **UOU2T14D**: /datasets/UOU2T14D/stream
- **UOU2T3YW**: /datasets/UOU2T3YW/stream
- **WINDFOR**: /datasets/WINDFOR/stream

## ❌ Failed Datasets (38)

- **FOU2T14D**: not_found_404 - Endpoint not found (may not support stream format)
- **FOU2T3YW**: not_found_404 - Endpoint not found (may not support stream format)
- **NOU2T14D**: not_found_404 - Endpoint not found (may not support stream format)
- **NOU2T3YW**: not_found_404 - Endpoint not found (may not support stream format)
- **IMBALANGC**: not_found_404 - Endpoint not found (may not support stream format)
- **INDO**: not_found_404 - Endpoint not found (may not support stream format)
- **INDOD**: not_found_404 - Endpoint not found (may not support stream format)
- **ITSDO**: not_found_404 - Endpoint not found (may not support stream format)
- **OCNMFW**: not_found_404 - Endpoint not found (may not support stream format)
- **OCNMFW2**: not_found_404 - Endpoint not found (may not support stream format)
- **TEMP**: not_found_404 - Endpoint not found (may not support stream format)
- **LOLPDM**: not_found_404 - Endpoint not found (may not support stream format)
- **SYS_WARN**: not_found_404 - Endpoint not found (may not support stream format)
- **SOSO**: not_found_404 - Endpoint not found (may not support stream format)
- **AGPT**: not_found_404 - Endpoint not found (may not support stream format)
- **AGWS**: not_found_404 - Endpoint not found (may not support stream format)
- **DGWS**: not_found_404 - Endpoint not found (may not support stream format)
- **DAG**: not_found_404 - Endpoint not found (may not support stream format)
- **IGCA**: not_found_404 - Endpoint not found (may not support stream format)
- **IGCPU**: not_found_404 - Endpoint not found (may not support stream format)
- **ATL**: not_found_404 - Endpoint not found (may not support stream format)
- **DATL**: not_found_404 - Endpoint not found (may not support stream format)
- **WATL**: not_found_404 - Endpoint not found (may not support stream format)
- **MATL**: not_found_404 - Endpoint not found (may not support stream format)
- **YATL**: not_found_404 - Endpoint not found (may not support stream format)
- **YAFM**: not_found_404 - Endpoint not found (may not support stream format)
- **ABUC**: not_found_404 - Endpoint not found (may not support stream format)
- **PPBR**: not_found_404 - Endpoint not found (may not support stream format)
- **CCM**: not_found_404 - Endpoint not found (may not support stream format)
- **FEIB**: not_found_404 - Endpoint not found (may not support stream format)
- **AOBE**: not_found_404 - Endpoint not found (may not support stream format)
- **BEB**: not_found_404 - Endpoint not found (may not support stream format)
- **CBS**: not_found_404 - Endpoint not found (may not support stream format)
- **PBC**: not_found_404 - Endpoint not found (may not support stream format)
- **TUDM**: not_found_404 - Endpoint not found (may not support stream format)
- **SAA-I062**: not_found_404 - Endpoint not found (may not support stream format)
- **RZDF**: not_found_404 - Endpoint not found (may not support stream format)
- **RZDR**: not_found_404 - Endpoint not found (may not support stream format)

---

## 🎯 Key Findings

### Datasets with Special Requirements

Found 4 datasets that require special handling:

- **BOALF**: Bid Offer Acceptance Level - requires 1-day max range
- **MELS**: Maximum Export Limit - requires 1-hour max range
- **MILS**: Maximum Import Limit - requires 1-hour max range
- **NONBM**: Non-BM STOR - requires 1-day max range

### Datasets with Nested Structures

None found - all datasets have flat structures.

---

## 📋 Usage

```bash
# Use the generated manifest with download scripts
python download_last_7_days.py --manifest insights_manifest_dynamic.json

# Or download all 2025 data
python download_all_2025_data.py --manifest insights_manifest_dynamic.json
```

## 🔄 Re-running Discovery

To update the dataset list (e.g., when Elexon adds new datasets):

```bash
python discover_all_datasets_dynamic.py
```

No need to manually update code - it queries the API automatically!
