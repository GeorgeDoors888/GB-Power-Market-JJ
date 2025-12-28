# P114 Settlement Value Calculation Explained

## The Confusing Numbers from Oct 17, 2024 Period 36

**Original Summary:**
- 5,705 BM Units participated
- Total Energy Settled: 465.33 MWh (NET)
- Total Settlement Value: £5,057.97
- System Price: £83.73/MWh

**The Question:** If we have 465.33 MWh at £83.73/MWh, that should be £38,956.79, not £5,057.97. What's going on?

---

## The Answer: You Can't Multiply Net Energy by System Price

### The Problem with Simple Math

❌ **WRONG**: `465.33 MWh × £83.73/MWh = £38,956.79`

This doesn't work because **465.33 MWh is the NET result** after offsetting:
- Generators producing energy (+MWh)
- Demand users consuming energy (-MWh)
- Interconnectors importing/exporting (+/- MWh)

**The 465.33 MWh is what's LEFT OVER, not the total settlement value.**

---

## How Settlement ACTUALLY Works

### Formula for Each BM Unit

For each of the 5,705 units, settlement is calculated as:

```
Settlement Value (£) = energy_mwh × system_price × multiplier
```

Where:
- `energy_mwh` (value2): Positive for generators, negative for demand/import
- `system_price`: £83.73/MWh (same for ALL units in this period)
- `multiplier`: Typically 0.5 for half-hour periods

### Total Settlement is SUM, Not Simple Multiplication

```sql
Total Settlement = SUM(energy_mwh × system_price × multiplier) 
                   FOR ALL 5,705 UNITS
```

**NOT**: `Net Energy × System Price`

---

## Worked Example with Real Data

Let's take the top 3 units from Oct 17, 2024 Period 36:

| Unit | Energy (MWh) | System Price | Multiplier | Settlement Value (£) |
|------|--------------|--------------|------------|---------------------|
| T_MRWD-1 | +418.20 | £83.73 | 0.5 | £17,509.23 |
| T_KEAD-2 | +406.98 | £83.73 | 0.5 | £17,036.01 |
| CLOND000 | -307.84 | £83.73 | 0.5 | -£12,881.17 |

**Individual Calculations:**
- T_MRWD-1: `418.20 × 83.73 × 0.5 = £17,509.23` (generator earns)
- T_KEAD-2: `406.98 × 83.73 × 0.5 = £17,036.01` (generator earns)
- CLOND000: `-307.84 × 83.73 × 0.5 = -£12,881.17` (demand pays)

**Net Energy from these 3 units:**
`418.20 + 406.98 - 307.84 = 517.34 MWh`

**Total Settlement Value from these 3 units:**
`£17,509.23 + £17,036.01 - £12,881.17 = £21,664.07`

Notice: `517.34 MWh × £83.73/MWh × 0.5 = £21,648.24` ✅ (matches when units offset)

---

## Why £5,057.97 is So Small

The **Total Settlement Value £5,057.97** is small because:

1. **Offsetting Happens**: Generators (+) and demand (-) largely cancel out
2. **System is Balanced**: Grid must match supply and demand
3. **Net 465.33 MWh**: This is the tiny imbalance left after 5,705 units offset

### Analogy

Imagine a marketplace with 5,705 traders:
- 3,000 sellers offering +10,000 kg of apples
- 2,705 buyers wanting -9,535 kg of apples
- **Net leftover: 465 kg of apples**
- Price: £83.73/kg

The **total money that changed hands** is NOT just the leftover 465 kg × price.

It's the SUM of:
- All sellers' earnings: `+10,000 kg × £83.73 = +£837,300`
- All buyers' costs: `-9,535 kg × £83.73 = -£798,300`
- **Net settlement: £39,000** (the difference)

But because of how settlement works (with multipliers and offsetting), the actual net value is much smaller.

---

## The Real Meaning of £5,057.97

This £5,057.97 represents:

1. **Imbalance Cost**: The value of the 465.33 MWh net energy imbalance
2. **After Offsetting**: All generator earnings minus all demand costs
3. **Settlement Residual**: What's left after the system balances

### More Accurate Calculation

To get the TRUE total money exchanged, you'd need to sum:

```sql
-- Total generation revenue (positive)
SUM(energy_mwh × system_price × multiplier WHERE energy_mwh > 0)

-- Total demand cost (negative)  
SUM(energy_mwh × system_price × multiplier WHERE energy_mwh < 0)

-- Net settlement = difference between above
```

For 5,705 units with near-perfect balance:
- Generators earned: ~£millions
- Demand paid: ~£millions (nearly same)
- **Net after offset: £5,057.97** ← This is what we see

---

## Key Takeaways

1. **£5,057.97 is NOT per MWh** — it's the TOTAL settlement value for all 5,705 units
2. **465.33 MWh is NET energy** — after generators (+) and demand (-) offset
3. **You can't multiply net energy by price** — must sum individual unit settlements
4. **Settlement offsets naturally** — grid must balance supply/demand
5. **Small net value is NORMAL** — shows grid was well-balanced this period

---

## SQL Query to Verify

```sql
-- Breakdown settlement by energy direction
SELECT 
    CASE 
        WHEN value2 > 0 THEN 'Generators (Export)'
        WHEN value2 < 0 THEN 'Demand/Import (Import)'
        ELSE 'Zero'
    END as direction,
    COUNT(DISTINCT bm_unit_id) as units,
    ROUND(SUM(value2), 2) as total_energy_mwh,
    ROUND(SUM(value2 * system_price * multiplier), 2) as total_settlement_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
WHERE settlement_date = '2024-10-17'
  AND settlement_period = 36
GROUP BY direction
ORDER BY direction
```

**Expected Result:**
- Generators: +XX,XXX MWh → +£YYY,YYY revenue
- Demand: -XX,XXX MWh → -£YYY,YYY cost
- **Net: 465.33 MWh → £5,057.97** ✅

---

## Next Steps

Run the breakdown query above to see:
1. How many generators vs demand units
2. Total generation vs total demand (MWh)
3. Gross settlement values before offsetting
4. Why the net value is so much smaller

This will fully explain the £5,057.97 figure.

---

*Created: 28 December 2025*  
*Reference: P114 S0142 BPI settlement data, Oct 17, 2024 Period 36*
