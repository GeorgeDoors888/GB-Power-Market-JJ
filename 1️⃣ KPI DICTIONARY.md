1️⃣ KPI DICTIONARY

(Authoritative definitions + formulas)

⸻

A. MARKET SIGNAL KPIs

(What the system is doing — not what you earned yet)

KPI: Real-time Imbalance Price

Definition
The imbalance price applied to the current Settlement Period.

Formula
	•	If single pricing: Price = SSP = SBP
	•	Else:
	•	Long → SSP
	•	Short → SBP

Unit: £/MWh
Source: BMRS / operational price feed
Notes:
Do not label SSP=SBP as “balanced” — it indicates single-price conditions, often stress.

⸻

KPI: Single-Price Frequency

Definition
Percentage of Settlement Periods where SSP = SBP.

Formula (# SPs where SSP = SBP) / (Total SPs) Unit: %
Use: Battery risk asymmetry indicator

⸻

KPI: Rolling Mean Price (7d / 30d)

Definition
Rolling average of imbalance price over lookback window.

Formula AVG(imbalance_price) over last N days Unit: £/MWh
Warning: Mean alone does not describe regime — pair with volatility.

⸻

KPI: Price Volatility

Definition
Standard deviation of imbalance price over lookback window.

Formula STDDEV(imbalance_price) Unit: £/MWh
Interpretation: Battery optionality ↑ as volatility ↑

⸻

KPI: Price Regime

Definition
Categorical classification of price environment.

Rule
	•	Low: < £20/MWh
	•	Normal: £20–£80
	•	High: £80–£150
	•	Scarcity: > £150

Unit: category
Use: Strategy selection (charge / discharge / hold)

⸻

B. BALANCING MECHANISM ACTIVITY

(What the system operator is doing)

⸻

KPI: Dispatch Intensity

Definition
Rate at which BM acceptances occur.

Formula Total acceptances / hour Unit: acceptances/hour
Companion KPIs:
	•	% of SPs with ≥1 acceptance
	•	Median accepted MW

⸻

KPI: Acceptance Energy-Weighted Price (EWAP)

Definition
Average price weighted by accepted energy.

Formula nit: £/MWh
Important:
If no acceptances → EWAP = NULL (not zero)

⸻

KPI: SO-Flag Rate

Definition
Share of acceptances marked as SO-Flag (system events).

Formula SO-Flag acceptances / total acceptances Use: Detect stress, NGSEA-type events, abnormal dispatch

⸻

C. BATTERY OPERATING KPIs

(What you can physically do)

⸻

KPI: State of Charge (SoC)

Definition
Battery energy relative to maximum usable energy.

Formula Current MWh / Max MWh Unit: %

⸻

KPI: Headroom / Footroom

Definition
Available power to increase or decrease net export.

Formula
	•	Headroom = Max discharge MW − current MW
	•	Footroom = current MW − Max charge MW

Unit: MW

⸻

KPI: Equivalent Full Cycles (EFC)

Definition
Cumulative battery throughput normalised to full cycles.

Formula Σ(|energy throughput|) / (2 × usable capacity) Unit: cycles
Use: Degradation accounting

⸻

KPI: Cycle Value

Definition
Profit earned per equivalent full cycle.

Formula Battery profit (£) / EFC Unit: £/cycle
Decision use: Compare against degradation cost

⸻

KPI: Arbitrage Capture Ratio

Definition
How much of theoretical perfect arbitrage was captured.

Formula Actual arbitrage £ / Perfect-foresight arbitrage £ Unit: %

⸻

D. CHP OPERATING KPIs

(Heat-constrained generation economics)

⸻

KPI: Spark Spread (Realised)

Definition
Net margin from generating electricity from gas.

Formula Electricity revenue − Gas cost − Carbon − Variable O&M Unit: £/MWh

⸻

KPI: Heat Constraint Index

Definition
Fraction of time CHP output is limited by heat demand.

Formula Constrained hours / total running hours Unit: %

⸻

KPI: Starts / Stops

Definition
Number of CHP start events.

Use: Wear and reliability proxy

⸻

E. OUTCOME KPIs (THE ONLY “£” THAT MATTER)

⸻

KPI: Pay-as-Bid Revenue

Definition
Revenue from accepted BM bids/offers.

Formula Σ(accepted_MW × 0.5 × acceptance_price) ource: BOALF / BOD
Note: Not settlement

⸻

KPI: Imbalance Settlement Outcome

Definition
Final settlement cost or revenue from being long/short.

Source: P114 (SAA)
Unit: £
Important: Only P114 proves this

⸻

KPI: Total Trading Value

Definition
All revenues minus costs.

Formula Pay-as-bid
+ Wholesale
+ Ancillaries
± Imbalance
− Fuel
− Carbon
− Degradation PI: Worst-Case SP Loss

Definition
Largest single-SP loss in lookback window.

Use: Risk control

⸻

2️⃣ ONE-PAGE TRADER DASHBOARD LAYOUT

⸻

TOP ROW — MARKET STATE (Signal) [ Real-time Price ]  [ Price Regime ]  [ Volatility ]  [ Single-Price % ] ECOND ROW — SYSTEM ACTIVITY [ Dispatch Intensity ]  [ EWAP ]  [ SO-Flag Rate ] THIRD ROW — ASSET READINESS BATTERY
[ SoC ] [ Headroom ] [ Footroom ] [ EFC Today ]

CHP
[ Output MW ] [ Spark Spread ] [ Heat Constraint % ] OURTH ROW — POSITION & RISK OURTH ROW — POSITION & RISK BOTTOM ROW — VALUE (Outcome) [ Pay-as-Bid £ ]  [ Imbalance £ ]  [ Wholesale £ ]  [ TOTAL £ ] 
⸻

SIDE PANEL — ALERTS (Actionable)
	•	High volatility + low SoC
	•	SSP spike
	•	Negative spark spread
	•	GC/DC envelope breach
	•	Missed delivery risk

⸻

Why this works
	•	No mixing of operational signals and settlement truth
	•	Battery and CHP treated differently (as they should be)
	•	Every £ has a provenance (BM, settlement, wholesale)
	•	Trader-first: shows what to do now, not just what happened