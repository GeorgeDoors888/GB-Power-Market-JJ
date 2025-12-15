# How BOA Energy Payments Are Accessed (GB)

**Date**: December 15, 2025  
**Context**: Balancing Mechanism revenue analysis for GB Power Market JJ project  
**Critical Issue**: EBOCF/BOALF data from BMRS ≠ actual settlement payments

---

## 1. What "BOA Energy Payments" Actually Are

**BOA energy payments** are the cashflows associated with accepted Balancing Mechanism (BM) Bids and Offers:

- **NESO accepts** a Bid or Offer against a BM Unit (BMU)
- **Acceptance creates** an energy delivery obligation
- **Delivered energy** is paid (or charged) at the accepted price
- **Payment settled** through BSC settlement

### What BOA Payments Are NOT

❌ Wholesale trades  
❌ VTP deviation settlement  
❌ Ancillary service availability fees (FFR, DR, etc.)  
❌ Capacity Market payments  
❌ Transparency data (BMRS)

**BOA = Balancing Mechanism energy delivery payments only**

---

## 2. Who Does What (Critical Separation)

### NESO (formerly NGESO)

**Role**: System operation & dispatch

- ✅ Accepts Bids and Offers in real time
- ✅ Determines what is accepted and when
- ❌ Does NOT settle payments
- ❌ Does NOT publish settlement cashflows

**NESO outputs are operational instructions, not financial truth.**

---

### Elexon (BSC Administrator)

**Role**: Settlement & financial reconciliation

- ✅ Calculates delivered volumes
- ✅ Applies accepted prices
- ✅ Determines who pays whom and how much
- ✅ Publishes transparency datasets (BMRS)
- ✅ Runs settlement via BSC agents (SAA, SVAA)

**All BOA energy payments are determined under the BSC, not by NESO.**

---

## 3. The Governing Frameworks (Why This Matters)

### A) Balancing and Settlement Code (BSC)

This is the **legal framework** that:
- Defines BM energy settlement
- Defines how accepted volumes become cashflows
- Defines payment timing, disputes, and reconciliation

**BOA energy payments are a BSC construct.**

---

### B) Grid Code

The Grid Code:
- Defines technical and operational obligations
- Defines who must comply with dispatch instructions
- **Does NOT define payments**

**The Grid Code enables dispatch; the BSC monetises it.**

---

## 4. Where BOA Energy Payment Data Is Accessed

### Critical Distinction

**There are three layers of access, and only one is settlement-grade.**

---

### 4.1 BMRS (Elexon Transparency) — NOT Settlement-Grade

**Accessible via**: https://data.elexon.co.uk/bmrs/api/v1

**Relevant datasets**:
- `BOAL` / `BOALF` → Accepted MW profiles (volumes)
- `BOD` → Submitted prices (intent only)
- `DISBSAD` → Certain system action costs/volumes
- `EBOCF` → **Indicative** cashflows (our project uses this)

**What you CAN do with BMRS**:
- ✅ Estimate energy volumes
- ✅ Estimate revenue
- ✅ Analyse competitiveness
- ✅ Build commercial analysis tools

**What you CANNOT do with BMRS**:
- ❌ Obtain legally binding cashflows
- ❌ Reproduce final settlement statements
- ❌ Use for accounting/audit purposes

**BMRS ≠ payment system**

---

### 4.2 Settlement Reports (BSC Parties Only) — Authoritative

If you are a **BSC Party**, you access BOA energy payments via:
- SAA settlement reports
- Credit & cashflow reports
- Energy imbalance and BM payment statements

**Accessed through**:
- Elexon portals
- Secure participant systems
- Bilateral settlement interfaces

**This is the only source of "truth" for BOA payments.**

---

### 4.3 Internal Participant Systems

Most BM participants:
- Ingest BMRS data for forecasting
- Ingest settlement reports for accounting
- Reconcile the two internally

**This is normal and expected.**

---

## 5. Why You Never See "BOA Payments" Directly in an API

**This is by design.**

### Reasons

1. **Settlement includes**:
   - Reconciliation
   - Corrections
   - Dispute windows

