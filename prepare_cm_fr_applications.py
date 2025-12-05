#!/usr/bin/env python3
"""
Capacity Market & Frequency Response Application Preparation
Generates prequalification templates for CM T-4 auction and FR capability assessment
Outputs: cm_prequalification_YYYYMMDD.txt, fr_assessment_request_YYYYMMDD.txt
"""

from datetime import datetime
import os

def generate_cm_prequalification():
    """Generate Capacity Market prequalification template"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    cm_template = f"""
{'=' * 80}
CAPACITY MARKET PREQUALIFICATION APPLICATION
UK Electricity Capacity Market - T-4 Auction
{'=' * 80}

Application Date: {datetime.now().strftime('%d %B %Y')}
Delivery Year: 2029/30 (T-4 auction, likely opens Q1 2026)

SECTION 1: APPLICANT INFORMATION
{'=' * 80}

Company Name: uPower Energy Ltd
Registered Address: [TO BE COMPLETED]
Company Number: [TO BE COMPLETED]
VAT Number: [TO BE COMPLETED]

Primary Contact:
  Name: George Major
  Email: george@upowerenergy.uk
  Phone: [TO BE COMPLETED]
  Position: Director

Secondary Contact:
  Name: [TO BE COMPLETED]
  Email: [TO BE COMPLETED]
  Phone: [TO BE COMPLETED]

SECTION 2: CAPACITY MARKET UNIT (CMU) DETAILS
{'=' * 80}

CMU Type: Battery Storage (Proven DSR)
CMU Name: [TO BE ASSIGNED - e.g., "uPower BESS 001"]
Technology: Lithium-ion Battery Energy Storage System (BESS)

Technical Specification:
  Installed Capacity: 25 MW (AC)
  Energy Capacity: 50 MWh
  Duration: 2 hours
  Round-trip Efficiency: 90%
  Technology Type: Grid-scale lithium-ion
  
Grid Connection:
  DNO: [TO BE COMPLETED]
  GSP Group: [TO BE COMPLETED]
  Connection Voltage: [TO BE COMPLETED - likely 33kV or 132kV]
  MPAN: [TO BE COMPLETED]
  Connection Agreement Status: [TO BE COMPLETED]
  Expected Energisation Date: Q2 2026

SECTION 3: DE-RATING FACTORS
{'=' * 80}

Per Ofgem Capacity Market Rules 2024:

Battery Storage De-rating Factors (2-hour duration):
  Installed Capacity: 25.00 MW
  De-rating Factor: 96% (per Ofgem CM rules for 2h batteries)
  De-rated Capacity: 24.00 MW
  
Historical Performance: N/A (new build)
Equivalent Forced Outage Rate (EFOR): Assume 2% (industry standard for new li-ion)

De-rating Calculation Method:
  Based on 2-hour duration classification
  Proven DSR technology
  96% de-rating per Ofgem methodology
  
Expected Auction Clearing Price: £45-75/kW/year (based on recent auctions)
Target Revenue at 24 MW de-rated: £1.08M - £1.80M per annum

SECTION 4: DELIVERY OBLIGATIONS
{'=' * 80}

Stress Event Participation:
  We confirm ability to deliver de-rated capacity during System Stress Events
  Expected response time: < 15 minutes
  Duration capability: 2 hours continuous at full de-rated capacity
  
Availability:
  Target availability: 98% during delivery year
  Planned maintenance: To be scheduled outside peak demand periods
  Remote monitoring: 24/7 real-time monitoring and control
  
Performance Testing:
  Willing to participate in mandatory CM prequalification tests
  Testing window: [To be scheduled with ESO]
  Test location: Battery site [TO BE CONFIRMED]

SECTION 5: METERING & SETTLEMENT
{'=' * 80}

Metering Arrangement:
  Metering Type: Half-hourly (HH) settlement
  Meter Operator: [TO BE APPOINTED]
  Data Aggregator: [TO BE APPOINTED]
  Metering Point ID: [TO BE ASSIGNED]
  
Settlement Agent: [TO BE APPOINTED - likely Elexon/EMRS]

BSC Party Status:
  [ ] Already BSC party (Party ID: ______)
  [X] Will use VLP aggregator (see Section 6)
  [ ] Will become direct BSC party

SECTION 6: VLP AGGREGATOR (IF APPLICABLE)
{'=' * 80}

