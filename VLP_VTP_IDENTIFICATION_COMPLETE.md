# VLP/VTP Identification Complete

**Date**: December 20, 2025
**Status**: ✅ Complete

## Summary

Successfully fetched all BSC (Balancing and Settlement Code) parties from Elexon Insights API and identified Virtual Lead Parties (VLP) and Virtual Trading Parties (VTP).

## Tables Created

### 1. `dim_party` - BSC Party Master Table
- **351 total parties** in the UK energy market
- **18 VLP parties** identified (have virtual aggregation units)
- **351 VTP parties** (all parties with BM Units can be VTP)
- Columns: `party_name`, `party_id`, `bmu_count`, `is_vlp`, `is_vtp`

### 2. `dim_bmu` - Updated with VLP/VTP Flags
- **2,717 BM Units** updated with party role flags
- Added columns: `is_vlp`, `is_vtp`
- Now includes party classification for join queries

## Virtual Lead Parties (VLP) - Top 18

| Party Name | Party ID | Total BMUs | Virtual Units |
|------------|----------|------------|---------------|
| Flexitricity Limited | FLEXTRCY | 59 | 12 |
| GridBeyond Limited | ENDECO | 26 | 25 |
| Danske Commodities A/S | DANSKE | 18 | 1 |
| SEFE Marketing & Trading | GAZPROM | 18 | 6 |
| Erova Energy Limited | EROVAIRL | 13 | 2 |
| Habitat Energy Limited | HABITAT | 12 | 9 |
| Edgware Energy Limited | EDGWARE | 8 | 2 |
| Welsh Power Group | WELSHPOW | 7 | 7 |
| Adela Energy Ltd | ADELA | 6 | 6 |
| Centrica Business Solutions | CENDEPUK | 6 | 6 |
| BESS Holdco 2 (Zenobe) | ZENOBE1 | 4 | 4 |
| EDF Energy Limited | LONDELEC | 4 | 2 |
| Levelise Limited | LEVELISE | 3 | 3 |
| Forsa Trading Limited | FORSA | 2 | 2 |
| Axle Energy Limited | AXLEENER | 1 | 1 |
| Enel X UK Limited | ENOC | 1 | 1 |
| Exergy Solutions Limited | EXERGY | 1 | 1 |
| Joulen | POWONTEC | 1 | 1 |

## Key Findings

### Flexitricity Status
- **✅ VLP + VTP**: Both Virtual Lead Party AND Virtual Trading Party
- **59 total BM Units**:
  - 41 battery storage units (2__FLEX*)
  - 12 virtual aggregation units (V__FLEX*)
  - 6 traditional/embedded units
- **Operates in both models**:
  - Physical battery arbitrage (VTP role)
  - Demand-side aggregation (VLP role)

### Virtual Unit Statistics
- **91 total virtual units** (V__* prefix) across all parties
- **93.3 MW** total registered capacity (most are 0 MW - aggregate distributed assets)
- **GridBeyond** has most virtual units (25)
- **Flexitricity** ranks 2nd with 12 virtual units

## Business Models Identified

### 1. Pure VLP Aggregators
- **GridBeyond**: 25 virtual units, minimal physical assets
- **Habitat Energy**: 9 virtual units, demand response focus
- **Welsh Power**: 7 virtual units, distributed generation

### 2. Hybrid VLP + Battery Operator
- **Flexitricity**: 12 virtual + 41 battery units
- **BESS Holdco 2 (Zenobe)**: 4 virtual + battery portfolio
- **EDF Energy**: 2 virtual + traditional generation

### 3. Trading Companies with Virtual Portfolios
- **Danske Commodities**: Energy trader with 1 virtual unit
- **SEFE**: Gas/power trader with 6 virtual units
- **Centrica**: Retailer with 6 virtual units for customer portfolios

## Usage Examples

### Query all VLP parties:
```sql
SELECT *
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_party`
WHERE is_vlp = TRUE
ORDER BY bmu_count DESC
```

### Query Flexitricity's virtual units:
```sql
SELECT
    b.bm_unit_id,
    b.bmu_name,
    b.gsp_group,
    p.is_vlp,
    p.is_vtp
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
    ON b.lead_party_id = p.party_id
WHERE b.lead_party_id = 'FLEXTRCY'
    AND b.is_virtual_unit = TRUE
```

### Compare VLP revenue across parties:
```sql
SELECT
    p.party_name,
    p.is_vlp,
    COUNT(b.bmUnit) as acceptances,
    SUM(b.acceptanceVolume * b.acceptancePrice) / 1000 as revenue_k_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete` b
INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` d
    ON b.bmUnit = d.bm_unit_id
INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.dim_party` p
    ON d.lead_party_id = p.party_id
WHERE p.is_vlp = TRUE
    AND DATE(b.acceptanceTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    AND b.validation_flag = 'Valid'
GROUP BY p.party_name, p.is_vlp
ORDER BY revenue_k_gbp DESC
```

## Data Source

- **Elexon Insights API**: `https://data.elexon.co.uk/bmrs/api/v1/reference/bmunits/all`
- **Method**: REST API call, public endpoint (no auth required)
- **Records**: 2,829 BM Units retrieved
- **Date**: December 20, 2025

## Technical Details

### VLP Identification Logic
Virtual Lead Party (VLP) flag set to `TRUE` if:
- Party is Lead Party for at least one BM Unit with ID starting with `V_` or `V__`
- These are Secondary BM Units used for aggregation

### VTP Identification Logic
Virtual Trading Party (VTP) flag set to `TRUE` if:
- Party is Lead Party for any BM Unit (has `bmu_count > 0`)
- Can participate in Balancing Mechanism trading

### Why All VLPs are also VTPs
- VLP status requires having Secondary BM Units (V__* pattern)
- Having any BM Unit means party can trade → VTP
- Therefore: `is_vlp = TRUE` implies `is_vtp = TRUE`
- But: `is_vtp = TRUE` does NOT imply `is_vlp = TRUE` (333 VTPs are not VLPs)

## Next Steps

1. **Revenue Analysis**: Compare VLP vs non-VLP revenue in BM
2. **Virtual Unit Performance**: Analyze acceptance rates for V__* units
3. **Geographic Distribution**: Map virtual units by GSP Group
4. **Refresh Cadence**: Re-run monthly to catch new VLP entrants
5. **Party Roles API**: Attempt to fetch formal BSC party roles if endpoint becomes available

## Files Created

- `fetch_bsc_parties_vlp_vtp.py` - Script to fetch and classify parties
- `dim_party` table in BigQuery - Party master with VLP/VTP flags
- `dim_bmu` table updated - Added `is_vlp` and `is_vtp` columns

## Contact

For questions about this analysis:
- Repository: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
- Data Platform: BigQuery project `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod`

---

*Last Updated: December 20, 2025*