2. **Payments are**:
   - Party-confidential
   - Legally binding

3. **Publishing them live would**:
   - Expose commercial positions
   - Undermine settlement finality

### Therefore

**There is no public API that says "BMU X was paid £Y today".**

That information exists only inside BSC settlement outputs.

---

## 6. How Analysts Correctly Reconstruct BOA Energy Payments

**This is what our project does.**

### Step 1 — Volumes

From `BOAL` / `BOALF`:
- Integrate MW over time → MWh delivered
- Our table: `bmrs_boalf` + `bmrs_boalf_iris`

### Step 2 — Prices

From either:
- Accepted price fields (if available), or
- Reconstructed mapping to `BOD` (approximate)
- Our table: `bmrs_boav` (volume-weighted accepted prices)

### Step 3 — Direction
- **Offers** → revenue (BMU increases output)
- **Bids** → cost or negative revenue (BMU decreases output)

### Step 4 — Adjustments

Optionally include:
- `DISBSAD` costs
- Flags (constraint, SO actions)
- Exclusions (e.g., tendered services)

### Result

**This produces an ESTIMATED BM revenue, not settlement truth.**

---

## 7. GB Power Market JJ Project: What We Actually Have

### Our Data Sources (All BMRS Transparency Data)

| Table | Description | Grade | Purpose |
|-------|-------------|-------|---------|
| `bmrs_boalf` | Accepted offers/bids (historical) | Indicative | Volume estimates |
| `bmrs_boalf_iris` | Accepted offers/bids (real-time) | Indicative | Recent volumes |
| `bmrs_boav` | Acceptance volumes by BMU | Indicative | Revenue estimates |
| `bmrs_ebocf` | **Indicative cashflows** | **Indicative** | Revenue proxy |
| `bmrs_bod` | Bid-offer data (submitted prices) | Indicative | Price analysis |

### What Our Analysis Shows

**Skelmersdale Tesla (E_SKELB-1)**:
- **Source**: `bmrs_ebocf` (indicative cashflows)
- **Revenue**: £1,083,670/year
- **Grade**: **ESTIMATED** (not settlement-grade)
- **Use case**: Commercial analysis, NOT accounting

**System-wide BM Revenue**:
- **Source**: `analyze_accepted_revenue_so_flags_v2.py`
- **Method**: BOALF volumes × BOAV prices
- **Result**: £169M (90 days), £25.06/MWh VWAP
- **Grade**: **ESTIMATED**

### Critical Disclaimer for Our Project

```
All BM revenue figures in this analysis are ESTIMATES derived from 
Elexon BMRS transparency data (BOALF, BOAV, EBOCF). These are NOT 
settlement-grade cashflows and should not be used for:
  - Financial accounting
  - Regulatory reporting
  - Contractual settlement
  - Audit purposes

BMRS data is suitable for:
  - Commercial analysis
  - Market research
  - Strategy development
  - Investment evaluation
```

---

## 8. Regulator-Safe Wording

### For Documentation/Reports

> Balancing Mechanism energy payments arise from accepted Bids and Offers 
> instructed by NESO and are settled under the Balancing and Settlement Code. 
> While Elexon publishes transparency data on accepted actions and system 
> balancing costs via BMRS, definitive BOA energy payments are determined 
> through BSC settlement processes and are not available via public APIs.

### For Our Analysis Outputs

> This analysis uses BMRS transparency data (BOALF, BOAV, EBOCF) to estimate 
> Balancing Mechanism revenue. These are indicative estimates only and do not 
> represent actual settlement cashflows. For settlement-grade BOA energy 
> payments, BSC Parties must refer to SAA settlement reports.

---

## 9. One-Page Summary

| Question | Answer |
|----------|--------|
| **What are BOA payments?** | Cashflows from accepted BM Bids/Offers, settled via BSC |
| **Who settles them?** | Elexon (BSC Administrator), NOT NESO |
| **Where is settlement data?** | BSC Party settlement reports (confidential) |
| **What is BMRS data?** | Transparency data for market analysis (NOT settlement) |
| **Can I get actual payments?** | NO - only if you're a BSC Party with settlement access |
| **What does EBOCF show?** | **Indicative** cashflows (estimated, not authoritative) |
| **Is our analysis valid?** | YES - for commercial/research purposes, NO for accounting |
| **Legal framework?** | BSC (settlement) + Grid Code (dispatch) |
| **Why the separation?** | Settlement needs reconciliation, disputes, finality |
| **Safe wording?** | "Estimated BM revenue from BMRS transparency data" |

