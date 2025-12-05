# 🚀 DEPLOYMENT CHECKLIST - Next 4 Actions

**Date**: December 5, 2025  
**Status**: Ready to Execute  
**Priority**: High

---

## ✅ STEP 1: Update Google Sheets with Three-Tier Model

### Files Ready:
- `update_battery_revenue_model_final.py` ✅ (Already executed)
- Results: `logs/battery_revenue_final_20251205_131134.csv` ✅

### Action Required:
```bash
# Deploy enhanced BESS calculator with three-tier model
python3 bess_profit_model_enhanced.py
```

### What It Does:
- Updates BESS sheet starting at row 60
- Adds three revenue scenarios (Conservative/Base/Best)
- Includes VLP route comparison
- Preserves existing DNO/HH/BtM sections (rows 1-59)

### Expected Output:
```
✅ Section 1: DNO Lookup - Preserved
✅ Section 2: HH Profile - Preserved  
✅ Section 3: BtM PPA Analysis - Preserved
✅ Section 4: Enhanced Revenue - DEPLOYED (rows 60+)
   - Conservative: £122k/month
   - Base: £286k/month
   - Best: £337k/month
```

**STATUS**: ⏳ READY TO EXECUTE

---

## 📋 STEP 2: Review VLP Aggregator Options

### Target Aggregators:

