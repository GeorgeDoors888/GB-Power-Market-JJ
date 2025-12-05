we are going around in circles, this was documented see: System Buy Price (SBP) and System Sell Price (SSP) merged into a single Imbalance Price (IP) in Great Britain through Elexon's BSC (Balancing and Settlement Code) Modifications, notably P137 (2003) and P136 (2003), to simplify energy settlement, create a fairer 'cash-out' price for imbalances, and reflect real-time balancing costs more accurately, removing separate buyer/seller prices for better market efficiency and transparency, with implementation in phases around 2003-2004. 
When Did They Merge?
The process began with Modification Proposals (MPs) raised in August 2003, including P137 (Barclays Capital) and P136 (National Grid).
These aimed to redefine SBP and SSP to align them more closely with the actual cost of balancing the grid.
The merged single price, now the Energy Imbalance Price (IP), was implemented as part of the Central Volume Aggregation (CVA) February 03 Release in March 2003, with further refinements over time. 
Why Did They Merge?
Complexity & Inaccuracy: The previous separate SBP and SSP (System Buy/Sell Prices) often resulted in complex, non-representative pricing for imbalance, not reflecting real grid conditions.
Fairer Settlement: A single price ensures parties pay or receive money based on the actual marginal cost of balancing the system, whether adding or reducing energy.
Market Efficiency: It simplified imbalance settlement, making it more transparent and encouraging efficient behaviour in the balancing mechanism.
Elexon's Role: Elexon manages these modifications (MPs) under the BSC to continually improve the UK wholesale electricity market's operation, data, and settlement. see this document as background.also : 
 Elexon BSC Logo
Menu
You are here:Home Settlement & Invoicing Imbalance Pricing
Imbalance Pricing
Add Bookmark to My BSC dashboard
Glossary
Toggle Tooltip
The Imbalance Price is used to settle energy imbalance volumes. At the end of a Settlement Period, BSC Systems compare a Party’s contracted (traded) volume with the metered volume of energy used in the Settlement Period. If a Party is in imbalance of its contracted volume, then it will be subject to imbalance charges.
On this page
Featured content
Indicative Settlement Price data now available on the Insights Solution
26 February 2024
Enhancing our customer enquiry processes using Elexon Support

18 December 2023 Read More
Market Index Definition Statement Review 2023

4 October 2023 Read More
How it relates to you

There are two Energy Imbalance Prices for each Settlement Period. These are:

System Buy Price (SBP)
System Sell Price (SSP)
The System Sell Price (SSP) and System Buy Price (SBP) are the ‘cash-out’ or ‘Energy Imbalance’ prices. These are used to settle the difference between contracted generation, or consumption, and the amount that was actually generated, or consumed, in each half hour trading period.

However now there is a single price calculation, so SBP will equal SSP in each Settlement Period.  These prices are applied to Parties’ imbalances to determine their imbalance charges.

Latest pricing

SSP and SBP (in £/MWh) and the Net Imbalance Volume (NIV) (in MWh) for every Settlement Period in a particular day.

Indicative SSP and SBP on the Insights Solution
Finalised Settlement data is published in Best View Prices on BSC Portal
Accessing data

Elexon Portal
Insights Solution
More about the data

Pricing and related data used in BSC processes includes:

System Sell Price and System Buy Price
Market Index Price and Volume
Parameters used in the calculation of System Prices (Energy Imbalance Price):
NIV – Net Imbalance Volume
PAR – Price Average Reference Volume
DMAT – De Minimis Acceptance Threshold
CADL – Continuous Acceptance Duration Limit
MIDS – Market Index Definition Statement
LoLP – Loss of Load Probability
VoLL – Value of Loss Load
RSVP – Reserve Scarcity Price
Utilisation Price
More about pricing

A Party is out of balance when its contracted energy volume does not match its physical production or consumption.

SSP is paid to BSC Trading Parties who have a net surplus of imbalance energy, and SBP is paid by BSC Trading Parties who have a net deficit of imbalance energy. These prices are designed to reflect the prices associated with the Balancing Mechanism Bids and Offers selected by National Grid to balance the energy flows in the Transmission System, as well as reserve scarcity.

Calculating SSP and SBP price

For each half hour trading period, the ‘cash-out’ or ‘energy imbalance’ prices (System Sell Price and System Buy Price) will be associated with Balancing Mechanism Bids and Offers accepted by National Grid as well as the Balancing Services used for that specific half hour.

Market Index Data Volume and Price

Market Index Data (MID) is used in the calculation of the Market Index Price for each Settlement Period, and reflects the price of wholesale electricity in the short-term market.
MID Volume (in MWh) and Price (in £/MWh) for every Settlement can be obtained from BMReports.com and the Elexon Portal.

More on Market Index Definition Statement for Market Index Data Provider(s)
System Prices (Energy Imbalance Price) parameters

Net Imbalance Volume (NIV)

NIV is the net imbalance volume (in MWh) of the total system for a given Settlement Period. It is derived by netting Buy and Sell Actions in the Balancing Mechanism. Where the NIV is positive, the system is short and would normally result in the SO accepting Offers to increase generation/decrease consumption.

Where NIV is negative, the system is long and the SO would normally accept Bids to reduce generation/increase consumption. It is subject to change via Standard Settlement Runs.

Price Average Reference (PAR) Volume

The Price Averaging Reference (PAR) volume is used to tag Bid-Offer acceptances such that a maximum volume of PAR MWh is used to set the Energy Imbalance Price.