---

## 10. Implications for Our Project

### What We Should Say

✅ **CORRECT**:
- "Estimated BM revenue based on BMRS data"
- "Indicative cashflows from EBOCF"
- "Analysis of accepted BM actions"
- "BMRS transparency data shows..."

❌ **AVOID**:
- "Actual BM payments"
- "Settlement cashflows"
- "Definitive revenue"
- "Audited financials"

### Updates Needed to Existing Analysis

1. **CAPACITY_MARKET_SO_FLAG_ANALYSIS.md**:
   - Update: "Proven BM Revenue" → "**Estimated** BM Revenue (BMRS)"
   - Add: Disclaimer about EBOCF being indicative

2. **analyze_accepted_revenue_so_flags_v2.py**:
   - Add comment: `# Note: BOALF/BOAV data = indicative, not settlement-grade`
   - Update output: "Estimated Revenue" instead of "Revenue"

3. **Google Sheets Dashboard**:
   - Add disclaimer cell: "BM revenue figures are estimates from BMRS transparency data"

4. **All Documentation**:
   - Search/replace: "BM revenue" → "Estimated BM revenue (BMRS)"
   - Add: Standard disclaimer about data sources

### Why This Matters

**Regulatory Risk**:
- Claiming BMRS data = actual payments → misleading
- Using for accounting → audit failure
- Claiming settlement-grade → potential BSC breach

**Commercial Risk**:
- Investors expect ±10-20% variance from BMRS estimates
- Actual settlement may differ due to:
  - Metering corrections
  - Reconciliation runs (RF, SF, R1, R2, R3)
  - Dispute resolutions

**Correct Positioning**:
- Our tool = market analysis & strategy
- Data grade = transparency/indicative
- Use case = commercial research, NOT settlement

---

## 11. Data Quality: BMRS vs Settlement

### Known Variances Between BMRS and Settlement

| Factor | BMRS Data | Settlement Data |
|--------|-----------|-----------------|
| **Volumes** | Accepted MW profiles | Metered delivery |
| **Prices** | Accepted prices | Final settled prices |
| **Timing** | Near real-time | RF, SF, R1, R2, R3 (up to 14 months) |
| **Corrections** | None | Disputes, reconciliations |
| **Accuracy** | ±5-15% typical | 100% (by definition) |

### Reconciliation Runs

- **RF (Day 1)**: Initial settlement
- **SF (Day 4)**: Second settlement
- **R1 (Month 1)**: First reconciliation
- **R2 (Month 4)**: Second reconciliation
- **R3 (Month 14)**: Final reconciliation

**BMRS data doesn't include any of these corrections.**

---

## 12. Action Items for Project

### Immediate (Dec 15, 2025)

- [ ] Add disclaimer to all BM revenue outputs
- [ ] Update terminology: "revenue" → "estimated revenue (BMRS)"
- [ ] Document data sources clearly in each script
- [ ] Add "Data Quality" section to README

### Short-term (This Week)

- [ ] Review all .md files for misleading wording
- [ ] Update Google Sheets dashboard with disclaimer
- [ ] Add data grade labels to all charts/tables
- [ ] Create standard boilerplate text for reports

### Long-term (2025)

- [ ] Consider building settlement reconciliation estimates
- [ ] Track variance between EBOCF and actual (if BSC access obtained)
- [ ] Document typical variance ranges by technology
- [ ] Build confidence intervals around estimates

---

**Document Status**: Complete explanation of BOA payments vs BMRS data  
**Critical Takeaway**: Our analysis is VALID but must be labeled as ESTIMATED, not actual settlement  
**Next Steps**: Update all existing documentation with correct disclaimers

**Contact**: george@upowerenergy.uk