#### 1. **Limejump** (Shell Energy subsidiary)
- **Contact**: Commercial team via [limejump.com](https://limejump.com)
- **Portfolio**: 1+ GW under management
- **Services**: BM bidding, optimization, settlement
- **Typical Fee**: 15-20% of BM revenue
- **Min Size**: 1 MW+ (25 MW ideal)
- **Reputation**: ⭐⭐⭐⭐⭐ (Market leader)

#### 2. **Flexitricity** (Centrica subsidiary)
- **Contact**: [flexitricity.com/contact](https://flexitricity.com/contact)
- **Portfolio**: 800+ MW demand response + storage
- **Services**: BM + FR + CM aggregation
- **Typical Fee**: 12-18% of BM revenue
- **Min Size**: 500 kW+
- **Reputation**: ⭐⭐⭐⭐⭐ (Strong track record)

#### 3. **Kiwi Power** (Independent)
- **Contact**: [kiwipower.com](https://kiwipower.com)
- **Portfolio**: 600+ MW flexible assets
- **Services**: Demand response + storage
- **Typical Fee**: 15-25% of BM revenue
- **Min Size**: 1 MW+
- **Reputation**: ⭐⭐⭐⭐ (Established player)

#### 4. **Habitat Energy** (AI-driven)
- **Contact**: [habitat.energy](https://habitat.energy)
- **Portfolio**: 2+ GW batteries
- **Services**: Trading + optimization platform
- **Typical Fee**: Platform subscription + % share
- **Min Size**: 1 MW+
- **Reputation**: ⭐⭐⭐⭐⭐ (Tech-forward, strong returns)

#### 5. **Enel X** (Global player)
- **Contact**: [enelx.com/uk](https://enelx.com/uk)
- **Portfolio**: 7+ GW globally
- **Services**: Full flexibility services
- **Typical Fee**: 15-20% of revenues
- **Min Size**: 500 kW+
- **Reputation**: ⭐⭐⭐⭐ (Large corporate backing)

### Action Template:

**Email Subject**: VLP Aggregation Enquiry - 50 MWh / 25 MW Battery Storage System

**Email Body**:
```
Dear [Aggregator] Commercial Team,

I am enquiring about Virtual Lead Party (VLP) aggregation services for a 
50 MWh / 25 MW battery storage system (2-hour duration, 90% efficiency).

Battery Specification:
- Capacity: 50 MWh
- Power: 25 MW
- Duration: 2 hours
- Efficiency: 90% round-trip
- Location: [TBD]
- Expected COD: [Q1 2026]

Services Required:
1. Balancing Mechanism (BM) bidding and optimization
2. BSC settlement management
3. Real-time dispatch optimization
4. Optional: Frequency Response (FR) stacking
5. Optional: Capacity Market (CM) participation support

Could you please provide:
1. Revenue share structure (% of gross BM revenue)
2. Contract terms (length, exclusivity, termination)
3. Minimum performance guarantees (if any)
4. Case studies of similar 20-30 MW batteries
5. Expected revenue (£/MWh or £/month benchmark)
6. Technical/metering requirements
7. Time to market (weeks from contract signing)

Our internal analysis suggests gross BM revenue of £113k/month for a 25 MW 
battery. We are evaluating VLP route vs. direct BSC accreditation.

Available for call to discuss further.

Best regards,
George Major
uPower Energy
george@upowerenergy.uk
```

**ACTION**: Send enquiries to all 5 aggregators (Limejump priority)

**TIMELINE**: Responses expected within 5-10 business days

**STATUS**: ⏳ READY TO SEND

---

## 🏛️ STEP 3: Submit CM Prequalification for T-4 Auction

### Background:
- **T-4 Auction**: 4 years ahead (for delivery year 2029)
- **Deadline**: Typically June-July each year
- **Next Auction**: T-4 2029 (likely June 2025) - **MISSED**
- **Alternative**: T-1 2026 (auction Dec 2025) - **UPCOMING**

### What We Need:

#### Battery Technical Data:
```yaml
Asset Type: Battery Energy Storage System (BESS)
Technology: Lithium-ion (assumed)
Capacity: 50 MWh
Power Rating: 25 MW
Duration: 2 hours
Connection: Grid-connected (DNO/TNO TBC)
Location: [TBD]
Expected COD: [Q1 2026]
De-rating Factor: 96% (for 2-4 hour battery)
De-rated Capacity: 24 MW
```

#### Prequalification Documents Required:
1. **Asset Owner Information** (company details, directors)
2. **Planning Permission** (if applicable)
3. **Grid Connection Agreement** (DNO/NESO)
4. **Metering Certificate** (P272 compliance)
5. **Technical Specification** (datasheet, performance curves)
6. **Financial Standing** (credit rating, parent company guarantee)
7. **Insurance Certificate** (liability cover)

### Action Required:

**Option 1: T-1 2026 Auction (Immediate)**
```bash
# Check if still open for prequalification
# Visit: https://www.emrdeliverybody.com/CM/Prequalification.aspx
# Deadline: Typically 6 weeks before auction (late Oct 2025 - MISSED)
```

**Option 2: T-4 2029 Auction (June 2025)**
```bash
# Prepare now for June 2025 prequalification
# Submit May-June 2025
# Result: August 2025
# Delivery: 2029
```

**Recommended Action**: 
1. Register on EMR Delivery Body portal: https://www.emrdeliverybody.com
2. Download prequalification guide
3. Prepare documentation pack now
4. Target: T-4 2029 auction (June 2025 submission)

**Contact**: EMR Delivery Body  
Email: emr@emrdeliverybody.com  
Phone: 020 7090 1000

**Expected Revenue**: £67,500/month (expected value with 45% clearing probability)

**STATUS**: ⏳ PREPARATION REQUIRED (Missed 2025 deadlines)

---

## ⚡ STEP 4: Request FR Capability Assessment from National Grid ESO

### Service Types Available:

#### Dynamic Containment (DC) - **PRIMARY TARGET**
- **Purpose**: Automatic frequency response (<1 second)
- **Revenue**: £17/MW/hour (highest value)
- **Requirements**: 
  - Response time <1 second
  - Continuous availability (4-hour blocks)
  - SOC management (maintain headroom)
- **Expected Revenue**: £51k/month (market-adjusted)

#### Dynamic Moderation (DM)
- **Purpose**: Continuous frequency regulation
- **Revenue**: £7/MW/hour
- **Requirements**: Bidirectional response, SOC management

#### Dynamic Regulation (DR)
- **Purpose**: Slower frequency response
- **Revenue**: £3/MW/hour
- **Requirements**: <10 second response

### Action Required:

**Step 1: Register as Potential Provider**

Contact: National Grid ESO Balancing Services  
Website: https://www.nationalgrideso.com/balancing-services  
Email: balancing.services@nationalgrideso.com  
Phone: 01926 653000

**Email Template**:
```
Subject: Dynamic Containment Capability Assessment - 25 MW BESS

Dear ESO Balancing Services Team,

I would like to request a capability assessment for Dynamic Containment 
(DC) and other frequency response services for a battery storage system:

Battery Specification:
- Technology: Lithium-ion battery energy storage
- Capacity: 50 MWh
- Power: 25 MW (import/export)
- Duration: 2 hours
- Efficiency: 90% round-trip
- Response time: <1 second (typical for modern inverters)
- Location: [TBD - GB DNO area]
- Expected COD: Q1 2026

Services of Interest:
1. Dynamic Containment (DC) - PRIMARY
2. Dynamic Moderation (DM) - SECONDARY
3. Dynamic Regulation (DR) - TERTIARY

Could you please provide:
1. Technical prequalification requirements
2. Capability testing procedures
3. Contract terms and procurement process
4. Expected revenue guidance (£/MW/hour benchmarks)
5. Integration with existing BM participation
6. SOC management best practices

Available for site visit / technical call.

Best regards,
George Major
uPower Energy
george@upowerenergy.uk
```

**Step 2: Technical Testing**

Once contacted, ESO will:
1. Review technical specification
2. Schedule capability test (on-site or remote)
3. Verify response time (<1s for DC)
4. Confirm telemetry/SCADA integration
5. Issue capability certificate

**Step 3: Market Participation**

- Tender submission via ESO portal
- Weekly/monthly auctions
- Dynamic pricing (£/MW/hour varies by auction)
- Can stack with BM revenue (subject to SOC management)

**TIMELINE**: 
- Initial contact: 1 week response
- Assessment: 2-4 weeks
- Testing: 1-2 days
- Certification: 2 weeks
- **Total: 6-8 weeks to market**

**STATUS**: ⏳ READY TO CONTACT

---

## 📊 Summary: Execution Order

### Week 1 (Immediate):
1. ✅ **Run BESS update script**: `python3 bess_profit_model_enhanced.py`
2. ✅ **Send VLP enquiries**: Email all 5 aggregators (use template above)

### Week 2-3:
3. ⏳ **Review VLP responses**: Compare offers, schedule calls
4. ⏳ **Contact ESO**: Submit FR capability request
5. ⏳ **Register EMR portal**: Start CM prequalification prep

### Week 4-8:
6. ⏳ **Negotiate VLP contract**: Target signing by end of month
7. ⏳ **ESO capability test**: Schedule and complete
8. ⏳ **CM documentation**: Prepare for June 2025 T-4 auction

### Expected Outcomes:
- **VLP contract signed**: +£96k/month BM revenue (15% fee)
- **FR approved**: +£51k/month DC revenue potential
- **CM prequalified**: +£68k/month (if 2029 auction clears)

---

## 🎯 Quick Start Command

```bash
# Update Google Sheets with three-tier model NOW
python3 /home/george/GB-Power-Market-JJ/bess_profit_model_enhanced.py

# Check output
cat /home/george/GB-Power-Market-JJ/logs/bess_integration_*.log | tail -50
```

---

**STATUS SUMMARY**:
- ✅ Step 1 (Sheets): Ready to execute (1 command)
- ⏳ Step 2 (VLP): Ready to send emails (templates provided)
- ⏳ Step 3 (CM): Registration needed (deadlines missed for 2025)
- ⏳ Step 4 (FR): Ready to contact ESO (email template provided)

**NEXT IMMEDIATE ACTION**: Run the sheets update script!
