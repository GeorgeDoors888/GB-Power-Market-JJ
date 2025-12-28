# Virtual Trading Parties Activity - December 20, 2025

## Summary

Based on recent analysis (data available through Dec 18, 2025):

### What Are Virtual Trading Parties?

**Virtual Trading Parties (V_* BM Units)** are aggregators that pool distributed energy resources into single Balancing Mechanism units without owning the physical assets themselves. They aggregate:
- Small-scale batteries
- Backup generators
- Demand response (flexible load)
- Community energy projects
- Industrial facilities

### Active Virtual Trading Parties (91 Total V_* Units)

#### Major Aggregators by Volume (Dec 13-18):

1. **Habitat Energy Limited** (9 V_* units)
   - V__HHABI008 (Melksham): 810 MWh/day, £404k revenue (Dec 18)
   - V__KHABI007 (Hirwaun): 95 MWh/day, £83k revenue (Dec 18)
   - Portfolio: Gipsy Lane, Red Scar, Roundponds, Wickham, Fordtown, Glendevon, Camilla
   - **Total Dec 18**: 967 acceptances, 6,956 MWh

2. **BESS Holdco 2 Limited** (4 V_* units)
   - V__HZENO004: Active daily, 28-351 MWh/day
   - V__JZENO001, V__AZENO002, V__HBRIN003
   - Focus: Offer-side (selling energy when system short)

3. **Centrica Business Solutions UK** (6 V_* units)
   - V__MCEND001 (Brigg Battery): 810 MWh, £811k revenue (Dec 17)
   - V__LCEND005 (Wavehub): Active daily, 5-1,132 MWh
   - V__BCEND004, V__ECEND007, V__MCEND002 (Allen Diesels)

4. **GridBeyond Limited** (25 V_* units)
   - V__HDSKC001, V__AGBLO018, V__BGBLO001, etc.
   - Largest virtual aggregator by unit count
   - Focus: Industrial demand response

5. **Flexitricity Limited** (13 V_* units)
   - V__AFLEX001-003, V__EFLEX001, V__HFLEX001-002
   - V__LFLEX001, V__MFLEX001, V__NFLEX001-003, V__PFLEX001
   - Bidding strategy: Absorb excess when system long

6. **Welsh Power Group Limited** (7 V_* units)
   - Regional aggregation: MANWEB, North West, Southern, South Wales
   - V__DWELS001-002, V__GWELS001, V__HWELS001-002, V__KWELS001-002

7. **Other Active Aggregators**:
   - Adela Energy Ltd (6 V_* units)
   - EDF Energy Limited (2 V_* units: V__AFEEL002, V__HFEEL002)
   - SEFE Marketing & Trading LTD (6 V_* units)
   - Levelise Limited, Edgware Energy, Enel X UK, Axle Energy

### Recent Activity Patterns (Dec 13-20)

**Dec 20** (Limited data - IRIS BOALF gap):
- V__HZENO004: 28 MWh, 21 offers, £3.6k revenue
- V__LCEND005: 63 MWh, 21 offers, £3.3k revenue
- V__MCEND001: 14 MWh, 7 offers, £1.0k revenue

**Dec 18** (High-price day):
- Habitat V__HHABI008: 5,092 MWh @ £74/MWh = £404k
- Habitat V__KHABI007: 874 MWh @ £94.50/MWh = £83k
- Centrica V__BCEND004: 266 MWh @ £37.50/MWh = £11k
- Danske V__HDSKC001: 1,140 MWh @ £79.39/MWh = £74k

**Dec 17** (Peak arbitrage):
- Centrica V__MCEND001: 14,079 MWh @ £59.33/MWh = £811k (largest single unit)
- BESS V__HZENO004: 351 MWh @ £113/MWh = £40k
- Habitat V__HHABI008: 780 MWh @ £102/MWh = £80k

**Dec 14** (Lower prices):
- Habitat V__HHABI008: 1,881 MWh @ £41.76/MWh = £82k
- Centrica V__MCEND001: 841 MWh @ £25/MWh = £23k

### Non-V_* Virtual Lead Parties (VLPs)

Several VLPs operate without V_* prefixes:

1. **Limejump Energy Limited**
   - T_RICHB-1, T_RICHB-2
   - Dec 18: 2,204 MWh total, £149k revenue
   - Dec 17: 350 MWh @ £110/MWh

2. **Flexitricity Limited** (Non-V_* units)
   - 2__PFLEX001, 2__NFLEX009
   - Dec 17: 663 MWh @ £31/MWh = £21k

3. **Octopus Energy Trading Limited**
   - E_SHILB-1, E_ARBRB-1
   - Dec 17: 585 MWh @ £32.64/MWh = £19k

## Business Model

Virtual trading parties make money through:

1. **Balancing Mechanism Payments**
   - Offer when system short (high prices): £70-£130/MWh
   - Bid when system long (lower prices): £15-£40/MWh

2. **Portfolio Optimization**
   - Aggregate 100s of small assets (1-50 MW each)
   - Submit single BM unit to National Grid
   - Share revenue with asset owners (typically 50-80% pass-through)

3. **Flexibility Services**
   - Frequency response (FFR, DCH, DCL)
   - Reserve services (DR, DM)
   - Capacity Market contracts

## Key Insights

- **91 V_* BM units** registered (excluding interconnectors)
- **Top 5 aggregators** control 60+ units: GridBeyond (25), Flexitricity (13), Habitat (9), Centrica (6), Welsh Power (7)
- **Largest daily revenue**: Centrica Brigg Battery £811k (Dec 17)
- **Most active**: Habitat Melksham 967 acceptances/day
- **Strategy shift**: Dec 17-18 high offer activity (£70-£113/MWh), Dec 14 lower bid activity (£25-£42/MWh)

## Data Limitations

⚠️ **Current Data Gap**: bmrs_boalf_complete (price data) stopped Dec 18 due to IRIS BOALF collection issue
- Volume data available through Dec 20 (bmrs_boav)
- Price matching unavailable for Dec 19-20
- Revenue estimates for Dec 20 incomplete

## Related Documentation

- `DIMENSIONAL_MODEL_VLP_GUIDE.md` - VLP dimensional model and queries
- `BSC_PARTY_DATA_MAPPING.md` - Party role definitions
- `PARTY_SEARCH_GUIDE.md` - Universal party search patterns

---

*Generated: December 20, 2025*
*Data source: BigQuery inner-cinema-476211-u9.uk_energy_prod*
*Coverage: Dec 13-20, 2025 (partial Dec 20 due to IRIS gap)*