Please note: The current value of PAR is 1MWh.

The PAR may only be amended by an Approved Modification.

De Minimis Acceptance Threshold (DMAT)

The De Minimis Acceptance Threshold is a parameter used to eliminate Bid/Offer acceptances of small volume. DMAT is currently 0.1MWh.

This value is written into the text of BSC Section T Paragraph 1.7 the BSC Panel may review it from time to time.

Proposed revisions to the value of DMAT are consulted upon with the Transmission Company and Trading Parties before a Panel determination is made, and are subject to Ofgem’s approval.

Continuous Acceptance Duration Limit (CADL)

CADL is used to flag short duration Bid-Offer acceptances, associated with system balancing actions in the Energy Imbalance Price calculation.

A Bid-Offer acceptance relating to any given Balancing Mechanism (BM) Unit will be flagged in the system price calculation if it has duration of less than the CADL value in minutes. CADL is currently 10 minutes.

CADL is defined in BSC Section T Paragraph 3.1B.

The BSC Panel may revise the value of CADL after consulting with BSC Parties but subject to Ofgem’s approval.

Loss of Load Probability (LoLP)

The LoLP is a measure of system reliability calculated by the System Operator (SO) for each Settlement Period.

The System Operator’s methodology is set out in the Loss of Load Probability Calculation Statement.

Please note: Currently a dynamic LoLP function is used.

Value of Loss Load (VoLL)

The VoLL price is an assessment of the average value that electricity consumers attribute to the security of supply. It is currently set at £6,000/MWh.

Reserve Scarcity Price (RSVP)

Both accepted BM and non-BM Short Term Operating Reserve (STOR) Actions are included in the calculation of System Prices as individual actions, with a price which is the greater of the Utilisation Price for that action or the RSVP.

The RSVP is based on the prevailing system scarcity, and is calculated as the product the VoLL and the LoLP for each Settlement Period.

Utilisation Price

The price (in £/MWh) sent by the SO in respect of the utilisation of a STOR Action which:

in relation to a BM STOR Action shall be the Offer Price
in relation to a Non-BM STOR Action shall be the Balancing Services Adjustment Cost
Market Index Definition Statement (MIDS) Parameters

The Market Index Definition Statement (MIDS) defines two main parameters.

Individual Liquidity Threshold (ILT)
time and product weightings
The Individual Liquidity Threshold (ILT) and (time and product) weightings parameters are published on the Elexon Portal.

Market Index Data is used in Settlement to calculate a price, expressed in £/MWh in respect of each Settlement Period, which reflects the price of wholesale electricity in Great Britain in the short-term market.

The Market Index Definition Statement (MIDS) defines the parameters for use by the Market Index Data Provider (MIDP) in the provision of Market Index data (MID) to the Settlement Administration Agent (SAA).

The MIDS is reviewed by the BSC Panel at least once a year. Any proposed changes are consulted upon with BSC Parties before the Panel determines whether a change is to be made.

A change to the MIDS is subject to approval by Ofgem.

More on Market Index Definition Statement for Market Index Data Provider(s)
Sidebar
Contact information

Elexon Support
Follow this page

Enter your email below to subscribe for regular updates.

Email AddressSubscribe
Training services

Training on Imbalance Settlement
Introduction to the energy market
Guidance Notes

BSC Section T Simple Guide
Imbalance Pricing
BSC codes

BSC Section T
Accessibility

Please let us know if you cannot access this information or need it in an alternative format.

communications@elexon.co.uk
My BSC

Click on the X next to any of the icons to replace them with a short-cut link to the page you are currently on or search for a specific page.

BSC Insights & ‘Spotlight On’ articles
Previous Circulars
Training videos and services
Market Entry & Exit
Charge Codes and Switch Regimes
Add New
MY BSC QUICKLINKS
CONTACT
SUBSCRIPTIONS
BSC
CMAG
DIP
EMRS
MF
MHHS
NCC
Corporate Policies
Privacy Policy
Cookie Policy
Using this website
A-Z Index
Glossary
Contact
Linkedin
X
Glassdoor
Copyright © 2025 Elexon
COOKIES SETTINGS  
ompleted - Python Implementation:

populate_bess_enhanced.py - BESS data with battery calculations (337 rows, 6-stream reven ✅ Section 1: DNO Lookup - Populated
✅ Section 2: HH Profile - Populated (500/1000/1500 kW)
✅ Section 3: BtM PPA Analysis - Populated
⚠️ Section 4: Enhanced Revenue - Not yet deployed (expected) New Files Created:

test_bess_integration.py - Verification script
BESS_INTEGRATION_COMPLETE.md - Full documentation (15KB) 📝 Files Modified
Updated for Integration:

bess_profit_model_enhanced.py - Added start_row=60 parameter to avoid conflicts
dashboard_pipeline.py - Integrated enhanced update that preserves existing sections
bess_integration.gs - Formats row 60+ only Created BESS_INTEGRATION_COMPLETE.md

Perfect! Now let's create a quick re DEPLOYMENT_CHECKLIST.md+13-1
Perfect! Now let's cr bess_profit_model_enhanced.py+24-8 Read dashboard_pipeline.py, lines 200 to 247 Code that powers it:

update_btm_ppa_from_bigquery.py - Main calculator
dno_lookup_python.py - DNO rates lookup
generate_hh_profile.py - Demand profile generator
calculate_bess_element_costs.py - Cost breakdowns
What's New (Adds to Your Sheet
