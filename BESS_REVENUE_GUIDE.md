# BESS Revenue & Profit Calculator Guide

## 📊 Revenue Streams Summary

Your battery generates revenue from **5 sources**:

### 1. System Operator (SO) Payments - £72,450 (34%)
**These are the BID/BOD/FFR/DCR services you asked about!**

#### FFR (Firm Frequency Response) - £10,800
- **What**: Availability payment to respond to frequency drops
- **Speed**: Must respond within 1 second
- **Rate**: £12/MW/hour for primary response
- **Typical**: 4 hours/day availability
- **Example**: 2.5 MW × 4 hrs × £12 = £120/day

#### DCR (Dynamic Containment) - £22,950 ⭐ HIGHEST
- **What**: Fast frequency response (up/down)
- **Speed**: Sub-1 second response required
- **Rate**: £17/MW/hour (high frequency)
- **Typical**: 6 hours/day availability
- **Example**: 2.5 MW × 6 hrs × £17 = £255/day

#### DM (Dynamic Moderation) - £6,075
- **What**: Medium-speed frequency control
- **Rate**: £9/MW/hour
- **Typical**: 3 hours/day
- **Example**: 2.5 MW × 3 hrs × £9 = £67.50/day

#### DR (Dynamic Regulation) - £6,750
- **What**: Continuous frequency regulation
- **Rate**: £10/MW/hour
- **Typical**: 3 hours/day
- **Example**: 2.5 MW × 3 hrs × £10 = £75/day

#### BID (Balancing Bids) - £19,125 ⭐ HIGH VALUE
- **What**: Paid to reduce demand or increase supply when grid is tight
- **When**: High demand periods (typically peak times)
- **Payment**: Market price + premium (~£50/MWh extra)
- **Acceptance**: ~85% of bids accepted
- **Typical**: 2 events/day × 1 hour each
- **Example**: 2.5 MW × 1 hr × £50 premium = £125/event
- **Revenue**: ~£212/day (2 events)

#### BOD (Balancing Offers) - £6,750
- **What**: Paid to increase generation/discharge when grid needs supply
- **When**: System shortfalls, unexpected demand
- **Payment**: Market price + premium (~£40/MWh extra)
- **Acceptance**: ~75% of offers accepted
- **Typical**: 1 event/day × 1 hour
- **Example**: 2.5 MW × 1 hr × £40 premium = £100/event
- **Revenue**: ~£75/day (1 event)

---

### 2. PPA Contract Revenue - £75,938 (36%)
- **What**: Fixed price for energy sold
- **Your Price**: £150/MWh (from B21)
- **Volume**: 506 MWh over 90 days
- **When**: Peak discharge periods (RED time band)
- **Daily**: ~£844/day

### 3. Energy Arbitrage - £58,999 (28%)
- **What**: Buy low (GREEN), sell high (RED)
- **Strategy**: Charge off-peak, discharge peak
- **Daily**: ~£656/day

### 4. Capacity Market - £3,699 (2%)
- **What**: Payment for being available
- **Rate**: £6/kW/year
- **Daily**: ~£41/day

---

## 🎯 How Min/Avg/Max kW Parameters Work

Your three power levels map to different operating modes:

### MIN kW (500 kW) - GREEN Time Band
**When**: 00:00-08:00, 22:00-24:00 (off-peak)
- **Mode**: Light charging
- **DUoS**: Lowest (£0.11/MWh)
- **Energy**: 250 kWh per 30-min period
- **Use**: Trickle charge, base load
- **Cost**: Minimal (best time to charge)

### AVG kW (1,500 kW) - AMBER Time Band
**When**: 08:00-16:00, 19:30-22:00 (mid-peak)
- **Mode**: SO services (FFR/DCR/DM/DR)
- **DUoS**: Medium (£2.05/MWh)
- **Energy**: 750 kWh per 30-min period
- **Use**: Frequency response, selective arbitrage
- **Focus**: Maximize availability payments

### MAX kW (2,500 kW) - RED Time Band
**When**: 16:00-19:30 (peak)
- **Mode**: Full discharge
- **DUoS**: Highest (£17.64/MWh) - but you're SELLING!
- **Energy**: 1,125 kWh per 30-min (with 90% efficiency)
- **Use**: PPA delivery, peak arbitrage, BID/BOD response
- **Revenue**: Maximum (best time to discharge)