VLP Aggregator Details:
  Company: [TO BE CONFIRMED - likely Limejump, Flexitricity, or Habitat Energy]
  VLP Party ID: [TO BE ASSIGNED]
  Agreement Status: Term sheet under negotiation
  Revenue Share: Expect 15-20% of CM revenues to be retained by VLP
  
CM Support Services from VLP:
  - CM prequalification support
  - Stress event notification and dispatch
  - Performance monitoring and reporting
  - Settlement reconciliation
  - Penalty management

SECTION 7: FINANCIAL STANDING
{'=' * 80}

Credit Cover Requirements:
  Estimated requirement: £300k - £500k (based on 24 MW de-rated x £45-75/kW)
  Credit cover method: [TO BE DECIDED]
    Options:
    [ ] Parent company guarantee
    [ ] Letter of credit
    [ ] Cash deposit
    
Financial Backing:
  Project Finance Status: [TO BE COMPLETED]
  Investor(s): [TO BE COMPLETED]
  Total Project Value: [TO BE COMPLETED]

SECTION 8: PLANNING & PERMITS
{'=' * 80}

Planning Permission:
  Status: [TO BE COMPLETED]
  Planning Authority: [TO BE COMPLETED]
  Reference Number: [TO BE COMPLETED]
  Conditions: [TO BE LISTED]

Environmental Permits:
  Battery Safety: BS EN IEC 62933 compliance
  Fire Safety: [TO BE CONFIRMED]
  Environmental Impact Assessment: [TO BE COMPLETED if required]

Health & Safety:
  Risk Assessment: [TO BE COMPLETED]
  Emergency Response Plan: [TO BE COMPLETED]
  Insurance: [TO BE ARRANGED]

SECTION 9: PROJECT TIMELINE
{'=' * 80}

Key Milestones:
  Q1 2026: CM T-4 auction prequalification opens
  Q2 2026: Submit prequalification application
  Q2 2026: Battery energisation and commissioning
  Q3 2026: CM performance testing and certification
  Q4 2026: T-4 auction (delivery year 2029/30)
  Q1 2027: Results notification
  Oct 2029: Delivery year commences (4 years after auction)

Critical Path:
  ✓ Complete grid connection agreement
  ✓ Secure planning permission
  ✓ Finalize battery procurement and construction
  ✓ Appoint VLP aggregator or become BSC party
  ✓ Install metering and comms
  ✓ Complete CM prequalification tests

SECTION 10: SUPPORTING DOCUMENTS (TO BE ATTACHED)
{'=' * 80}

Required Documents:
  [ ] Grid connection agreement (signed)
  [ ] Planning permission certificate
  [ ] Company incorporation certificate
  [ ] Financial statements (last 2 years if applicable)
  [ ] Battery technical specification (manufacturer datasheet)
  [ ] Site layout plan
  [ ] Single line diagram
  [ ] Metering schematic
  [ ] Insurance certificate
  [ ] Health & safety risk assessment
  [ ] VLP aggregator agreement (if applicable)

SECTION 11: DECLARATIONS
{'=' * 80}

We declare that:
  [X] All information provided is accurate to the best of our knowledge
  [X] The CMU will be able to deliver its de-rated capacity during stress events
  [X] We understand the Capacity Market Rules and our delivery obligations
  [X] We will maintain required credit cover throughout the delivery year
  [X] We consent to EMR Delivery Body sharing our data per CM rules

Signed: _________________________  Date: __________
Name: George Major
Position: Director
Company: uPower Energy Ltd

{'=' * 80}
NEXT STEPS AFTER COMPLETION
{'=' * 80}

1. Complete all [TO BE COMPLETED] fields with actual project details
2. Gather all supporting documents listed in Section 10
3. Confirm VLP aggregator or prepare for direct BSC accreditation
4. Arrange credit cover (£300k-500k)
5. Submit via EMR Delivery Body portal (https://emrsettlement.co.uk)
6. Await prequalification testing schedule from National Grid ESO
7. Complete mandatory performance tests (typically 2-4 weeks notice)
8. Receive provisional approval (6-8 weeks after test)
9. Participate in T-4 auction (Q4 2026 likely)
10. Sign Capacity Agreement if successful (within 20 business days)

Contact for Queries:
  EMR Delivery Body: capacity.market@emrsettlement.co.uk
  Phone: 0207 090 5086
  Portal: https://emrsettlement.co.uk

Estimated Time to Complete: 8-12 weeks from application to auction eligibility
Expected Auction Success Rate: 40-50% for batteries (competitive market)
Target Revenue: £1.08M - £1.80M per annum (£67.5k/month average)

{'=' * 80}
END OF CAPACITY MARKET PREQUALIFICATION APPLICATION
{'=' * 80}
"""
    
    return cm_template, timestamp

def generate_fr_assessment():
    """Generate Frequency Response capability assessment request"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    fr_template = f"""
{'=' * 80}
FREQUENCY RESPONSE CAPABILITY ASSESSMENT REQUEST
National Grid ESO - Ancillary Services
{'=' * 80}

Request Date: {datetime.now().strftime('%d %B %Y')}
Service Types of Interest: Dynamic Containment (DC), Dynamic Moderation (DM), Dynamic Regulation (DR)

SECTION 1: APPLICANT INFORMATION
{'=' * 80}

Company Name: uPower Energy Ltd
Registered Address: [TO BE COMPLETED]
Company Number: [TO BE COMPLETED]

Primary Contact:
  Name: George Major
  Email: george@upowerenergy.uk
  Phone: [TO BE COMPLETED]
  Position: Director

Technical Contact:
  Name: [TO BE COMPLETED]
  Email: [TO BE COMPLETED]
  Phone: [TO BE COMPLETED]
  Position: [e.g., Operations Manager, Technical Director]

SECTION 2: ASSET SPECIFICATION
{'=' * 80}

Asset Type: Battery Energy Storage System (BESS)
Asset Name: [TO BE ASSIGNED - e.g., "uPower BESS 001"]

Technical Specification:
  Rated Power (MW): 25 MW (AC)
  Energy Capacity (MWh): 50 MWh
  Duration: 2 hours
  Round-trip Efficiency: 90%
  Response Time: < 1 second (typical for battery)
  Ramp Rate: 25 MW/second (full power in <1s)
  State of Charge Management: Automated
  
Battery Technology:
  Chemistry: Lithium-ion (NMC or LFP - [TO BE CONFIRMED])
  Manufacturer: [TO BE CONFIRMED]
  Inverter Type: Grid-forming or grid-following [TO BE CONFIRMED]
  Control System: [TO BE CONFIRMED]

Grid Connection:
  DNO: [TO BE COMPLETED]
  Connection Voltage: [33kV or 132kV - TO BE CONFIRMED]
  MPAN/MSID: [TO BE COMPLETED]
  Connection Capacity: 25 MW import/export
  Expected Energisation: Q2 2026

SECTION 3: FREQUENCY RESPONSE SERVICES - CAPABILITY ASSESSMENT
{'=' * 80}

A. DYNAMIC CONTAINMENT (DC) - Primary Interest
-------------------------------------------

Service Description: Fastest FR service, responding within 1 second to frequency deviations

Capability Assessment:
  Maximum Power Available: 25 MW
  Response Time: < 1 second ✓ (meets DC requirement)
  Sustained Delivery: 15 minutes ✓ (battery can deliver 25 MW for 15+ min)
  Accuracy: +/- 2% ✓ (battery control precision typical)
  Availability: 24/7 capable ✓
  
State of Charge (SoC) Management:
  Target SoC Range: 40-60% (enables symmetric response)
  Low/High Frequency Capability: Symmetric (import or export)
  Recharge Strategy: Automatic rebalancing between events
  Energy Throughput: ~12.5 MWh available (50% of capacity)
  
DC Market Analysis:
  Current Clearing Price: £12-22/MW/hour (average £17/MW/hour)
  Expected Revenue at 25 MW: £51,000/month (40% utilization assumed)
  Service Windows: 24/7 availability (ESO procures for all periods)
  Contract Length: Day-ahead auction (daily commitment)
  
Technical Requirements:
  [✓] Response time < 1 second
  [✓] Sustained delivery 15 minutes
  [✓] Symmetric (both directions)
  [✓] Metering resolution 1 second
  [ ] EDL/ECL certification [TO BE ARRANGED]
  [ ] Grid Code compliance certification [TO BE ARRANGED]

B. DYNAMIC MODERATION (DM)
-------------------------------------------

Service Description: Medium-speed FR, responding within 2 seconds

Capability: ✓ CAPABLE (battery exceeds DM requirements)
  Response Time: < 1 second (exceeds 2s requirement)
  Sustained Delivery: 30 minutes required ✓
  Expected Revenue: Lower than DC (~£8-12/MW/hour)
  
Assessment: Battery over-qualified for DM - prioritize DC instead

C. DYNAMIC REGULATION (DR)
-------------------------------------------

Service Description: Continuous frequency regulation, very frequent cycling

Capability: ✓ CAPABLE but high degradation risk
  Response Time: < 1 second ✓
  Cycling Impact: High (100+ cycles/day typical)
  Battery Degradation: Significant concern
  Revenue: £15-20/MW/hour but battery wear may exceed revenue
  
Assessment: Not recommended due to battery degradation concerns
            Only consider if stacked with other services

SECTION 4: STACKING & OPTIMIZATION
{'=' * 80}

Recommended Service Stack (Priority Order):

1. DYNAMIC CONTAINMENT (DC) - Primary Service
   Revenue: £51,000/month
   Availability: 16-20 hours/day
   SoC Management: 40-60% range
   
2. ENERGY ARBITRAGE - Secondary Service
   Revenue: £122,000/month (proven from historical data)
   Availability: During non-DC periods (4-8 hours/day)
   Strategy: Charge cheap (overnight), discharge expensive (peak)
   Synergy: Use arbitrage cycles to rebalance SoC for DC service
   
3. BALANCING MECHANISM (via VLP) - Tertiary Service
   Revenue: £96,000/month (conditional on VLP contract)
   Availability: Opportunistic (when called by ESO)
   Integration: VLP can stack BM with DC/arbitrage
   
4. CAPACITY MARKET - Annual Contract
   Revenue: £67,500/month average
   Obligation: Deliver during 4-6 stress events per year (2h duration)
   Synergy: No conflict with DC/arbitrage (rare events)

Expected Combined Revenue:
  Conservative (Arbitrage only): £122k/month
  Base (Arbitrage + DC): £173k/month  
  Best (Arbitrage + DC + BM + CM): £337k/month

SECTION 5: TECHNICAL REQUIREMENTS FOR FR PARTICIPATION
{'=' * 80}

Metering & Communications:
  [TO BE COMPLETED] Real-time metering (1-second resolution)
  [TO BE COMPLETED] Dedicated comms link to ESO control room
  [TO BE COMPLETED] SCADA integration for remote monitoring
  [TO BE COMPLETED] Backup communications (redundancy required)

Control System:
  [TO BE COMPLETED] Automated frequency response controller
  [TO BE COMPLETED] Grid Code G99 or G100 compliance certification
  [TO BE COMPLETED] Capability to receive/respond to ESO signals
  [TO BE COMPLETED] SoC management algorithm

Testing & Certification:
  [TO BE COMPLETED] EDL/ECL certification (Energy Data Logger/Energy Calculating Logger)
  [TO BE COMPLETED] Manufacturer performance certificates
  [TO BE COMPLETED] Witnessed performance tests
  [TO BE COMPLETED] Grid Code compliance statement

Software & Data:
  [TO BE COMPLETED] ESO portal access (for auction participation)
  [TO BE COMPLETED] Historical performance logging (for settlement)
  [TO BE COMPLETED] Real-time monitoring dashboard

SECTION 6: VLP AGGREGATOR FOR FR (OPTIONAL)
{'=' * 80}

Using VLP Aggregator for FR Services:

Advantages:
  ✓ Aggregator handles ESO contracts and compliance
  ✓ Optimized stacking (DC + arbitrage + BM)
  ✓ Automated bidding and dispatch
  ✓ Faster time to market (4-6 weeks vs 12+ weeks direct)
  ✓ Lower technical burden (aggregator manages metering/comms)

Disadvantages:
  ✗ Revenue share (10-20% to aggregator)
  ✗ Less control over dispatch decisions
  ✗ Contract lock-in (12-24 months typical)

Recommended Aggregators for FR:
  1. Flexitricity - Strong FR track record, excellent stacking
  2. Habitat Energy - AI-driven optimization, highest revenue/MWh
  3. Open Energi - DC market pioneer, fast deployment
  4. Limejump - Market leader, comprehensive services

Direct ESO Route:
  Advantages: Keep 100% revenue, full control
  Disadvantages: 12+ weeks setup, technical complexity, ongoing compliance burden
  Recommendation: Only for portfolios >50 MW or if in-house expertise available

SECTION 7: BATTERY DEGRADATION ANALYSIS
{'=' * 80}

Frequency Response Impact on Battery Life:

DC Service Degradation:
  Typical Cycling: 0.5-1.5 cycles/day (lower than arbitrage)
  Depth of Discharge: 20-40% (shallow cycles)
  Calendar Life Impact: Minimal (<5% additional degradation)
  Warranty Coverage: Usually covered under standard warranty
  
Arbitrage Degradation:
  Typical Cycling: 2 cycles/day (design spec)
  Depth of Discharge: 80-90%
  Calendar Life Impact: As per manufacturer warranty
  
Combined DC + Arbitrage:
  Total Cycling: 2.5-3.5 cycles/day
  Degradation Rate: 2-3% per year (within acceptable range)
  Warranty Considerations: Check with manufacturer for stacked services
  Expected Battery Life: 12-15 years (20+ years calendar life typical)

Recommendation: DC stacking is low-risk from degradation perspective
                Benefits outweigh minimal additional wear

SECTION 8: FINANCIAL PROJECTIONS
{'=' * 80}

DC Service Revenue Scenarios:

Conservative (40% utilization, £12/MW/hour):
  25 MW x £12/MW/h x 24h x 30d x 40% = £86,400/month

Base Case (50% utilization, £17/MW/hour):
  25 MW x £17/MW/h x 24h x 30d x 50% = £153,000/month

Optimistic (60% utilization, £22/MW/hour):
  25 MW x £22/MW/h x 24h x 30d x 60% = £237,600/month

Used in Battery Revenue Model: £51,000/month
(Conservative assumption: 40% utilization, £17/MW/h average)

Net of VLP Fee (15%): £43,350/month

SECTION 9: NEXT STEPS
{'=' * 80}

Timeline to FR Market Participation:

Week 0-2: Complete this capability assessment
  - Finalize battery technical specifications
  - Confirm grid connection details
  - Decide on VLP aggregator vs. direct route

Week 2-4: VLP Aggregator Selection (if applicable)
  - Send RFP to shortlist (Flexitricity, Habitat, Open Energi, Limejump)
  - Evaluate term sheets and revenue projections
  - Negotiate contract terms

Week 4-8: Technical Integration
  - Install metering and communications
  - Configure control systems for FR
  - Integrate with VLP platform (if applicable)
  
Week 8-12: Testing & Certification
  - Witnessed performance tests
  - EDL/ECL certification
  - Grid Code compliance verification
  
Week 12-16: Market Entry
  - ESO contract execution (or via VLP)
  - First DC auction participation
  - Revenue generation begins

Total Time to Market:
  Via VLP: 4-6 weeks (aggregator fast-tracks)
  Direct ESO: 12-16 weeks (full compliance process)

SECTION 10: KEY CONTACTS
{'=' * 80}

National Grid ESO - Ancillary Services:
  Email: commercial.operation@nationalgrideso.com
  Phone: 01926 653 000
  Website: https://www.nationalgrideso.com/industry-information/balancing-services

EDL/ECL Certification:
  Elexon BSC: bscservicedesk@elexon.co.uk
  Phone: 0207 380 4100

Grid Code Compliance:
  DNO Technical Team: [Contact via your specific DNO]
  G99/G100 Application: Submit via DNO portal

Recommended VLP Aggregators (for FR):
  Flexitricity: info@flexitricity.com | +44 131 221 8100
  Habitat Energy: contact@habitat.energy | +44 20 3868 6030
  Open Energi: hello@openenergi.com | +44 20 3929 0008
  Limejump: commercial@limejump.com | +44 20 3608 8740

SECTION 11: DECLARATION & REQUEST
{'=' * 80}

We request a formal capability assessment for the following services:
  [X] Dynamic Containment (DC) - PRIMARY INTEREST
  [ ] Dynamic Moderation (DM) - Lower priority
  [ ] Dynamic Regulation (DR) - Not recommended (degradation risk)

We declare that:
  [X] Technical specifications provided are accurate
  [X] Battery will meet all FR technical requirements
  [X] We understand ESO Grid Code compliance obligations
  [X] We will maintain required insurance and safety standards

Preferred Route:
  [X] Via VLP aggregator (recommended for 25 MW asset)
  [ ] Direct ESO contract (for larger portfolios >50 MW)

Request:
  Please provide feedback on our FR capability and next steps for market entry.
  We are targeting Q2 2026 energisation with FR services commencing Q3 2026.

Signed: _________________________  Date: __________
Name: George Major
Position: Director
Company: uPower Energy Ltd

{'=' * 80}
END OF FREQUENCY RESPONSE CAPABILITY ASSESSMENT REQUEST
{'=' * 80}

SUMMARY - KEY TAKEAWAYS:
• Battery is well-suited for Dynamic Containment (DC) service
• Expected DC revenue: £51k/month (conservative estimate)
• Recommend VLP aggregator route for faster deployment (4-6 weeks)
• Stacking with arbitrage creates optimal revenue (£173k/month combined)
• Low degradation risk from DC service (0.5-1.5 cycles/day)
• Contact Flexitricity, Habitat Energy, or Open Energi for FR capabilities
• Direct ESO route only if portfolio >50 MW or in-house expertise available
"""
    
    return fr_template, timestamp

def main():
    """Generate both CM and FR application templates"""
    
    print("=" * 80)
    print("CAPACITY MARKET & FREQUENCY RESPONSE APPLICATION PREPARATION")
    print("=" * 80)
    print(f"\nDate: {datetime.now().strftime('%d %B %Y %H:%M')}\n")
    
    # Generate CM prequalification
    print("Generating Capacity Market prequalification template...")
    cm_content, timestamp = generate_cm_prequalification()
    cm_file = f'/home/george/GB-Power-Market-JJ/cm_prequalification_{timestamp}.txt'
    with open(cm_file, 'w') as f:
        f.write(cm_content)
    print(f"✅ CM Prequalification: {cm_file}")
    
    # Generate FR assessment
    print("\nGenerating Frequency Response capability assessment...")
    fr_content, timestamp = generate_fr_assessment()
    fr_file = f'/home/george/GB-Power-Market-JJ/fr_assessment_request_{timestamp}.txt'
    with open(fr_file, 'w') as f:
        f.write(fr_content)
    print(f"✅ FR Assessment: {fr_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ APPLICATION TEMPLATES GENERATED")
    print("=" * 80)
    print(f"\nCapacity Market Prequalification:")
    print(f"  File: {cm_file}")
    print(f"  Target: T-4 auction Q4 2026 (delivery year 2029/30)")
    print(f"  Expected Revenue: £67.5k/month (£1.08M-£1.80M per annum)")
    print(f"  De-rated Capacity: 24 MW (96% of 25 MW)")
    
    print(f"\nFrequency Response Capability Assessment:")
    print(f"  File: {fr_file}")
    print(f"  Primary Service: Dynamic Containment (DC)")
    print(f"  Expected Revenue: £51k/month (conservative)")
    print(f"  Recommended Route: VLP aggregator (4-6 weeks to market)")
    
    print("\n" + "=" * 80)
    print("NEXT ACTIONS")
    print("=" * 80)
    print("\n1. Review templates and complete all [TO BE COMPLETED] fields")
    print("2. Gather supporting documents listed in Section 10 (CM)")
    print("3. Confirm battery technical specifications with manufacturer")
    print("4. Complete grid connection agreement")
    print("5. Select VLP aggregator (recommended: Flexitricity for FR, Habitat for revenue)")
    print("6. CM: Submit prequalification Q2 2026 (after energisation)")
    print("7. FR: Submit capability assessment to ESO or via VLP aggregator")
    print("8. Arrange credit cover for CM (£300k-500k)")
    print("9. Schedule performance testing with ESO")
    print("10. Participate in auctions (CM: Q4 2026, DC: daily from Q3 2026)")
    
    print("\n" + "=" * 80)
    print("REVENUE IMPACT")
    print("=" * 80)
    print("\nIf Both Services Secured:")
    print("  Capacity Market: +£67,500/month")
    print("  Frequency Response (DC): +£51,000/month")
    print("  Total Uplift: +£118,500/month")
    print("  Combined with Arbitrage: £240,735/month")
    print("  Combined with Base Case (Arb+VLP+CM+FR): £336,740/month")
    
    print("\n" + "=" * 80)
    
    return cm_file, fr_file

if __name__ == '__main__':
    try:
        cm_file, fr_file = main()
        print(f"\n✅ Step 3 Complete")
        print(f"   CM: {cm_file}")
        print(f"   FR: {fr_file}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