---

## 💰 Complete Profit Calculation

```
TOTAL REVENUE (90 days):        £211,086
├─ PPA Revenue:                 £75,938   (36%)
├─ SO Payments:                 £72,450   (34%)
│  ├─ DCR:                      £22,950
│  ├─ BID:                      £19,125
│  ├─ FFR:                      £10,800
│  ├─ DR:                       £6,750
│  ├─ BOD:                      £6,750
│  └─ DM:                       £6,075
├─ Energy Arbitrage:            £58,999   (28%)
└─ Capacity Market:             £3,699    (2%)

TOTAL COSTS:                    £126,306
├─ Energy purchases (SBP):      ~£90,000
└─ All levies (DUoS+CCL+RO+etc):~£36,306

NET PROFIT:                     £84,779   (40% margin)
├─ Daily:                       £942/day
├─ Monthly:                     £28,260
└─ Annual:                      £343,828/year
```

---

## 📋 Usage Instructions

### Setup
1. Enter battery specs in B17:B19:
   - B17: Min kW (off-peak charging)
   - B18: Avg kW (normal operations)
   - B19: Max kW (peak discharge)

2. Enter PPA price in B21:
   - Format: Just the number (e.g., 150 for £150/MWh)

3. Ensure DUoS rates in B10:D10 are populated

### Run Analysis
```bash
python3 calculate_bess_revenue.py
```

### View Results
- **Rows 170-205**: Complete revenue breakdown
- **Summary in A20**: Quick daily/annual figures

---

## 🎯 Optimization Tips

### 1. Maximize DCR Revenue (£255/day)
- **Best opportunity**: Highest £/MW/hour rate
- **Strategy**: Maintain 50% SOC for bidirectional response
- **Requirement**: <1 second response time
- **Benefit**: Passive income while available

### 2. Capture BID Premiums (£212/day)
- **Timing**: Peak demand periods (RED time band)
- **Strategy**: Be charged and ready at 16:00-19:30
- **Stacking**: Combine with PPA discharge
- **Premium**: ~£50/MWh on top of market price

### 3. Optimize Charge Timing
- **GREEN periods**: Charge at MIN kW (lowest costs)
- **Avoid RED**: Never charge during peak (high DUoS)
- **AMBER**: Selective - only if spread >20%

### 4. Balance Cycle Life
- **Current**: ~1.5 cycles/day = 550/year
- **Warranty**: 4,000-6,000 cycles typical
- **Lifespan**: 7-10 years at this rate
- **Sustainable**: Yes, revenue covers degradation

---

## �� Key Performance Indicators

| Metric | Value | Target |
|--------|-------|--------|
| Daily Profit | £942 | >£500 |
| Annual Profit | £344k | >£200k |
| Gross Margin | 40.2% | >35% |
| Revenue/kW/year | £137 | >£100 |
| SO Revenue % | 34% | >30% |
| Cycles/Day | 1.5 | <2.0 |

---

## 🔄 Revenue Stack Example (Typical Day)

**06:00** - GREEN period
- Charging at MIN (500 kW)
- DUoS: £0.11/MWh
- Cost: ~£25/hour
- Mode: Trickle charge

**10:00** - AMBER period  
- Available for DCR
- Payment: £17/MW/hour × 2.5 MW = £42.50/hour
- Mode: Frequency response

**17:00** - RED period (PEAK)
- Discharge at MAX (2,500 kW)
- PPA Revenue: £150/MWh × 2.5 MWh = £375/hour
- BID event: +£50/MWh × 2.5 MW = +£125
- Total: £500/hour
- Mode: Maximum discharge

**Daily Total**: ~£942 net profit

---

## 🚀 Quick Wins

1. **Join DCR auctions** - £22,950/quarter passive income
2. **Submit BID offers** - £19,125/quarter for 2 events/day
3. **Charge GREEN only** - Save £17.53/MWh on DUoS
4. **Discharge RED + BID** - Stack revenues (£150+£50/MWh)
5. **Track 50% SOC** - Maximize FFR/DCR availability

---

## �� Need Help?

Run the calculator: `python3 calculate_bess_revenue.py`
View results: Rows 170-205 in BESS sheet
Update parameters: B17:B19 (power), B21 (PPA price)

