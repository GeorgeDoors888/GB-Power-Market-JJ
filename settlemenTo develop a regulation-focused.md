settlemenTo develop a regulation-focused report using the Baselining Methodology Document in the context of Virtual Trading Parties (VTPs), CHP, batteries, frequency response, balancing services, and DNO flexibility, could you please clarify the following:
	1.	Which specific regulations or policy objectives should the report align with (e.g. Ofgem flexibility strategy, Smart Systems and Flexibility Plan)?
	2.	Should the report target a regulatory gap analysis, policy recommendations, or compliance review?
	3.	Should the focus be GB-wide or aligned with a specific DNO area or market segment (e.g. LV flexibility services, frequency response only)?
	4.	Are there specific BigQuery datasets you want included in the analysis? If so, please provide names or descriptions.
	5.	Should we include worked examples for each asset type (CHP, battery, etc.) within a VTP framework?

This will help tailor the regulatory insights more accurately to your needs.Great. I will develop a regulatory report for Great Britain covering the integration and settlement treatment of Virtual Trading Parties (VTPs), Combined Heat and Power (CHP), and battery energy storage (BESS) in relation to frequency response, balancing services, and DNO flexibility. This will use the Elexon Baselining Methodology Document and data sources from BigQuery and the Elexon website. The report will include regulatory context, worked examples for each asset type, and an integrated use case combining CHP with BESS.

I’ll format the report with clear sections and include a comprehensive glossary of terms. Integrating Virtual Trading Parties (VTPs), CHP, and BESS into GB Flexibility Markets

Introduction

The energy landscape in Great Britain (GB) is evolving to enable more participation from flexible and distributed resources. Recent regulatory changes under the Balancing and Settlement Code (BSC) and Ofgem guidance have introduced new roles and methodologies to facilitate aggregators and behind-the-meter assets in providing services. In particular, the Baselining Methodology Document (Version 3.1) and BSC Modifications like P376 and P415 establish how Virtual Lead Parties (VLPs) and the new Virtual Trading Party (VTP) role can integrate assets such as Combined Heat and Power (CHP) units and Battery Energy Storage Systems (BESS) into various markets. These markets include frequency response services (to help control grid frequency), the Balancing Mechanism and other balancing services, and emerging Distribution Network Operator (DNO) flexibility markets. This report outlines the regulatory framework, compliance requirements, and practical examples of how CHP and BESS assets (alone or combined) can participate in these markets under the new arrangements. We reference the Elexon Baselining Methodology and relevant BSC modifications (notably P376 and P415), highlight applicable codes and regulations (from Ofgem, Elexon, the Grid Code, etc.), and describe baseline calculation and verification processes. Worked examples for a standalone CHP, a standalone battery, and a combined CHP+battery setup are provided to illustrate engagement with the VTP/VLP framework. A final section provides a comprehensive glossary of terms and acronyms for clarity.

Regulatory Framework Overview

Ofgem and Elexon Reforms: Ofgem – as the GB energy regulator – has been driving reforms to open markets to new participants and ensure codes facilitate flexibility. Key BSC modifications approved by Ofgem include P376 and P415, which underpin the current framework. Modification P376, implemented in February 2023, introduced the use of an approved baselining methodology to determine expected energy volumes for certain assets instead of relying solely on Physical Notifications (PNs) ￼ ￼. This was in response to the difficulty some flexible assets had in providing accurate PNs, leading to settlement inaccuracies. By allowing recent historical metered data to set a Baseline (an estimate of what the energy flow at a site would have been under “normal” conditions), P376 decouples settlement from real-time dispatch instructions. National Grid ESO (the System Operator) still uses participants’ Final Physical Notification (FPN) for dispatch purposes, but settlement calculations now use the calculated baseline to more accurately verify delivered balancing services ￼ ￼. This change improved fairness by ensuring providers (like demand-side responders or small generators) are paid or charged based on what they actually delivered relative to a credible baseline, rather than a potentially mis-estimated FPN.

Modification P415 (effective November 2024) extends this further by creating the Virtual Trading Party (VTP) role and allowing independent aggregators to participate directly in the wholesale energy market ￼. Prior to P415, independent aggregators (VLPs) could only access the Balancing Mechanism and ancillary services, and any wholesale market trading of their flexibility had to be mediated by a licensed supplier ￼ ￼. P415 removes this barrier by delinking the wholesale trading role from holding a supply license, enabling VLPs to register as VTPs and trade energy deviations on equal footing with suppliers ￼. In approving P415, Ofgem recognized it as a major step to “facilitate access to wholesale markets for flexibility dispatched by VLPs” and noted that it includes compensation mechanisms to address impacts on suppliers ￼ ￼. Under the P415 framework, when an aggregator’s action causes a consumer’s consumption to differ from what the supplier expected, a compensation arrangement ensures the original supplier is kept whole (these costs are mutualised across suppliers, per Ofgem’s decision) ￼. A new concept of “Deviation Volumes” was introduced: this represents the difference between a site’s expected consumption/generation (its baseline forecast) and the actual metered consumption/generation, attributable to the VLP/VTP’s action ￼. In other words, deviation volumes are the flexible volumes traded by the VTP in the wholesale market, and they are calculated and settled separately so that the energy can be traded without shifting the customer to a different supplier ￼. This ensures consumers (and their assets) can earn revenue from flexibility via an aggregator without physically changing suppliers, aligning with Ofgem’s objectives for competition and innovation.

Roles and Market Participants: Under these modifications, the roles in the market have been expanded:
	•	Virtual Lead Party (VLP): A category of BSC Party (introduced by earlier mods like P344) that aggregates demand or generation from customers to provide balancing services (e.g. in the Balancing Mechanism) ￼. VLPs register Secondary BM Units (sBMUs) consisting of one or more metering points (sites) in the Supplier Volume Allocation (SVA) system. Unlike traditional suppliers or generators, a VLP’s sole function is to deliver balancing services (they do not supply energy to consumers in the retail sense). VLPs can control MSID Pairs (paired Import/Export metering points at a site) or Asset Metering (AMSID) Pairs behind a site’s boundary. Prior to 2024, VLPs could not directly trade in wholesale markets ￼ ￼ – their activities were limited to ancillary services, the Capacity Market, and the Balancing Mechanism.
	•	Asset Metering Virtual Lead Party (AMVLP): A subtype of VLP introduced by BSC Modification P375 (implemented in 2022), which allows aggregators to use asset-level metering. An AMVLP can register Asset Metering Systems (assets behind the meter, like a CHP unit or battery with its own meter) and use those readings for settlement (a practice called asset differencing if separating the asset’s impact from the site’s main meter). This role is important for behind-the-meter resources, as it improves accuracy by measuring the asset’s output directly rather than inferring it from the site’s net meter. (While P375 is not the main focus of this report, it is a complementary development that enables more precise baseline calculations for individual assets.)
	•	Virtual Trading Party (VTP): A new BSC role created by P415 (effectively an additional role that a VLP/AMVLP can attain) to access wholesale energy trading. A VTP must be a qualified VLP/AMVLP that extends its capability to trade “deviation volumes” in the wholesale market without a supply license ￼ ￼. In practice, a VTP registers Secondary BM Units that must be baselined – meaning the units are set up so that their expected consumption/generation is determined by an approved baseline methodology, allowing calculation of deviations ￼ ￼. The VTP role went live in November 2024 alongside the P415 rule changes ￼. In essence, a VTP-enabled aggregator can submit Wholesale Market Activity Notifications and trade flexibility on power exchanges or via bilateral trades, and Elexon will settle the resulting deviation volumes between the VTP and the supplier.
	•	Suppliers: Traditional electricity suppliers continue to serve customers and are the default Balancing Responsible Parties for those customers’ metered volumes. Under the new framework, suppliers remain financially responsible for their customers’ energy imbalances, but adjustments are made so that when a VLP/VTP dispatches a customer’s asset, the supplier’s position is corrected by Elexon (so the supplier is not unduly penalized or rewarded for the aggregator’s actions) ￼ ￼. Suppliers impacted by an aggregator’s wholesale trades are compensated at a price reflecting the energy cost, via a mutualised fund ￼. Suppliers and VLPs therefore must coordinate on data (e.g., suppliers are informed of which sites are enlisted with a VLP through industry data flows), and suppliers have the right to dispute allocations of their customers to VLP portfolios in certain cases (per BSC procedures for MSID allocation).
	•	Distribution Network Operators (DNOs) / Distribution System Operators (DSOs): DNOs operate the regional distribution grids and are increasingly procuring flexibility services to manage local network constraints (e.g. congestion or voltage issues). While these DNO flexibility markets have historically operated outside of the BSC central settlement, there is a strong push to align them with national markets. Ofgem’s DSO transition incentives and the Energy Networks Association (ENA) Open Networks project have established standardized processes for DNOs to tender for flexibility from resources like CHP, batteries, and demand response. The regulatory framework is converging such that assets might participate in both DNO-led and ESO-led markets using common platforms and standards. For example, Ofgem has initiated a Flexibility Market Asset Registration (FMAR) system – to be operated by Elexon – which will serve as a “one-stop-shop” to register flexible assets for both local and national markets ￼ ￼. By 2027, an aggregator will only need to register an asset once to then use it in any of the more than 20 local DNO markets or national services ￼. This reduces barriers and ensures DNOs and the ESO have a shared view of resource participation. Already, Elexon (through a Market Facilitator role) is working with Ofgem and stakeholders to drive alignment between local and national flexibility markets and remove barriers to entry ￼. Part of this alignment involves standardizing baseline calculation methods for DNO services, as discussed later. DNOs themselves must comply with Ofgem’s requirements to consider flexibility solutions (instead of simply building new network infrastructure), and they are subject to a DSO Incentive scheme from April 2024 onward to encourage market development (per Ofgem’s DSO incentive reports).
	•	National Grid Electricity System Operator (NGESO or simply ESO): The ESO remains responsible for balancing the national system and procuring ancillary services (frequency response, reserve, etc.). It interacts with VLPs/VTPs in the Balancing Mechanism and through ancillary service contracts. The Grid Code and associated codes (like the Connection Conditions and Operating Codes) impose technical requirements on any connected generation or storage providing frequency response or other services. For example, large CHP or storage units must meet certain performance standards (such as response speed, droop settings for frequency response, etc.) as conditions of their connection agreements. In practice, assets providing frequency response (like Dynamic Containment, Dynamic Regulation, or older Firm Frequency Response) must pass NGESO’s testing and meet the service specification (which often references Grid Code capabilities, though the procurement is via contract). While the Grid Code governs the technical capability (e.g. mandatory frequency response is required of large generators above 50MW as a license/connection condition), the BSC and ancillary service agreements govern how the delivery is measured and paid. The recent frameworks do not alter the Grid Code; rather, they create new routes for smaller or aggregated assets to contribute without being large power stations. Nonetheless, all participants must ensure their equipment and operations comply with relevant technical standards (Grid Code for transmission-connected or large plant, Distribution Code and Engineering Recommendations like G99 for distribution-connected generation including CHP/BESS, etc.). Compliance with these codes is essential for safe operation and is typically verified during connection commissioning and via performance monitoring by the ESO and DNOs.

In summary, as of late 2024 GB has a multi-layer regulatory framework that enables flexibility from VLPs/VTPs while ensuring traditional market actors (suppliers, network operators) and system reliability are kept whole. The BSC changes are central to enabling these new transactions, and they work in concert with Ofgem’s broader policies (like encouraging DNOs to use flexibility, and clarifying the legal status of storage as generation for licensing and charging purposes).

Baselining Methodology (BSC Section S and Document v3.1)

A cornerstone of integrating independent flexible assets is the baselining methodology – a standardized way to estimate what a site or asset would have consumed or generated in the absence of a flexibility dispatch. Baselining allows “measuring” the service delivered (i.e., the difference made by the asset’s action). Under P376, the BSC was updated to include Section S3 and S13 provisions for baselining, and a Baselining Methodology Document (a Category 3 BSC Configurable Item) details the approved calculation methods. Version 3.1 of this document (effective late 2024) corresponds with the implementation of P415, incorporating adjustments for VTP activities. Key points from the Baselining Methodology Document v3.0/3.1 include:
	•	Approved Method (BL01): Currently the BSC Panel has approved one standard baseline calculation method (referred to as BL01). It uses a “High X of Y” approach with an In-Day Adjustment. In simple terms, BL01 selects a set of recent historical days and averages their half-hourly values to form an initial baseline, then adjusts that baseline on the event day if needed to better match the pre-event trend. Specifically, for each Settlement Day where a baseline is needed, the Supplier Volume Allocation Agent (SVAA) will look back at up to 60 days of historical data for the same site or asset (the “Baselined Entity”). It filters for “Eligible Days” that fall within D–60 to D–1, matching the day-type (weekday vs weekend) and having valid half-hourly metered data ￼. Certain days are excluded: any days the Lead Party (aggregator) has flagged as Event Days (i.e., days with unusual activity such as prior service dispatches) are removed, as are days with clock changes or missing data ￼ ￼. From the remaining eligible days, the methodology selects the top few days with the highest usage in the same time period to ensure a representative but non-inflated baseline. For BL01, up to 10 days are selected for a Working Day baseline (or 4 days for a non-working day) ￼ – typically the days with the highest consumption in each time period are chosen, which is a common practice to avoid underestimating flexible load baselines.
	•	Unadjusted Baseline: Once the reference days are chosen, the Unadjusted Baseline Value is computed for each settlement period of the target day by averaging the metered values of those periods from the selected historical days ￼. This yields an initial profile of what the site tends to do on a similar day. If no further action occurred, this would be the baseline.
	•	In-Day Adjustment: If the asset is dispatched or trades on that day, the baseline may need a shift to reflect the day-specific behavior. BL01 includes an In-Day Adjustment mechanism to calibrate the baseline up or down based on the period just prior to a dispatch event ￼ ￼. The In-Day Reference Window for BL01 is a 3-hour window immediately before the dispatch period (or before a wholesale trade execution) ￼ ￼. Essentially, the SVAA compares the average consumption in that 3-hour window from the unadjusted baseline to the actual metered data in that window. Any difference is assumed to be a systematic error in the baseline (e.g., the site was trending higher or lower than the historical average that day) and is added as a flat adjustment to the baseline for the dispatch period ￼ ￼. This helps the baseline start at the right level when the event begins. However, important exceptions exist: if no dispatch or trade occurred that day, no in-day adjustment is applied to the baseline used for settlement (it stays unadjusted) ￼ ￼. Moreover, if the only activity was a VTP wholesale trade (and no ESO dispatch acceptance), the methodology sets the In-Day Adjustment to zero ￼ ￼. In other words, a Wholesale Market Activity Notification from a VTP, by itself, does not trigger any baseline “drift” correction – the baseline remains purely the historical average. This rule was introduced to handle the P415 case: if an aggregator trades in the wholesale market, the baseline should remain the expected consumption absent that trade (so the entire deviation from baseline is attributed to the trade). Only an ESO dispatch (e.g., a Balancing Mechanism Bid-Offer Acceptance) triggers the normal in-day adjustment calculation. If neither an ESO acceptance nor a VTP trade occurs, the SVAA will still calculate hypothetical in-day adjustments for each period for assurance purposes (to monitor baseline accuracy), but those adjustments are not applied in settlement ￼ ￼. In all cases where no instructed event happens, the baseline used in settlement ultimately defaults to the actual metered data (meaning no delivered volume – this prevents false credits) ￼ ￼.
	•	Baseline Outputs and Use: The outcome of the baseline process is an MSID Baseline Value for each half-hour (Settlement Period) for each “Baselined Entity” (which could be an MSID Pair or an AMSID Pair). This baseline is expressed in MWh and represents “an estimate of what the net metered volume would have been in the absence of any dispatch by the ESO or any wholesale trading by a VTP” ￼. These values are reported to the Lead Party (the VLP/VTP) and are used in settlement to calculate delivered volumes. Specifically, for a given period, if a balancing service was delivered or a trade executed, the delivered (or deviation) volume = actual metered volume – baseline volume. This difference can be positive or negative depending on whether the asset decreased consumption/increased export (creating a “Delivered Volume” credited to the VLP) or increased consumption/decreased generation (which could be an instructed increase for certain services, or a deviation the other way). The baseline methodology accounts for import vs export metering: if a site has both import and export MSIDs, the baseline is split into import and export components (non-negative values for each) so that settlement can allocate volumes correctly to each meter ￼. For example, if a CHP normally exports power, its export MSID would carry the positive baseline generation, whereas a reduction in CHP output (to provide downward reserve) would show up as a shortfall against that export baseline (which settlement treats as delivered downward balancing energy).
	•	Governance: The Baselining Methodology Document is maintained by the BSC Panel (not by full code modification votes, since it’s a Category 3 document). Section S13.2 of the BSC requires the Panel to review and update the methodology if significant changes occur (e.g., major shifts in typical demand due to something like a pandemic, or changes in network charging that alter behavior) ￼ ￼. Parties such as Suppliers, VLPs, or VTPs can request a review if they believe the baseline isn’t accurately representing certain technologies or situations ￼. This is important as new asset types (or combinations like hybrid CHP+storage) emerge – if evidence shows the current baseline method yields systematic errors for those assets, the methodology can be refined. Additionally, aggregators must adhere to processes defined in BSC Procedure BSCP602 to interact with the baseline system – for instance, notifying “Event Days”. An Event Day is a day on which the site’s data was atypical due to specified reasons: delivery of a balancing service, participation in virtual trading (VTP activity), a site outage or equipment failure, or similar exceptional events ￼ ￼. Aggregators can declare such days so that they are excluded from baseline history (preventing an anomalous low or high day from skewing future baselines) ￼ ￼. The Lead Party must keep evidence of the event (e.g., dispatch instructions, outage reports) in case of audit ￼. This requirement underscores the compliance aspect: VLPs/VTPs are subject to Performance Assurance checks. Elexon’s Technical Assurance Agent or BSC Auditor can request proof that a declared Event Day indeed met the criteria, and generally ensure that baselines are not being manipulated.

Overall, the Baselining Methodology provides a transparent and standardized way to measure flexibility services. For market participants, understanding this baseline is crucial: it forms the reference for how much energy was actually “freed up” to sell to the ESO or into the market.

Integration into Frequency Response and Balancing Services (ESO Markets)

CHP and Battery assets can engage in NGESO’s balancing services in several ways: through the Balancing Mechanism (BM), via ancillary service products (like frequency response or reserve services), or the newer Demand Flexibility Service (DFS) trials. The regulatory frameworks ensure that whether the asset participates via a supplier or via an independent VLP, the delivery is accounted for and compliant with the rules.

Balancing Mechanism (BM): This is the real-time balancing market where NGESO accepts offers to increase or decrease generation/demand. Aggregators (VLPs) can participate in the BM by registering their resources as Secondary BM Units. A CHP unit or battery, if operated by a VLP, is typically assigned to a Secondary BM Unit that might contain just that asset or a portfolio of assets in the same Grid Supply Point (GSP) zone. The VLP offers Bids (to reduce generation or increase demand) or Offers (to increase generation or reduce demand) from that BMU to NGESO in the BM systems. When NGESO wants to activate it, they issue a Bid/Offer Acceptance (BOA).

From a regulatory standpoint, once a BOA is issued to a VLP’s BMU, settlement needs to verify how much was delivered. This is where the P376 baseline comes into play. Physical Notifications (PNs) are still submitted by the VLP to NGESO for scheduling (the VLP must indicate an expected profile – often they will use the baseline as the PN since it’s their best forecast of the asset without dispatch). But for settlement, instead of comparing actuals to that PN, the system uses the calculated Baseline Value as described earlier. If, for example, a stand-alone CHP is told to reduce output by 2 MW for an hour via a BOA, the baseline might have been, say, 5 MW export (based on historical data for that hour) and the actual metered export turned out to be 3 MW. The Delivered Volume for that Settlement Period would be baseline (5) minus actual (3) = 2 MWh delivered reduction, matching the instructed amount. This volume is assigned to the VLP’s account as a balancing service delivered, and the corresponding adjustment is made to the supplier’s account so that the supplier’s imbalance is as if the CHP had produced its normal 5 MW ￼ ￼. If the CHP under-delivered (say it only reduced to 3.5 MW, delivering 1.5 MW instead of 2), then 0.5 MWh would count as non-delivery and could expose the VLP to non-delivery charges per the BSC rules (ensuring compliance to what was instructed).

It’s worth noting that the Grid Code requires large generators (including large CHP plants, typically over 50 MW) to be able to respond to frequency and accept dispatch signals. Smaller resources aggregated by a VLP are not individually under Grid Code control, but the aggregator’s BMU as a whole is expected to follow dispatch instructions. NGESO’s systems (via the Wide Access API and electronic dispatch systems) send signals to the VLP, and the VLP must then orchestrate their assets to deliver. There is a requirement to submit Delivered Volumes back to Elexon (through the SVAA) after an event ￼ ￼. However, with baselining, Elexon itself calculates the delivered volume, so what the VLP submits is essentially a confirmation at MSID Pair level. The SVAA apportions the total metered volume between the VLP and the Supplier for settlement, using the baseline to figure out the VLP’s share ￼ ￼. VLPs thus must maintain accurate metering and data communication to ensure the baseline inputs (historical metering) and outputs (delivered volumes) are correct.

Frequency Response Services: NGESO transitioned in 2021-2022 from static Firm Frequency Response to dynamic services like Dynamic Containment (DC), Dynamic Regulation (DR), and Dynamic Moderation (DM). These services typically involve an asset providing rapid power changes in response to frequency deviations or setpoint signals. Technically, a CHP or a battery can participate if they meet the speed and accuracy requirements. For a CHP, this might be challenging unless it has fast-acting controls or can be paired with a dump load or storage; batteries, on the other hand, excel at this due to instantaneous response. The market entry for these services is usually via a tender or auction outside the BSC (they are procured as ancillary contracts). However, measurement of performance still matters for settlement of these services. For dynamic frequency response, NGESO monitors the asset’s output against a baseline or setpoint continuously during the service window. The baseline in that context is not the P376 baseline, but rather a real-time setpoint (for example, the instructed pre-frequency-response level, or a given dispatch level around which the asset should modulate). For instance, a battery contracted for Dynamic Containment might be instructed to hold at 0 MW and then inject or absorb power as frequency changes; its performance is measured by comparing actual power to what it should be doing at a given frequency. These specifics are governed by the service contract terms and Grid Code (especially the Balancing Code and relevant performance monitoring standards). If the asset delivers as expected, it gets paid the service fee; if not, there may be penalties or non-delivery payments.

Where the BSC baseline and VLP/VTP framework come in is if these services are delivered by an independent aggregator. As of late 2024, VLPs can and do participate in frequency response tenders (several have provided Dynamic Containment via aggregated batteries, for example). The settlement of those services might be handled via the BSC if they are run through the Balancing Mechanism (some frequency responses can be called via BM dispatch as well), or via separate ancillary service settlement processes. For most frequency response, NGESO pays the VLP directly for availability and performance, and adjusts the baseline for any net energy delivered. In some cases, energy delivered as part of frequency response might be treated as an accepted offer/bid (particularly for DR or DM services that look like a series of small energy deviations). Regardless, the asset’s baseline (expected load) is key to determining how much extra energy the asset provided or consumed due to frequency deviations. If a CHP is providing a downward frequency response (reducing output when frequency is high), it needs to have a notion of what its output would have been (perhaps its dispatch plan or baseline) to gauge the response volume. NGESO’s monitoring will handle this in real-time; on the BSC side, if that response is not explicitly integrated, it may simply reflect in the actual metered data being different from the FPN. P376’s baseline can optionally be used by suppliers too – if a supplier’s asset provides response outside the BM, they might elect to use the baseline method to avoid imbalance charges for that response. The Baselining Methodology Document notes that baseline can also apply to supplier-registered Additional BMUs ￼ ￼, meaning even a supplier with say a portfolio of batteries could use the baseline to measure delivered DSR for settlement purposes.

In summary for frequency response and BM: the regulatory alignment ensures that whether a flexible action is taken via an aggregator in the BM or via a contract, baseline methods are available to correctly count the action and ensure the right party is credited/debited. The Grid Code and NGESO’s service requirements ensure the asset’s technical compliance (ability to follow setpoints, provide a defined response curve, etc.), while the BSC baseline and settlement rules ensure financial compliance (e.g., no double-counting of energy, proper allocation of volumes between supplier and VLP).

Other Balancing Services: Aside from the BM and primary frequency response, other services such as reserve (e.g., STOR – Short Term Operating Reserve, or the new Reserve Reform products), capacity market dispatches, and the Demand Flexibility Service (DFS) use baseline principles as well. The Demand Flexibility Service, run by NGESO in winter 2022/2023 and 2023/2024, paid consumers (via suppliers or VLPs) to reduce demand at peak times. It explicitly relied on a baseline methodology (NGESO adopted a baseline of the average of a number of recent similar days with some adjustments) to measure how much each customer reduced during a 1-hour event. Notably, VLPs were allowed to bring customers into DFS in 23/24, meaning an independent aggregator could coordinate peak reductions and get paid by ESO. The DFS baseline approach was similar in spirit to BSC’s but tailored for that program (e.g., using 3 out of the last 6 days highest usage, with day-of adjustments, etc.). P376’s framework could accommodate such services in the future more seamlessly through the BSC if DFS or similar become enduring.

From a compliance perspective, any asset providing balancing services must ensure accurate metering (down to half-hourly or finer granularity), communications for dispatch, and reliability. VLPs/VTPs have to post Credit Cover under the BSC to cover any potential imbalance they might cause (for example, if they fail to deliver and incur imbalance costs, Elexon holds credit to cover that) ￼ ￼. They also undergo a rigorous qualification process (administered by Elexon’s Performance Assurance Board) to demonstrate capability in metering, data submission, and processes ￼ ￼. This ensures that only serious, prepared parties can operate as VLPs or VTPs, maintaining system integrity.

Participation in DNO Flexibility Markets

In addition to national ESO services, CHP and BESS can provide local flexibility to DNOs/DSOs. These are typically programs where an asset reduces load or increases export in a specific area to help manage network constraints (for example, avoiding cable overloads or managing voltage in a rural grid). Historically, each DNO ran its own tenders (e.g., UK Power Networks’ “Flexibility Services”, Western Power Distribution’s “Flexible Power” platform, etc.), with varying requirements and baseline methodologies. Regulation in this area is moving toward standardization:
	•	Baseline Methodologies for DNO Services: The ENA Open Networks project, in collaboration with industry (including Elexon), published a Standardised Baselining Methodology report in 2025. Building on that, Elexon (expected to be the central Market Facilitator for these services) drafted a Flexibility Market Rule on Standard Baselining Methodologies ￼ ￼. This draft (v0.1 as of 2025) outlines minimum expectations for baselining in DNO markets. It defines several baseline techniques appropriate to different scenarios – for example: “Asset Capacity” baseline (assuming an asset’s full capacity as the baseline if it would otherwise be off, applicable to turn-down of generation like CHP), “Recent History” (like the aforementioned High-X-of-Y method for loads), “Nomination” (where an aggregator nominates a baseline with accuracy requirements), “Fixed” profiles, or simply “Zero” baseline (for assets that are normally off, any activation is incremental) ￼ ￼. The rule sets accuracy targets and requires DNOs and providers to use these methods consistently. All DNOs are expected to adopt the standard baseline rule by April 2026 (July 2026 for one DNO) ￼ ￼. This means a CHP or battery providing, say, a peak shaving service to a DNO in 2024 might currently face a bespoke baseline (some DNOs let aggregators nominate a baseline, others use standardized historical baselines), but by 2026 the approach will be harmonized.
	•	Coordination with BSC/ESO: One challenge is ensuring that if an asset provides a DNO service, it doesn’t accidentally get double-counted or conflict with national services. For instance, if a battery is used in a DNO constraint management event, its output may differ from what suppliers/ESO expect. If that same battery is part of a VLP’s BMU, the VLP should ideally flag that day as an “Event Day” (even though it wasn’t an ESO service, the VLP might want to exclude it from baseline history to avoid skewing future baselines). Currently, the BSC Event Day definition doesn’t explicitly list DNO events, but a VLP could potentially treat it as an outage or site exception if needed. Looking ahead, the FMAR system and closer integration mean that a single asset register will know if an asset is committed to a DNO service at a given time, so the ESO (and Elexon) can be aware. Ofgem’s policies emphasize visibility of distributed energy resources (there was a 2024 consultation on a common asset registration to improve visibility ￼). We expect that by late 2024, DNOs must inform NGESO of scheduled local actions (in fact, procedures exist for DNOs to flag if a resource is not available for national services due to local needs, to avoid clashes).

From a market participant perspective: a CHP or battery can stack revenues by participating in both DNO and ESO markets, but there are rules to prevent double-payment for the same action. For example, if a battery is providing voltage support for a DNO at a certain time, it might not be allowed to concurrently offer frequency response to ESO unless it has the capacity to do both independently. The Grid Code and Distribution Code require that any such operations do not jeopardize the network – meaning the asset must respect its export/import limits, ramp rates, etc., to not cause instability. Also, if a DNO calls a flexibility event, the supplier or VLP needs to make sure any expected energy change is accounted for. Typically, DNO services are relatively short events (1-2 hours) where the asset either reduces consumption or increases export. These are measured against a baseline determined by the agreed method. The DNO then pays the aggregator (or directly the asset owner) for the proven reduction (e.g., £/MWh of reduction). This doesn’t directly flow through the BSC, but it can indirectly affect settlement: if the asset reduced load, the supplier sees lower consumption than forecast – however, because this was a DNO service, it is outside the supplier’s control. Ofgem has acknowledged this and in some cases allowed that DNO procured flexibility should not penalize suppliers. In practice, currently suppliers bear the imbalance but can incorporate that expectation (since DNO events are pre-planned or dispatched ahead of time, they might notify suppliers). With the VLP/VTP framework, a more elegant solution is emerging: an aggregator could act as a VLP for the DNO event, thus any deviation volume could be picked up similar to a BM action and adjusted in settlement. Indeed, Ofgem’s longer-term Market Facilitator plan suggests that all flexibility actions, local or national, might be settled through a unified process (so that if an aggregator reduces demand for a DNO, it could be treated akin to a “trade” that is settled centrally, compensating the supplier appropriately). We are moving toward that model by 2025-2027.

In terms of codes: the Distribution Code (and DCUSA – Distribution Connection and Use of System Agreement) cover the arrangements at distribution level. The Distribution Code’s Engineering Recommendation G99 imposes technical requirements on CHP and storage (for example, a CHP connecting at 11kV must have certain protection settings, and a battery must be able to manage voltage steps, etc.). These ensure the asset can disconnect or curtail if needed for safety. When providing flexibility, the asset must still comply with those parameters (e.g., not exceed agreed export capacity). DCUSA has provisions on network access and charges – recently modified so that storage units aren’t double-charged usage fees (to encourage storage, Ofgem removed demand residual charges for storage charging, etc.). Also, Access and Forward-Looking Charges reforms (implemented around 2023) changed how DNOs signal local constraints via charges; however, DNOs concurrently use flexibility markets to manage constraints instead of just curtailment.

Regulatory alignment also involves transparency: DNOs are required to publish their flexibility needs and market results, and Ofgem monitors their progress. DNO license conditions now require them to act neutrally and facilitate markets. This means a CHP or battery owner can expect standardized contracts and fair opportunity across all DNOs. By late 2024, all DNOs have portals listing locations and times where flex is needed (often referred to as **DFES – Distribution Future Energy Scenarios – and “heat maps” for constraint areas). An aggregator or VTP can use this info to target assets in those areas. In fact, an asset could be providing frequency response and still offer to turn down for a DNO if, say, a local constraint coincides with low frequency event probability – careful coordination (potentially automated via platforms) will be key, which the new systems aim to handle.

In summary, CHP and BESS integration into DNO flexibility markets is supported by emerging rules that mirror those for ESO services: baseline methodologies to measure performance, registration processes (soon unified by Elexon’s FMAR), and oversight to ensure no adverse impacts on the wider system. Market participants should stay aware of DNO-specific requirements (e.g., some DNOs require telemetry or a minimum notice for dispatch, typically outlined in their contract terms) and ensure they do not commit the same capacity twice. The trend is that by aligning the local and national markets, a single asset can flexibly service both levels without double-counting and with proper compensation from each as applicable.

Compliance and Data Alignment for Market Participants

Under these frameworks, compliance and alignment are crucial for all parties:
	•	Virtual Lead/Trading Parties (Aggregators): VLPs/VTPs must adhere to BSC rules (such as accurate metering, data submissions via BSCP602/603 processes, maintaining credit cover, and undergoing regular performance assurance checks). They are responsible for notifying Elexon of their asset registrations (MSID pair allocations to BMUs), any changes, and event day declarations. For VTPs specifically, Wholesale Market Activity Notifications (WMAN) must be submitted to Elexon ahead of Gate Closure for any period they plan to trade flexibly ￼ ￼. This notification is effectively the signal that “we will be doing a trade that will cause a deviation from baseline in period X.” If they fail to submit this, the settlement system wouldn’t know to calculate a deviation volume, risking that the action is not accounted for (and thus the supplier might end up inadvertently out of balance). VTPs also continue to submit any BM delivered volumes like VLPs do. They must comply with market conduct rules – for example, not artificially inflating baseline by manipulating load on prior days, etc. (The baseline methodology and audit provisions help guard against this, since suspicious patterns could be flagged by Elexon’s performance assurance function.)
	•	Suppliers: Suppliers need to accommodate the new roles by updating their systems to handle adjustment notifications and compensation charges. Under P415, suppliers will receive information about deviation volumes and the mutualised compensation they’re owed or must pay (depending on the direction of the flexibility). While these costs are socialised, an individual supplier might see on their bill an adjustment related to “VLP deviation compensation” which they pay into or receive from the fund, ensuring neutrality ￼. Suppliers must not obstruct their customers from participating with VLPs (per competition principles), but they are entitled to be informed (the BSC’s processes ensure that when a VLP registers a customer’s MSID to its portfolio, the incumbent supplier is notified and has a window to dispute if, say, the customer isn’t actually contracted or if there’s an error). Compliance for suppliers also means updating customer terms – suppliers may include clauses about customers notifying them if they engage with a VLP, mainly so the supplier can adjust forecasting. However, with baseline methods, the supplier’s forecasting task is partially taken over by the central baseline which corrects after the fact.
	•	DNOs: DNOs must comply with neutral market facilitation – they can’t favor their own solutions over market offers. They must also coordinate with NGESO under the Grid Code OC2 (Outage and restriction planning) and other operability protocols to ensure that a local action doesn’t compromise transmission. For compliance, DNOs now have to report to Ofgem on their flexibility usage and follow the standardized baselining and dispatch processes (by 2026 as mentioned) ￼ ￼. If a DNO needs to override an aggregator’s action for safety (say a grid emergency), they have the authority under the Electricity Act to disconnect or constrain assets, but normally this is not exercised except in emergencies. Generally, DNOs will include in their agreements that assets must comply with their dispatch signals and may face penalties if they fail to deliver when called upon (though as of now, many DNO contracts simply don’t pay if no delivery, rather than punitive charges).
	•	Data and IT Systems: The integration of VTPs, CHP, and BESS relies heavily on data sharing and IT. Elexon’s systems (SVAA, Settlement Administration Agent) have been upgraded to handle more data granularity (e.g. asset-level data from P375) and new data flows (for baseline and deviation volumes). NGESO has developed APIs to allow VLPs to communicate electronically (so aggregators can send bids and receive dispatches digitally). The Elexon Portal and BMRS (Balancing Mechanism Reporting Service) provide public data on balancing actions, prices, system frequency, etc., which all market participants can use to inform their strategies. For instance, an aggregator might watch the BMRS for imbalance prices or frequency deviations as signals to activate flexibility (in a quasi-autonomous way if not instructed). Furthermore, Elexon publishes settlement data that parties can download or query – such as via the Elexon Data Portal or APIs. This includes historic meter volumes, imbalance prices, credit reports, and (for the parties themselves) their specific settlement reports (e.g., the SAA-I014 report shows all adjustments to a party’s account).

Leveraging BigQuery and Data Analytics: In the context of this question, BigQuery (a Google Cloud data warehouse) is assumed to host settlement or operational datasets. Participants can leverage such tools to monitor and optimize their activities:
	•	A VLP or VTP could stream their meter data and dispatch data into BigQuery, along with pulling data from the Elexon API (for example, pulling down half-hourly metered volumes, baseline values calculated by SVAA, and settlement results). By analyzing this data, they can verify that baseline calculations are accurate and spot any anomalies. For instance, they could query the data to see all days where a certain asset’s baseline was significantly off from actual, investigate why (perhaps an unreported event day), and improve future nominations or request methodology adjustments if needed. They might also analyze the performance of their portfolio: e.g., calculate delivered vs expected volumes across many events to demonstrate compliance or to identify which asset under-delivers. This can feed into compliance reports or improvements in control strategies.
	•	Suppliers and DNOs can also use data analytics. A supplier might use BigQuery to aggregate all its customers’ half-hourly data (from smart meters or from Elexon’s settlement files) and overlay which customers are involved in flexibility events. This helps in forecasting and also in validating the mutualised compensation: e.g., checking that the total deviation volumes attributed to VTPs for their portfolio match the actual consumption drop observed. DNOs might use data from the Elexon portal to see baseline vs actual for assets in their region (though not trivial, but if asset is in a VLP program, some info might be available via coordination).
	•	Regulatory Monitoring: Ofgem and Elexon will likely use advanced data analysis to monitor the success of these schemes. For example, they can analyze settlement data to see if baseline methods are over- or under-estimating on average (which could indicate gaming or systematic bias). The Baselining Methodology Document explicitly mentions facilitating monitoring of accuracy, by calculating those hypothetical in-day adjustments even when no event occurred ￼. Elexon could compile statistics on how often baseline error exceeded certain thresholds, etc. BigQuery or similar big-data tools could store years of half-hourly data for all flexible assets and help regulators identify trends (like specific technology types such as CHP vs battery – perhaps CHP might be harder to baseline due to heat-driven variability, which could justify introducing an improved method for CHP in the future).
	•	Optimization: From a market perspective, having large datasets accessible allows participants to optimize bidding and operation. For instance, a battery operator might use historic price data (available from BMRS and NGESO transparency data) in BigQuery to run simulations on revenue from different services. They can correlate that with their baseline availability – e.g., if a battery is often idle (baseline ~0) during certain hours with high price volatility, it’s a prime candidate to engage in wholesale trading via a VTP at those times. Or a CHP operator might use gas price and electricity price data to decide when to run the CHP for heat vs when to curtail electrical output to sell power back (i.e., if electricity price is low or if paid to turn down via a service).

In terms of official data sources, Elexon has made strides in providing open data. While not literally on BigQuery public datasets (as of 2024), the BMRS and new Elexon Data Insight Platform allow API queries for many data types ￼. Many analysts pull this data into their own databases (BigQuery, AWS, etc.) for analysis. The consistency in identifiers (MSIDs, BMU IDs, etc.) across systems ensures data from DNOs, Elexon, and NGESO can be linked. For example, an MSID (Metering System ID) is a key that could tie a site’s data from a DNO’s register to Elexon’s settlement volumes for that site.

Compliance Reporting: Each party has reporting duties – e.g., VLPs must provide periodic summaries of delivered volumes, and any issues (like events of under-delivery) might need explanation to Elexon or ultimately to Ofgem if significant. The capacity market (if a CHP or battery is in it) has its own metering and testing requirements too, with data often checked via Elexon settlement data for consistency. All these illustrate that data transparency and accuracy are fundamental to the regulatory alignment: the baseline approach and data flows create a single source of truth for “what would have happened” vs “what happened due to flexibility”, and all transactions hinge on that.

Next, we turn to specific worked examples illustrating how a CHP unit, a battery system, and a combination of both can participate under this framework, showing baseline calculations and engagement with VTP mechanisms.

Worked Examples

Example 1: Standalone CHP providing Balancing Services

Scenario: A factory has a 5 MW gas-fired Combined Heat and Power plant that normally runs to supply heat and power on weekdays. It usually exports about 2 MW to the grid in addition to self-serving the factory. The site is signed up with an aggregator (VLP) to provide balancing services. In this example, the aggregator bids the CHP into the Balancing Mechanism for an evening peak reduction service – essentially offering to turn down the CHP’s electrical output when the grid is tight. This could be used as a frequency-responsive action or simply as a peak shaving in the BM.

Normal Operation and Baseline: The CHP’s normal output varies with the factory’s heat demand but, say, on a typical weekday winter evening (5-6pm), it outputs 4 MW (of which 2 MW is used on-site, 2 MW exported). Over the past 60 days, there are many similar weekdays. The SVAA would identify those days and likely choose the top 10 days of output in that period for the baseline (since CHP might run a bit lower on some days if heat demand was less, the “high X of Y” picks the higher ones to avoid underestimation). Suppose on those 10 days at 5pm, the average export was 2.0 MW (and average on-site use 2.0 MW, making total generation ~4.0 MW). Thus, the Unadjusted Baseline for the export MSID at 5pm is 2.0 MWh, and similarly an implicit 2.0 MWh for the import MSID (though in this case import MSID actually measures net import, which might be zero or even negative during export – but baseline methodology would split the values into import/export as needed ￼). Let’s assume net site import is zero normally (the site is self-sufficient at that time), so baseline for import MSID is 0, export MSID is 2.0 MW.

Now, on the event day, NGESO accepts the VLP’s offer for the CHP to turn down at 5pm by 1.5 MW (meaning the CHP should drop from about 4 MW to 2.5 MW generation, reducing export from 2 MW down to 0.5 MW, effectively freeing up 1.5 MW for the grid). Before the event, from 2pm to 5pm, suppose the CHP was running slightly higher than usual (maybe the factory had high heat demand, so it was at full 5 MW for a while). In the In-Day Adjustment window (2–5pm, the 3 hours prior to dispatch), the SVAA sees that the actual output was, say, averaging 4.5 MW (export ~2.5 MW). The unadjusted baseline for that same period might have been 4.0 MW (export 2.0). This indicates the CHP was running hotter than normal that day. The SVAA would compute an In-Day Adjustment of +0.5 MW to apply starting 5pm ￼ ￼. However, since an ESO acceptance was issued for 5pm, the baseline will incorporate this in-day adjust. So the Adjusted Baseline for 5pm becomes 2.0 + 0.5 = 2.5 MW export (basically, had the CHP not been turned down, we estimate it would have exported 2.5 MW given the day’s trend).

Delivery and Settlement: At 5pm, the VLP receives the dispatch to reduce output by 1.5 MW. The CHP’s control system ramps down generation accordingly. The factory may need to draw a bit of extra power from the grid to make up for lost self-generation, but in this example, assume the factory can reduce some non-critical processes or has a heat buffer so it can afford the electrical drop. The CHP goes from 5 MW to 3.5 MW output over that interval. The meter reading for the export MSID from 5–5:30pm ends up being 0.5 MWh export (down from baseline 2.5), and the import MSID maybe shows 1 MWh import (because the factory drew 1 MW from the grid to compensate, whereas baseline import was 0). The net effect is the same 1.5 MW reduction in generation delivered. Elexon’s settlement will take the baseline (2.5 export vs 0 import) and actual (0.5 export vs 1 import) to calculate delivered volumes. For the export MSID: baseline 2.5 vs actual 0.5 means 2.0 MWh shortfall on export; for the import MSID: baseline 0 vs actual 1 means 1.0 MWh increase in import. However, in terms of the VLP’s delivered volume, it is the net change that matters – indeed the Baselining Methodology effectively splits positive and negative, and here the +1 MWh on import partially cancels the -2 MWh on export. The net delivered volume should equal 1.5 MWh delivered reduction (in practice, Elexon would allocate 1.5 to whichever meter accounts appropriately). The VLP would be credited for 1.5 MWh of balancing energy at the accepted offer price. The CHP owner might get paid through the VLP according to their contract (e.g., sharing that revenue). The supplier adjustment: The site’s supplier originally expected net zero import (and likely 0 export since they don’t count export in their energy). After the fact, the supplier sees 1 MWh of import they hadn’t expected (so they would be negatively imbalanced). But settlement fixes this: the supplier is allocated a +1.5 MWh adjustment (basically giving them energy as if the CHP hadn’t turned down), and the difference (1.5 MWh) is taken from the VLP. End result: supplier is as though CHP ran normally, VLP pays for the energy shortfall which NGESO effectively bought from them. This aligns with P376’s goal: the supplier’s BRP (Balance Responsible Party) position is not harmed by the VLP’s actions ￼ ￼.

Compliance: The VLP must ensure the CHP followed the dispatch; if it didn’t (say only reduced 1.0 MW), the baseline would show 0.5 MWh not delivered and the VLP could face a charge for non-delivery. The CHP’s telemetry might be audited to confirm it was physically capable (which it was, since CHPs can ramp down reasonably quickly, albeit with some thermal considerations). The baseline handled the verification. Later, the VLP will mark that day as an Event Day for that MSID Pair (delivery of a balancing service) so that these abnormal low values don’t enter future baseline calculations ￼.

This example demonstrates how a standalone CHP can engage in frequency and balancing services via a VLP. In fact, CHPs are often candidates for demand turn-down or “reserve” products: they effectively provide a service similar to a demand-side unit by reducing generation, which from the grid’s perspective is equivalent to increasing demand. The regulatory framework treats it the same as a load drop – baseline was expected generation, actual was less, difference is a service delivered.

Example 2: Standalone Battery participating via a VTP in Wholesale Trading

Scenario: Consider a 10 MW/20 MWh battery energy storage system connected at the distribution level. It is not associated with any consumer load (it’s a standalone grid-scale battery at a renewable farm). The battery operator teams up with an aggregator that is a VTP (so they have the VLP role and have qualified for the VTP extension under P415). They want to arbitrage in the wholesale market: charging when prices are low and discharging when prices are high, without being a licensed supplier. Before P415, this would require complex agreements with a supplier or the battery forgoing some opportunities; now the aggregator can do it directly.

Baseline Behavior: A battery’s baseline under normal circumstances can be tricky – if the battery is purely merchant, “normal” might be to do nothing (idle) or to follow some routine optimization. However, for baselining, if the battery is frequently used by the VTP, one might define baseline as what the battery would have done in absence of VTP’s trades. If the battery only operates when the VTP is trading, its baseline could effectively be “do nothing” (0 MW output, only minimal maintenance cycling). Let’s assume the battery typically stays idle unless instructed. Over the past weeks, on days it wasn’t providing any service, the import/export was near zero (aside from minor losses). So the baseline methodology, looking at historical days, would likely often pick a flat 0 MW as the expected profile (especially if we exclude days where it did trades as Event Days). That means on a given day, absent trading, the battery is expected not to charge or discharge. Baseline = 0 MW (for both import and export) for all periods, essentially.

VTP Wholesale Trade: Now, say on a certain day, the day-ahead market shows a price spike at lunchtime (13:00–13:30) due to low wind, and negative prices overnight. The VTP plans to arbitrage this by charging the battery at 3am (when prices are negative, effectively being paid to consume) and discharging at 13:00 (when prices are high). Because the VTP will execute this via the wholesale market, they must submit a Wholesale Market Activity Notification to Elexon for those Settlement Periods (one for the early morning charge action, one for the midday discharge) ￼. This tells Elexon’s systems to expect “deviation volumes.”

Let’s focus on the 13:00 discharge event. The VTP buys (or rather, sells) 10 MWh in the intra-day wholesale market for delivery in that half-hour, at, say, £200/MWh. This means the battery will inject 10 MWh to the grid during that half-hour (discharging at an average of 20 MW – since it’s 10 MW max, it might discharge 10 MW for the full half-hour to get 5 MWh, so actually 10 MWh might be 10 MW over an hour; to keep within capacity, maybe assume it discharges 10 MW for one hour from 12:30 to 13:30 across two periods). For simplicity, assume it’s 5 MWh in 12:30–13:00 and 5 MWh in 13:00–13:30.

Settlement with Baseline: The baseline for those periods, as said, is 0 MW (the battery would have done nothing). Actual metered data: at 12:30–13:00 the battery goes from 0 to 10 MW discharge, and similarly in the next period. So actual meter reading for those periods: Export MSID shows +5.0 MWh each half-hour; Import MSID 0 (since it’s discharging, not charging). Because a Wholesale Market Activity Notification was submitted, the baseline methodology will not apply any in-day adjustment that would muddy the waters ￼ ￼. (Had the battery been charging earlier, the baseline might catch a trend, but likely we exclude that or treat separate blocks.) The baseline remains 0. Therefore, the Deviation Volume for each period is simply 0 – (+5.0) = –5.0 MWh on the import/export difference (i.e., +5 MWh export that wasn’t expected, which is a negative deviation from the perspective of consumption, meaning generation delivered). Elexon will calculate a 5 MWh Deviation Volume attributable to the VTP for each period ￼ ￼. Since this is energy injected that the supplier of that site didn’t forecast (the site’s supplier, if any – actually if it’s purely exporting, it likely has a “zero” supplier because it’s generation-only, but under BSC every MSID has a supplier registered even if a dummy one), the settlement system will adjust so that the VTP is treated as selling 5 MWh and the supplier of that GSP is credited 5 MWh (or charged, depending on sign conventions). In practice, because this is a Secondary BMU, the energy goes into the VTP’s imbalance account. The VTP should have a corresponding trade so that they’re financially hedged – i.e., they sold 10 MWh at £200, and any imbalance from deviation volumes should settle at imbalance price, which ideally is close to that if system was short. If there’s a difference, the VTP might gain or lose a bit, but presumably they try to stick to their schedule.

Now, the money: the VTP gets paid £200/MWh * 10 MWh = £2000 from the market for that trade. They will have to buy back that energy in settlement at imbalance price or via contracts (since they effectively injected power). However, since they physically delivered it, their imbalance should be zero if done perfectly (sold 10 MWh, delivered 10 MWh, so no shortfall). The supplier of the site would see an unexpected 10 MWh export. Without adjustments, that supplier would get paid in imbalance at the price, but under P415, compensation flows handle this. Likely the supplier is charged the energy at a reference price and the VTP is credited (or vice versa) to ensure the supplier doesn’t profit from the VTP’s action. The design chosen was mutualisation: all suppliers collectively cover the cost of these deviations, as Ofgem determined this was better than charging individual suppliers (since individual suppliers can’t control it) ￼ ￼. So in effect, the funds the VTP receives from the market cover paying into the mutual pool for the energy, and the supplier gets cost recovery from that pool. The net result is the VTP’s profit is from the market spread (buy low, sell high), and suppliers collectively bear/benefit from any imbalance at a standard rate, not from the specific price spikes (so they’re neutral).

From a compliance perspective, the battery had to follow a schedule like a generator in the wholesale market. The VTP had to ensure the battery could sustain 10 MW discharge for the planned duration and not default on the trade. If the battery tripped or underperformed, the VTP would have been short (since they sold energy they didn’t deliver) and would pay imbalance charges — a strong incentive to be reliable. The VTP also had to submit the WMAN on time (prior to Gate Closure for those periods, which is one hour ahead in the current market) ￼. Missing that would mean the deviation might not be properly attributed, risking imbalances. The baseline made verification straightforward: since baseline was zero, the actual meter readings directly equal the provided service.

After the fact, the VTP and battery owner would analyze performance. They might use a BigQuery dataset containing all their trades and meter data to see how closely they followed their expected profile and whether any imbalance penalties occurred. If the battery had efficiency losses or if they over/under-delivered by a slight margin, that data would show up. They also will exclude this day’s operation from the baseline reference pool by marking it as an Event Day (due to “Virtual Trading”) ￼, because you wouldn’t want a day where the battery was very active to be considered “normal” – otherwise future baselines might assume the battery normally discharges at lunchtime every day, which is false.

This example highlights a key benefit of P415: a BESS can earn wholesale arbitrage revenues without being a generator with a license. The regulatory framework of VTP ensures the energy is accounted for (through deviation volumes and compensation) so that the integrity of settlements remains and suppliers aren’t left carrying risks they didn’t sign up for. The baseline methodology is crucial in attributing the battery’s actions to the VTP and not to the supplier’s imbalance. And from the Grid Code side, since this battery is 10 MW, it’s below the 50 MW threshold of direct Grid Code obligations, but it still must comply with G99, and if it were larger or directly connected to transmission, it would have to follow Grid Code dispatch rules too (in fact, NGESO might interact with it in BM if needed).

Example 3: Combined CHP + Battery in DNO Flexibility and Wholesale Markets

Scenario: A large commercial site (e.g., a hospital campus or university) has both a 3 MW CHP plant and a 2 MW/4 MWh battery on site. The CHP provides heat and baseload power, the battery is used for backup and peak shaving. The site’s import/export fluctuates – sometimes importing from the grid, sometimes exporting excess CHP power. The site is interested in providing DNO flexibility to the local network (the DNO has a constraint during winter evenings on the feeder) and also wants to monetize flexibility through an aggregator. We’ll consider a scenario where the site participates in a DNO’s local flexibility dispatch, coordinated by a VLP (who might also be a VTP for other markets).

Normal Profile: Early evening (5-7pm) is a peak time for the site’s electrical use (heat demand might also be up, causing the CHP to run near full output). Let’s say normally at 6pm the CHP is at 3 MW (its max), the battery might occasionally discharge 0.5 MW to shave peaks, and the site still imports 1 MW from the grid (meaning total site load 4.5 MW, 3 supplied by CHP, 0.5 by battery, 1 from grid). This is a bit complex since it involves two assets; for baseline purposes we consider the net site MSID pair unless using asset meters. Without asset-level baseline, the baseline is computed on the net import/export of the site. Suppose historically, similar winter weekdays show an average net import of 1 MW at 6pm (matching that pattern). So baseline import MSID = 1 MW, baseline export MSID = 0 (since net export is zero; the CHP’s generation is implicitly accounted as reduced import).

However, P375’s asset metering could be very useful here: the aggregator could register an AMSID for the battery and maybe one for the CHP (though CHP is already metered at boundary if exporting). The benefit would be to measure battery separately if the CHP confuses baseline. But let’s proceed with net baseline for simplicity.

DNO Flex Event: The DNO calls an event from 6pm to 7pm to alleviate a local constraint (say a substation is nearing capacity). The site’s location is suitable to help by reducing its net demand on the grid. The aggregator agrees with the DNO to deliver a 1.5 MW net reduction during that hour. To achieve this, the plan is: the CHP will increase output by 0.5 MW (if possible – maybe it normally was 3 MW, but perhaps it has some surge capacity or can overproduce if more fuel is burned and excess electricity dumped or exported), and the battery will discharge 1.0 MW (it has 2 MW capacity, but they may not need full). Additionally, the site may do minor demand turn-off to reduce 0.5 MW of load (like dimming lights, etc.), but let’s focus on CHP and battery actions. Net target: instead of importing 1 MW, they want to be exporting 1 MW (a swing of 2 MW reduction in draw – overshooting the 1.5 MW a bit in this narrative).

The DNO event is outside the national balancing (it’s not dispatched by NGESO). The aggregator as a Flexibility Service Provider executes it at 6pm.

Interaction with Baseline: From the BSC perspective, this looks like the site unexpectedly reduced its import/export. Unless flagged, the supplier would see a sudden change. Because this is not an ESO service, the BSC doesn’t automatically adjust anything – the supplier might simply be “long” (over-supplied) by that 1.5-2 MW if nothing is done, meaning the supplier’s imbalance would improve (they delivered more energy to grid than needed). In 2024, since VLPs cannot trade energy for DNO events in wholesale (unless they choose to also do a wholesale trade to cover it), this could be a gap. However, the supplier and aggregator likely have a side agreement or knowledge. Or the aggregator might register as a VTP and pre-emptively do a wholesale trade opposite to the DNO dispatch (for example, they could submit a WMAN and sell the 1.5 MW in the wholesale market for that hour, effectively monetizing it nationally while delivering it for the DNO – this ensures the supplier gets an adjustment via the P415 mechanism!). This kind of “stacked service” is complex but feasible: deliver DNO service (get paid by DNO), concurrently use the reduction as a deviation trade (get paid by wholesale/imbalance). The risk is if you promise same energy twice, but if done carefully it’s aligning one action to two value streams.

Let’s assume the aggregator does use the new VTP ability: They submit a Wholesale Market Activity Notification that they will deliver a 1.5 MW reduction for that hour (maybe through an internal trade at £0 since primary payment is DNO). This triggers the BSC deviation mechanism. Baseline for 6-7pm was import 1 MW; actual: at 6:30, the CHP is at 3.5 MW (0.5 above normal, possibly exporting 0.5 to grid), the battery is discharging 1 MW (which directly reduces grid import by 1), and some loads shed 0.5 MW. So net, instead of +1 MW import, the site might be –0.5 MW exporting (0.5 MW export). The baseline (import 1) vs actual (export 0.5) means a deviation of 1.5 MWh + 0.5 MWh = 2 MWh swing (1.5 reduction plus 0.5 extra export = 2 total change). If only 1.5 was committed, let’s assume they fine-tuned to exactly 1.5 reduction, but anyway. Elexon would calculate a Deviation Volume ~1.5 MWh (the difference attributable to VTP). The supplier’s position is adjusted accordingly via P415 compensation. The DNO separately measures the drop: they likely use their own baseline. Perhaps the DNO baseline was also ~1 MW import and now sees 0.5 MW export, so they see a 1.5 MW drop and pay the agreed rate (maybe £300/MWh for that hour or a availability + utilization combination).

Verification: The DNO will have the site’s meter data (either via the aggregator or directly if they installed monitoring) to confirm the flex delivered. The aggregator will compile a report to DNO showing, e.g., “Baseline 1 MW import, actual 0.5 MW export, thus 1.5 MW delivered, please pay us £450 (1.5 * £300).” Because the DNO’s baseline method might differ slightly, there could be a small discrepancy; the contract usually states how baseline is calculated (some use day-of adjustment, etc.). If standardized, it might even align with the BSC baseline to avoid confusion.

Asset Coordination: This example also showcases how multiple assets work together. The CHP on its own couldn’t increase output beyond 3 MW (if 3 is max, unless it had spare capacity), so maybe instead the CHP holds at 3 but normally at 6pm it would drop to 2.5 if heat demand falls? There are many possible nuances, but the aggregator’s control system will manage dispatch: perhaps it pre-charges the battery slightly before 6pm knowing it will discharge, and ensures the CHP keeps running to provide heat (the battery covers any electrical shortfall to the facility when the CHP output is diverted to export). The flexibility provided is the net effect.

Regulatory alignment issues: The aggregator had to use a bit of a trick by also acting as a VTP and using the wholesale notification to get the BSC to recognize the flex. If they hadn’t, the supplier of the site would simply see lower consumption and potentially be overbalanced (which might help them – ironically the supplier would gain because they sold energy that wasn’t consumed). DNOs currently typically require that any “Delivered Volumes” under their contract cannot also be sold to NGESO (no double payment). In this case, the aggregator didn’t sell to NGESO, they just adjusted wholesale position – arguably not double paid by NGESO, but they did avoid giving the supplier a free benefit. As markets align, this process will likely become official: the FMAR and Market Facilitator might auto-adjust supplier positions for DNO-called events too. Indeed, Ofgem’s Market Facilitation Blueprint envisions a system where local and national instructions all feed into one settlement adjustment engine ￼ ￼.

After-event: The aggregator will mark this day as an Event Day (due to Virtual Trading or classify under allowed categories) so it’s not in baseline history. They also provide DNO with documentation of performance. The DNO might have a cap on how often the CHP can be used for flex (maybe not, but if it’s an emissions thing perhaps). The site must remain within network limits: if exporting 0.5 MW was not normal, they must ensure reverse power flow is acceptable at their connection. Technically, the Grid Code/Distribution Code require that generating units not routinely export beyond agreed capacity – here it was likely fine and agreed.

This combined example shows how CHP and BESS together can achieve a bigger flex and how the regulatory framework is starting to accommodate stacking of services. It is complex but manageable with data and careful compliance: baseline methods, notifications, and coordinated market rules prevent conflicts.

Glossary of Terms and Acronyms

AMSID (Asset Metering System Identifier): An identifier for a metering system that measures a specific asset behind a site’s boundary point. Introduced with BSC P375, AMSIDs allow Asset Metering (measuring generation or consumption of a particular device, like a battery or EV charger, separately from the main meter). AMSIDs are paired as AMSID Pairs (import and export) similar to MSID Pairs.

AMVLP (Asset Metering Virtual Lead Party): A type of Virtual Lead Party that is qualified to use Asset Metering. An AMVLP can register AMSID Pairs and is allowed to provide balancing services using asset-level data ￼ ￼. Essentially a VLP with additional capability to meter behind-the-meter assets individually.

Baseline / Baselining: In this context, a Baseline is an estimate of the electricity consumption or generation profile that would have occurred absent any flexibility intervention. Baselining is the process of calculating that profile using a defined methodology and historical data ￼ ￼. The baseline is crucial for determining “Delivered Volumes” or “Deviation Volumes” for settlement.

Baselining Methodology Document: A BSC document describing the approved methods to calculate baselines for MSID Pairs/AMSID Pairs. Version 3.1 (effective Nov 2024) contains the details of method BL01 and provisions for adjustments, event days, etc. It was established under P376 and updated for P415.

BM (Balancing Mechanism): The near-real-time market operated by NGESO for balancing supply and demand. Licensed generators and suppliers (and now VLPs) submit offers to increase or decrease power, and NGESO accepts these as needed. Actions in the BM result in imbalance settlement and (for VLPs) use baselining to verify delivered energy.

BMU (Balancing Mechanism Unit): A unit of trade in the BM. Generators typically have one BMU per power station, suppliers one per region, etc. Secondary BMU refers to a BMU registered by a VLP consisting of one or more consumer sites (MSIDs) ￼ ￼. Additional BMU is a term for a supplier’s additional units (e.g., a supplier may create an “Additional BMU” to put some customers or generation into a separate unit for offering into balancing services).

BOA (Bid-Offer Acceptance): Instruction from NGESO in the Balancing Mechanism accepting a bid or offer from a BMU. It indicates the volume and time to increase/decrease generation or demand. For a VLP’s BMU, a BOA triggers the need to calculate delivered volume via baseline.

BSC (Balancing and Settlement Code): The industry code governing electricity balancing and settlement in GB. It is administered by Elexon and defines rules for imbalance settlement, metering, data, and roles like Supplier, Generator, and now VLP/VTP. Modifications like P376 and P415 are changes to the BSC.

BSCP (BSC Procedure): Detailed process documents under the BSC. For example, BSCP602 covers registering and managing MSID Pair allocations (including event day notifications) for VLPs, BSCP603 covers asset metering registration and data collection ￼ ￼. These are effectively “how-to” guides for parties to comply with code processes.

CHP (Combined Heat and Power): A generation technology that produces electricity and useful heat simultaneously. Often used on industrial or campus sites for efficiency. In flexibility terms, a CHP can either increase output (if it has spare capacity and fuel) or decrease output (diverting to boilers for heat or using stored heat) to provide grid services.

DNO (Distribution Network Operator): A company licensed to operate the local electricity distribution networks (e.g., UK Power Networks, Western Power Dist (National Grid Distribution), Northern Powergrid, etc.). Also evolving into DSO (Distribution System Operator) as they take on active system management like running flexibility markets. They ensure power is delivered from transmission to end-users safely and reliably.

DNO Flexibility Markets: Platforms/programs run by DNOs to procure demand or generation changes to manage local network issues. They usually involve contracts or auctions for certain zones where participants agree to reduce consumption or increase generation when called. Examples include load management during peak hours in constrained areas. Payments typically include availability (if you’re on standby) and utilization (for energy actually delivered).

DSR (Demand Side Response): Broad term for adjusting demand (or behind-the-meter generation) in response to signals, for economic or reliability reasons. VLP aggregators essentially deliver DSR, whether via turning down industrial processes, controlling EV charging, or modulating CHP/Batteries.

ESO (Electricity System Operator): In GB, National Grid ESO – responsible for balancing the grid and ensuring stability. Oversees frequency control, reserve, system voltage, etc. They interact with balancing services providers (including VLPs) and run markets like the Balancing Mechanism and ancillary service tenders.

FPN (Final Physical Notification): The expected generation or demand profile that participants submit to NGESO ahead of delivery (in half-hour increments). NGESO uses FPNs for scheduling. Under P376, the FPN is still submitted by VLPs for dispatch purposes, but settlement may use an alternate baseline for determining delivered volume ￼ ￼.

Frequency Response: Services wherein assets automatically or quickly adjust their power in response to frequency deviations to help stabilize the grid. It can be Primary, Secondary, High etc in legacy terms, or the new Dynamic Containment/Regulation/Moderation services. Providers must meet technical specs (e.g., respond within 1 second, sustain for 30 seconds or more, etc.). Both generation and demand/battery can provide this by either injecting power or reducing consumption.

Grid Code: The technical code that all users of the transmission system must comply with. It includes requirements for connecting plant (fault ride-through, frequency and voltage control capability, etc.) and operational procedures. Even distributed resources fall under Grid Code if they can affect the transmission system (and via Distribution Code for local). For example, Grid Code CC.6.1-6.3 cover general design criteria like frequency range tolerance and response capability for generators. Flexibility providers must ensure their assets meet any relevant parts of the Grid Code (directly or via their DNO’s implementation of those requirements).

MSID (Metering System Identifier): A unique number for a meter point (MPAN in England/Wales/Scotland, which the MSID typically maps to). For each site, there is usually an Import MSID (measuring consumption from grid) and possibly an Export MSID (if the site exports). A MSID Pair refers to the combination of an Import MSID and its corresponding Export MSID for the same site (or a “Secondary” MSID in case of certain virtual setups) ￼ ￼. VLPs work with MSID Pairs to capture the net site effect.

Mutualisation (Fund): In P415 context, the approach where costs of compensating suppliers for lost volume due to VLP trades are spread (“mutualised”) among all suppliers ￼. This avoids a situation where only the supplier of a specific flexing customer bears the whole cost, which could deter suppliers from allowing participation. Instead, all suppliers collectively fund it (assuming overall system benefit and competition justify it).

P376: BSC Modification “Utilising a Baselining Methodology to Set Physical Notifications for Settlement of Applicable Balancing Services.” Approved by Ofgem in 2021 and implemented Feb 2023. It allows baselines to replace FPNs in settlement for certain BMUs, improving accuracy of settling balancing services ￼ ￼. It introduced the Baselining Methodology Document and associated processes.

P415: BSC Modification “Facilitating Access to Wholesale Markets for Flexibility Dispatched by VLPs.” Approved in 2023, effective Nov 2024. It enables VLPs to trade in wholesale by establishing the Virtual Trading Party role and associated “Deviation Volume” settlement and compensation arrangements ￼ ￼. A landmark change opening the wholesale market to independent aggregators without a supply license ￼.

Settlement Period: The half-hour time interval used in electricity trading and settlement in GB. 48 per day (or 50 on clock change days). All energy volumes and prices are accounted per Settlement Period.

SVAA (Supplier Volume Allocation Agent): The system agent under the BSC that processes metering data from the distribution level (Supplier Volume Allocation) and calculates volumes for settlement. The SVAA is responsible for executing the baseline calculations for VLP/VTP arrangements ￼ ￼. It receives metered data from Data Collectors/Aggregators, applies the baseline methodology, and outputs baseline values and delivered volumes.

Secondary BMU: A BM unit registered by a VLP consisting of one or more SVA Metering Systems (customers or assets) ￼. Called “secondary” to distinguish from primary BMUs of suppliers/generators. They usually have an ID like “_V” in systems. Secondary BMUs allow aggregated or individual flexible sites to participate in balancing as a unit.

Supplier: In BSC terms, a party responsible for the energy taken by end consumers at sites. They buy energy from generators or markets and sell to consumers, and are the default party balancing those volumes. Under these new frameworks, suppliers’ roles are largely unchanged but their customers’ flexibility can now be tapped by others with appropriate settlement adjustments. Suppliers still handle billing, customer relationships, and remain obligated to maintain compliance with supply license conditions (including supporting smart metering, offering demand response programs, etc.).

TNUoS/DNUoS: Transmission/Distribution Network Use of System charges – mentioned here only to note that in recent years these charges for storage were clarified (storage pays reduced or no demand UoS charges when charging, to prevent double charging since they later export that energy). Not a direct part of flexibility markets, but relevant for BESS economics and regulatory treatment (Ofgem recognized storage as a distinct subset of generation).

VLP (Virtual Lead Party): A class of BSC Party created to enable independent aggregators to provide balancing services without being a supplier ￼. They “lead” Secondary BM Units composed of consumption/generation sites they don’t own. VLPs have lighter obligations than suppliers (no need for a supply license, exempt from some charges like capacity market supplier charges, etc.), but can only participate in specific markets (BM, ancillary services, etc. – until P415, no wholesale). They must qualify and follow all data/settlement rules.

VTP (Virtual Trading Party): The new BSC role that an existing VLP/AMVLP can take on to access wholesale markets ￼ ￼. A VTP is essentially a VLP with additional responsibilities: all their involved assets must be baselined and any trades must be declared via WMAN. The VTP role allows trading of Deviation Volumes – differences between baseline and actual due to the VTP’s action – as a product on the wholesale market. The role became active from November 2024 ￼.

Wholesale Market Activity Notification (WMAN): A notification submitted by a VTP to Elexon indicating that it will be active in the wholesale market in a given Settlement Period ￼ ￼. It serves to alert the settlement system that any deviation of that BMU’s volume from baseline in that period is intentional and should be treated as a traded volume (Deviation Volume). It’s analogous to submitting a trade schedule. Must be submitted before Gate Closure for the period.

Worked Example Terms:
	•	Delivered Volume: The amount of energy delivered (or not delivered) in response to an accepted instruction (e.g., a balancing service). Calculated as baseline minus actual for a reduction service (or actual minus baseline for an increase service). In P415 context, “Deviation Volume” is essentially the delivered volume for an uninstructed trade.
	•	Event Day: A day excluded from baseline calculations due to unusual activity (balancing service dispatch, etc.) ￼ ￼.
	•	In-Day Adjustment: A correction applied to the daily baseline to account for conditions on the day (computed from a pre-event window) ￼ ￼.
	•	High X of Y (Baseline selection): A common baseline approach where out of Y historical days, the X days with the highest values (in the relevant period) are averaged to form the baseline. Ensures baseline is not undershooting normal peak usage. BL01 uses 4 of last 5 non-weekend days for non-working day baseline, and up to 10 of last 10 same-type days for working day (which is effectively all if available, but weighted to higher ones if some days were lower, per defined rules) ￼.
	•	Deviation Volume: Specifically under P415, the difference between forecast (baseline) and actual consumption/generation attributed to a VTP’s action ￼. It’s a new volume that is settled to facilitate VLP wholesale trades.

By understanding these terms and the examples above, stakeholders can better navigate the GB regulatory environment as it stood in late 2024 – an environment increasingly conducive to flexible, aggregated energy resources like CHP and battery storage, backed by robust methodologies and code modifications that ensure fairness and accountability across the system.

Sources:
	•	Elexon, Baselining Methodology Document v3.0, effective 07 Nov 2024 (BSC Section S Annex) ￼ ￼
	•	Ofgem, Approval of BSC Modification P376 (Baselining for Settlement) – Decision Letter, 06 Aug 2021 ￼ ￼
	•	Ofgem, Decision on BSC Modification P415: “Facilitating access to wholesale markets for flexibility” – Decision Letter, 06 Oct 2023 ￼ ￼
	•	GridBeyond (industry insights), “Navigating P415: opportunities and challenges”, Dec 2023 – summary of P415 impacts ￼ ￼
	•	Enegen (industry guide), “Virtual Lead Party (VLP) role explanation” – details on VLP and baselining options ￼ ￼
	•	Enegen, “Virtual Trading Party (VTP) role explanation” – details on VTP obligations and deviation volumes ￼ ￼
	•	Elexon/ENA, Draft Flexibility Market Standard Baselining Methodologies v0.1, 2025 – outlining baseline standards for DNO services ￼ ￼
	•	Ofgem Press Release, “Ofgem fast-tracks new energy flexibility tool…”, 07 Mar 2025 – on Elexon’s role in asset registration and market alignment ￼ ￼.Below is a clear, GB-specific breakdown of VTP revenue streams and all battery (BESS) revenues, mapped to regulation, market access, and settlement. This is written so it can drop straight into your report or be turned into a standalone MD section if you want.

⸻

VTP Revenue and Battery (BESS) Revenue Streams in Great Britain

1. What a VTP Can Earn Revenue From (GB, post-P415)

A Virtual Trading Party (VTP) is not itself a technology — it is a market access role.
Revenue flows depend on what assets the VTP controls, typically batteries, CHP, demand, or hybrids.

High-level VTP revenue categories ategory
Revenue Type
Who Pays
Regulatory Basis
Wholesale trading
Energy arbitrage
Power exchanges / counterparties
BSC P415
Balancing Mechanism
BOA energy payments
NGESO
BSC + Grid Code
Frequency response
Availability + performance
NGESO
Ancillary service contracts
Reserve services
Availability + utilisation
NGESO
ESO procurement
DNO flexibility
Utilisation + availability
DNOs
DSO frameworks
Capacity Market
£/kW/year
NGESO
Capacity Market Rules
Avoided imbalance
Reduced exposure
Imbalance prices
BSC settlement
Portfolio optimisation
Cross-market stacking
Indirect
Allowed, with restrictions
 A VTP may access all of the above, provided:
	•	Assets are baselined
	•	Wholesale trades are declared (WMAN)
	•	No double-counting of the same MW occurs

⸻

2. Battery (BESS) Revenue Stack – Great Britain (2024–2025)

A. Wholesale Market Revenues (via VTP)

Energy arbitrage
	•	Buy electricity at low prices
	•	Sell at high prices
	•	Captured through:
	•	Day-Ahead Market
	•	Intraday auctions
	•	Continuous intraday trading

Settlement mechanism
	•	BESS exports/imports deviate from baseline
	•	Deviation Volumes settled under P415
	•	Supplier compensated via mutualisation
	•	VTP captures price spread

Typical GB arbitrage characteristics
	•	Highly volatile intraday prices
	•	Strong correlation with wind forecast error
	•	Increasing cannibalisation → optimisation critical

⚠️ Without VTP status, standalone batteries cannot trade wholesale directly unless licensed.

⸻

B. Balancing Mechanism (BM) Revenues

BESS can earn energy payments via:
	•	Offers (increase generation / reduce demand)
	•	Bids (reduce generation / increase demand)

Key points
	•	Paid at accepted BM prices (£/MWh)
	•	Settlement uses baselining (P376)
	•	High price volatility → major upside in scarcity events

Why batteries dominate BM
	•	Fast ramp (milliseconds)
	•	Predictable response
	•	Zero fuel risk

⸻

C. Frequency Response Revenues (Core BESS Income)

1. Dynamic Containment (DC)
	•	Fast response (<1s)
	•	High availability payments
	•	Battery-dominated market

2. Dynamic Regulation (DR)
	•	Continuous modulation
	•	Lower price, higher utilisation

3. Dynamic Moderation (DM)
	•	Less lucrative, more situational

Revenue structure
	•	£/MW/hour availability
	•	Performance-adjusted
	•	Separate energy settlement if applicable

Regulatory note
	•	Contracted outside BSC
	•	Metering and verification still rely on baseline concepts
	•	Assets may not double-count MW with BM in same period

⸻

D. Reserve Services (ESO)

Includes:
	•	STOR (legacy)
	•	New reserve reform products

Revenue
	•	Availability (£/MW)
	•	Utilisation (£/MWh when called)

BESS advantage:
	•	Predictable delivery
	•	Lower performance risk than thermal plant

⸻

E. Capacity Market (CM)

What it pays
	•	£/kW/year for derated capacity

Key features
	•	Long-term revenue certainty
	•	Requires stress event delivery
	•	Performance penalties apply

Typical BESS role
	•	Revenue stabiliser
	•	Lower risk, lower upside
	•	Often stacked with frequency response

⸻

F. DNO Flexibility Revenues

Local network constraint management.

Payment types
	•	Availability (£/MW/year)
	•	Utilisation (£/MWh)

Key GB features
	•	Location-specific
	•	Often winter evening peaks
	•	Lower prices than ESO markets but low competition

Regulatory evolution
	•	Standardised baselining coming (Elexon / ENA)
	•	FMAR will simplify multi-market participation
	•	Increasing integration with ESO services

⸻

G. Imbalance Value Capture (Indirect)

BESS can:
	•	Reduce supplier imbalance exposure
	•	Exploit imbalance price spreads
	•	Hedge portfolio positions

Via VTP:
	•	Imbalance impacts correctly assigned
	•	No accidental supplier windfalls
	•	Portfolio-level optimisation possible

⸻

3. CHP + BESS Combined Revenue Stack

A hybrid site (CHP + battery) is structurally superior.

Why? CHP
Battery
Heat-led, slower
Fast, precise
Baseload generation
Short-duration flexibility
Good for turn-down
Good for turn-up/down
Below is a clear, GB-specific breakdown of VTP revenue streams and all battery (BESS) revenues, mapped to regulation, market access, and settlement. This is written so it can drop straight into your report or be turned into a standalone MD section if you want.

⸻

VTP Revenue and Battery (BESS) Revenue Streams in Great Britain

1. What a VTP Can Earn Revenue From (GB, post-P415)

A Virtual Trading Party (VTP) is not itself a technology — it is a market access role.
Revenue flows depend on what assets the VTP controls, typically batteries, CHP, demand, or hybrids.

High-level VTP revenue categories

Category	Revenue Type	Who Pays	Regulatory Basis
Wholesale trading	Energy arbitrage	Power exchanges / counterparties	BSC P415
Balancing Mechanism	BOA energy payments	NGESO	BSC + Grid Code
Frequency response	Availability + performance	NGESO	Ancillary service contracts
Reserve services	Availability + utilisation	NGESO	ESO procurement
DNO flexibility	Utilisation + availability	DNOs	DSO frameworks
Capacity Market	£/kW/year	NGESO	Capacity Market Rules
Avoided imbalance	Reduced exposure	Imbalance prices	BSC settlement
Portfolio optimisation	Cross-market stacking	Indirect	Allowed, with restrictions

A VTP may access all of the above, provided:
	•	Assets are baselined
	•	Wholesale trades are declared (WMAN)
	•	No double-counting of the same MW occurs

⸻

2. Battery (BESS) Revenue Stack – Great Britain (2024–2025)

A. Wholesale Market Revenues (via VTP)

Energy arbitrage
	•	Buy electricity at low prices
	•	Sell at high prices
	•	Captured through:
	•	Day-Ahead Market
	•	Intraday auctions
	•	Continuous intraday trading

Settlement mechanism
	•	BESS exports/imports deviate from baseline
	•	Deviation Volumes settled under P415
	•	Supplier compensated via mutualisation
	•	VTP captures price spread

Typical GB arbitrage characteristics
	•	Highly volatile intraday prices
	•	Strong correlation with wind forecast error
	•	Increasing cannibalisation → optimisation critical

⚠️ Without VTP status, standalone batteries cannot trade wholesale directly unless licensed.

⸻

B. Balancing Mechanism (BM) Revenues

BESS can earn energy payments via:
	•	Offers (increase generation / reduce demand)
	•	Bids (reduce generation / increase demand)

Key points
	•	Paid at accepted BM prices (£/MWh)
	•	Settlement uses baselining (P376)
	•	High price volatility → major upside in scarcity events

Why batteries dominate BM
	•	Fast ramp (milliseconds)
	•	Predictable response
	•	Zero fuel risk

⸻

C. Frequency Response Revenues (Core BESS Income)

1. Dynamic Containment (DC)
	•	Fast response (<1s)
	•	High availability payments
	•	Battery-dominated market

2. Dynamic Regulation (DR)
	•	Continuous modulation
	•	Lower price, higher utilisation

3. Dynamic Moderation (DM)
	•	Less lucrative, more situational

Revenue structure
	•	£/MW/hour availability
	•	Performance-adjusted
	•	Separate energy settlement if applicable

Regulatory note
	•	Contracted outside BSC
	•	Metering and verification still rely on baseline concepts
	•	Assets may not double-count MW with BM in same period

⸻

D. Reserve Services (ESO)

Includes:
	•	STOR (legacy)
	•	New reserve reform products

Revenue
	•	Availability (£/MW)
	•	Utilisation (£/MWh when called)

BESS advantage:
	•	Predictable delivery
	•	Lower performance risk than thermal plant

⸻

E. Capacity Market (CM)

What it pays
	•	£/kW/year for derated capacity

Key features
	•	Long-term revenue certainty
	•	Requires stress event delivery
	•	Performance penalties apply

Typical BESS role
	•	Revenue stabiliser
	•	Lower risk, lower upside
	•	Often stacked with frequency response

⸻

F. DNO Flexibility Revenues

Local network constraint management.

Payment types
	•	Availability (£/MW/year)
	•	Utilisation (£/MWh)

Key GB features
	•	Location-specific
	•	Often winter evening peaks
	•	Lower prices than ESO markets but low competition

Regulatory evolution
	•	Standardised baselining coming (Elexon / ENA)
	•	FMAR will simplify multi-market participation
	•	Increasing integration with ESO services

⸻

G. Imbalance Value Capture (Indirect)

BESS can:
	•	Reduce supplier imbalance exposure
	•	Exploit imbalance price spreads
	•	Hedge portfolio positions

Via VTP:
	•	Imbalance impacts correctly assigned
	•	No accidental supplier windfalls
	•	Portfolio-level optimisation possible

⸻

3. CHP + BESS Combined Revenue Stack

A hybrid site (CHP + battery) is structurally superior.

Why?

CHP	Battery
Heat-led, slower	Fast, precise
Baseload generation	Short-duration flexibility
Good for turn-down	Good for turn-up/down

Combined revenue opportunities
	1.	CHP
	•	Turn-down in BM
	•	DNO demand reduction
	•	Capacity Market
	2.	Battery
	•	Frequency response
	•	Arbitrage
	•	BM rapid response
	3.	Together
	•	CHP provides energy
	•	Battery provides speed
	•	Enables compliance with tighter service specs

Example
	•	Battery handles frequency deviations
	•	CHP provides sustained output change
	•	Site exports net power while maintaining heat

This combination:
	•	Improves baselining accuracy
	•	Reduces non-delivery risk
	•	Unlocks higher-value services

⸻

4. Revenue Risk & Constraints (Important)

Non-stackable constraints
	•	Same MW cannot be sold twice in same period
	•	ESO > DNO priority typically applies
	•	Contract rules override optimisation logic

Baselining risk
	•	Poor Event Day management → baseline drift
	•	CHP variability increases baseline error
	•	Asset-level metering (AMSID) strongly recommended

Market cannibalisation
	•	Frequency response prices declining
	•	Arbitrage margins tightening
	•	Portfolio optimisation increasingly critical

⸻

5. Typical GB BESS Revenue Mix (Indicative)

Revenue Stream	Share
Frequency response	40–60%
BM actions	10–25%
Wholesale arbitrage	10–30%
Capacity Market	5–15%
DNO flexibility	0–10%

Exact mix depends on location, duration, cycling limits, and control sophistication.

⸻

6. Strategic Value of VTP Status

Without VTP:
	•	No wholesale access
	•	Supplier dependency
	•	Revenue leakage

With VTP:
	•	Full market access
	•	Correct settlement
	•	Portfolio-level optimisation
	•	Enables hybrid assets (CHP + BESS) to reach full value

In GB, VTP is now the gateway role for advanced battery monetisation.

⸻

If you want next:
	•	📊 A numeric worked revenue example (£/MW/year)
	•	🧮 A stacking optimisation model (rules + constraints)
	•	📄 This section merged into your existing MD file
	•	🇬🇧 A regulatory comparison vs EU / US

Just say which one. Typical GB BESS Revenue Mix (Indicative)evenue Stream
Share
Frequency response
40–60%
BM actions
10–25%
Wholesale arbitrage
10–30%
Capacity Market
5–15%
DNO flexibility
0–10%
. Strategic Value of VTP Status

Without VTP:
	•	No wholesale access
	•	Supplier dependency
	•	Revenue leakage

With VTP:
	•	Full market access
	•	Correct settlement
	•	Portfolio-level optimisation
	•	Enables hybrid assets (CHP + BESS) to reach full value

In GB, VTP is now the gateway role for advanced battery monetisation.

⸻

If you want next:
	•	📊 A numeric worked revenue example (£/MW/year)
	•	🧮 A stacking optimisation model (rules + constraints)
	•	📄 This section merged into your existing MD file
	•	🇬🇧 A regulatory comparison vs EU / US

Just say which one. This is a really important question, because it sits right at the boundary between NESO dispatch and Elexon settlement, and it’s often misunderstood.

I’ll answer it cleanly, step-by-step, and tie it explicitly to Offers accepted, baselining, and BLP/VLP identification.

⸻

How are BLPs (Baseline / Balancing Lead Parties) Identified for Accepted Offers?

Short answer

NESO identifies the BM Unit and Lead Party for an accepted Offer.
Elexon identifies the Baselined Lead Party (BLP/VLP/VTP) for settlement.

They play different roles, using different systems, but they reconcile to the same BM Unit.

⸻

1. Who Does What – NESO vs Elexon (Clear Separation)

Function	Organisation	System
Dispatch (Offer acceptance)	NESO	BM systems (BMU, BOA)
Physical control	NESO	Grid Code / dispatch
Baseline calculation	Elexon	SVAA
Delivered volume calculation	Elexon	Settlement
Allocation to parties	Elexon	BSC settlement

So:
	•	NESO never identifies a “BLP”
	•	Elexon never accepts Offers

⸻

2. What NESO Identifies When an Offer Is Accepted

When NESO accepts an Offer, it identifies:

✅ 1. The BM Unit (BMU)
	•	Primary BMU (generator/supplier)
	•	Secondary BMU (VLP / aggregated unit)

✅ 2. The Lead Party for that BMU
	•	Generator
	•	Supplier
	•	Virtual Lead Party (VLP)

This is done entirely under:
	•	Grid Code
	•	BM participation rules

At this point:
	•	NESO does not care about baselining
	•	NESO does not know about MSIDs, AMSIDs, or baselined entities

NESO instruction =

“BMU X, owned by Lead Party Y, deliver Z MW”

⸻

3. How Elexon Identifies the Baselined Lead Party (BLP)

Once the Offer has been accepted, the Daily Activations Report is sent from NESO → Elexon.

From this point onward, Elexon takes over.

Step 1: Identify the BM Unit

Elexon receives:
	•	BMU ID
	•	Settlement Period(s)
	•	Accepted volume

⸻

Step 2: Identify the Lead Party in BSC terms

From BSC registration:
	•	That BMU is registered to:
	•	A Supplier
	•	A Generator
	•	A Virtual Lead Party (VLP)

If it is a Secondary BMU, it is always a VLP.

⸻

Step 3: Identify Baselined Entities

Using BSCP602 registrations, Elexon (via SVAA) determines:
	•	Which MSID Pairs / AMSID Pairs belong to that BMU
	•	Which of those are:
	•	Baselined
	•	Non-baselined
	•	Inactive

This is where the Baselined Lead Party (BLP) concept arises.

⚠️ “BLP” is not a formal BSC role — it is shorthand for
“the Lead Party responsible for baselined entities in settlement”

⸻

4. How This Works for Accepted Offers (End-to-End)

Timeline for an Offer Acceptance

1️⃣ Before Gate Closure
	•	VLP submits Physical Notifications (for dispatch)
	•	Baseline setup already exists in Elexon systems

2️⃣ NESO accepts an Offer
	•	Identifies BMU + Lead Party
	•	Issues BOA
	•	Sends activation data to Elexon

3️⃣ Elexon settlement process
Elexon (SVAA + SAA):
	1.	Sees BMU had an Acceptance
	2.	Identifies Lead Party = VLP
	3.	Identifies Baselined Entities within BMU
	4.	Calculates baseline values (BL01)
	5.	Calculates Delivered Volumes:

Delivered Volume = Actual Metered – Baseline


	6.	Attributes Delivered Volume to:
	•	The VLP (financial credit)
	•	Adjusts Supplier imbalance to neutralise effect

At no point does NESO identify or care about baselining.

⸻

5. What About VTPs and Wholesale Trades?

Exactly the same logic — just a different trigger.

Instead of:
	•	NESO BOA

You have:
	•	Wholesale Market Activity Notification (WMAN)

Process:
	1.	VTP submits WMAN
	2.	Elexon flags the Settlement Period as “VTP active”
	3.	SVAA calculates baselines
	4.	Deviation Volumes calculated
	5.	Supplier compensated
	6.	VTP settles wholesale trade

Again:
	•	NESO is not involved
	•	Elexon identifies the VTP as the responsible party

⸻

6. Key Regulatory Anchors (So You Can Cite This)

In the BSC / Baselining Methodology
	•	Baselining applies when:
	•	BM Acceptance or
	•	Wholesale Market Activity Notification exists
	•	SVAA calculates baselines after activations
	•	Lead Party responsibility is determined from BSC registration, not ESO dispatch

Critical sentence (paraphrased from Baselining Methodology Doc):

“SVAA will calculate Baseline Values for Baselined Entities where the BM Unit received an Acceptance from the NETSO or a Wholesale Market Activity Notification from a VTP.”

This tells you:
	•	Trigger = NESO or VTP
	•	Identification & calculation = SVAA (Elexon)

⸻

7. One-Line Answer You Can Use Externally

If you need a clean regulatory sentence:

NESO identifies the BM Unit and Lead Party for dispatch, but Elexon identifies the baselined Lead Party and allocates delivered volumes for settlement using BSC registrations and baselining methodologies.

⸻

If you want, next I can:
	•	Draw a sequence diagram (NESO → Elexon → Supplier)
	•	Explain how disputes are handled if baselines are challenged
	•	Show how this works for CHP + BESS specifically
	•	Map this to Grid Code vs BSC legal responsibilities

Just say the word. . Who Does What – NESO vs Elexon (Clear Separation) Function
Organisation
System
Dispatch (Offer acceptance)
NESO
BM systems (BMU, BOA)
Physical control
NESO
Grid Code / dispatch
Baseline calculation
Elexon
SVAA
Delivered volume calculation
Elexon
Settlement
Allocation to parties
Elexon
BSC settlement
What NESO Identifies When an Offer Is Accepted

When NESO accepts an Offer, it identifies:

✅ 1. The BM Unit (BMU)
	•	Primary BMU (generator/supplier)
	•	Secondary BMU (VLP / aggregated unit)

✅ 2. The Lead Party for that BMU
	•	Generator
	•	Supplier
	•	Virtual Lead Party (VLP)

This is done entirely under:
	•	Grid Code
	•	BM participation rules

At this point:
	•	NESO does not care about baselining
	•	NESO does not know about MSIDs, AMSIDs, or baselined entities

NESO instruction =

“BMU X, owned by Lead Party Y, deliver Z MW”

⸻

3. How Elexon Identifies the Baselined Lead Party (BLP)

Once the Offer has been accepted, the Daily Activations Report is sent from NESO → Elexon.

From this point onward, Elexon takes over.

Step 1: Identify the BM Unit

Elexon receives:
	•	BMU ID
	•	Settlement Period(s)
	•	Accepted volume

⸻

Step 2: Identify the Lead Party in BSC terms

From BSC registration:
	•	That BMU is registered to:
	•	A Supplier
	•	A Generator
	•	A Virtual Lead Party (VLP)

If it is a Secondary BMU, it is always a VLP.

⸻

Step 3: Identify Baselined Entities

Using BSCP602 registrations, Elexon (via SVAA) determines:
	•	Which MSID Pairs / AMSID Pairs belong to that BMU
	•	Which of those are:
	•	Baselined
	•	Non-baselined
	•	Inactive

This is where the Baselined Lead Party (BLP) concept arises.

⚠️ “BLP” is not a formal BSC role — it is shorthand for
“the Lead Party responsible for baselined entities in settlement”

⸻

4. How This Works for Accepted Offers (End-to-End)

Timeline for an Offer Acceptance

1️⃣ Before Gate Closure
	•	VLP submits Physical Notifications (for dispatch)
	•	Baseline setup already exists in Elexon systems

2️⃣ NESO accepts an Offer
	•	Identifies BMU + Lead Party
	•	Issues BOA
	•	Sends activation data to Elexon

3️⃣ Elexon settlement process
Elexon (SVAA + SAA):
	1.	Sees BMU had an Acceptance
	2.	Identifies Lead Party = VLP
	3.	Identifies Baselined Entities within BMU
	4.	Calculates baseline values (BL01)
	5.	Calculates Delivered Volumes: Delivered Volume = Actual Metered – Baseline
	6.	Attributes Delivered Volume to:
	•	The VLP (financial credit)
	•	Adjusts Supplier imbalance to neutralise effect

At no point does NESO identify or care about baselining.

⸻

5. What About VTPs and Wholesale Trades?

Exactly the same logic — just a different trigger.

Instead of:
	•	NESO BOA

You have:
	•	Wholesale Market Activity Notification (WMAN)

Process:
	1.	VTP submits WMAN
	2.	Elexon flags the Settlement Period as “VTP active”
	3.	SVAA calculates baselines
	4.	Deviation Volumes calculated
	5.	Supplier compensated
	6.	VTP settles wholesale trade

Again:
	•	NESO is not involved
	•	Elexon identifies the VTP as the responsible party

⸻

6. Key Regulatory Anchors (So You Can Cite This)

In the BSC / Baselining Methodology
	•	Baselining applies when:
	•	BM Acceptance or
	•	Wholesale Market Activity Notification exists
	•	SVAA calculates baselines after activations
	•	Lead Party responsibility is determined from BSC registration, not ESO dispatch

Critical sentence (paraphrased from Baselining Methodology Doc):

“SVAA will calculate Baseline Values for Baselined Entities where the BM Unit received an Acceptance from the NETSO or a Wholesale Market Activity Notification from a VTP.”

This tells you:
	•	Trigger = NESO or VTP
	•	Identification & calculation = SVAA (Elexon)

⸻

7. One-Line Answer You Can Use Externally

If you need a clean regulatory sentence:

NESO identifies the BM Unit and Lead Party for dispatch, but Elexon identifies the baselined Lead Party and allocates delivered volumes for settlement using BSC registrations and baselining methodologies.

⸻

If you want, next I can:
	•	Draw a sequence diagram (NESO → Elexon → Supplier)
	•	Explain how disputes are handled if baselines are challenged
	•	Show how this works for CHP + BESS specifically
	•	Map this to Grid Code vs BSC legal responsibilities

Just say the word. Below is a concise but complete summary document, written in a regulatory / briefing-note style, pulling together:
	•	VTP revenues
	•	BESS revenue stacking in GB
	•	CHP + BESS hybrid value
	•	How NESO vs Elexon identify parties for Offer acceptance and settlement
	•	Where baselining and “BLP” responsibility actually sits

You can paste this directly into a report or save it as summary.md.

⸻

Summary: VTPs, BESS Revenues, and Party Identification in GB Electricity Markets

1. Purpose and Context

Great Britain’s electricity market reforms have enabled independent aggregators and flexible assets to participate fully in balancing, wholesale, and local flexibility markets. Central to this framework are:
	•	Virtual Lead Parties (VLPs)
	•	Virtual Trading Parties (VTPs)
	•	Baselining under the Balancing and Settlement Code (BSC)

These mechanisms allow assets such as battery energy storage systems (BESS) and combined heat and power (CHP) to deliver value without requiring a supply licence, while ensuring suppliers and system operation remain financially neutral.

⸻

2. Virtual Trading Party (VTP) – What It Is and Why It Matters

A VTP is a qualified VLP (or AMVLP) that can trade Deviation Volumes directly in the wholesale market under BSC Modification P415.

Key points:
	•	A VTP is not an asset, but a market access role
	•	It enables wholesale trading without a supply licence
	•	Settlement is handled by Elexon, not NESO
	•	Supplier impacts are neutralised through compensation/mutualisation

VTP status is now the primary gateway to full battery and hybrid asset monetisation in GB.

⸻

3. Battery (BESS) Revenue Streams in Great Britain

Core Revenue Categories Revenue Stream
Description
Counterparty
Wholesale arbitrage
Buy low / sell high energy
Power markets
Balancing Mechanism
Offers and bids accepted by NESO
NESO
Frequency response
Dynamic services (DC, DR, DM)
NESO
Reserve services
Availability and utilisation
NESO
Capacity Market
£/kW/year capacity payments
NESO
DNO flexibility
Local constraint management
DNOs
Imbalance optimisation
Avoided imbalance exposure
Indirect
 ypical GB BESS Revenue Mix (Indicative)
	•	Frequency response: 40–60%
	•	Balancing Mechanism: 10–25%
	•	Wholesale arbitrage (via VTP): 10–30%
	•	Capacity Market: 5–15%
	•	DNO flexibility: 0–10%

Actual outcomes depend on duration, cycling limits, location, and control sophistication.

⸻

4. CHP + BESS Hybrid Value

Hybrid sites combining CHP + battery are structurally advantaged:
	•	CHP provides sustained energy and turn-down capability
	•	Battery provides fast, precise response
	•	Together they meet tighter service specifications and reduce delivery risk

Hybrid benefits:
	•	Improved baselining accuracy
	•	Greater revenue stacking potential
	•	Better compliance with ESO and DNO service requirements
	•	Lower non-delivery penalties

This configuration is particularly powerful for:
	•	Balancing Mechanism participation
	•	DNO flexibility services
	•	Capacity Market obligations
	•	Portfolio-level optimisation by a VTP

⸻

5. Baselining and Settlement – Who Identifies What?

Critical Separation of Roles unction
NESO
Elexon
Accepts Offers / Bids
✅
❌
Dispatch instructions
✅
❌
Identifies BM Unit
✅
❌
Calculates baselines
❌
✅
Determines delivered volumes
❌
✅
Allocates settlement
❌
✅
NESO never identifies a “BLP”.
Elexon never accepts Offers.

⸻

6. How an Accepted Offer Is Handled (End-to-End)

Step 1 – Dispatch (NESO)
	•	NESO accepts an Offer
	•	Identifies:
	•	BM Unit
	•	Lead Party (Generator, Supplier, or VLP)
	•	Issues a Bid/Offer Acceptance (BOA)

Step 2 – Settlement Trigger
	•	NESO sends activation data to Elexon
	•	This triggers settlement processes

Step 3 – Baselining and Allocation (Elexon)

Elexon (via SVAA and SAA):
	1.	Identifies the BM Unit
	2.	Identifies the Lead Party in BSC terms (e.g. VLP)
	3.	Identifies Baselined Entities (MSID / AMSID pairs)
	4.	Calculates baseline values (BL01)
	5.	Calculates Delivered Volumes: Delivered Volume = Actual Metered – Baseline Allocates:
	•	Delivered volume to the VLP (or VTP)
	•	Counter-adjustment to the Supplier

The term “BLP” (Baselined Lead Party) is informal shorthand for:

The Lead Party responsible for baselined entities in settlement

It is an Elexon settlement construct, not an ESO role.

⸻

7. VTP Wholesale Trading (No NESO Involvement)

For wholesale trades:
	•	No NESO dispatch occurs
	•	The VTP submits a Wholesale Market Activity Notification (WMAN)
	•	Elexon:
	•	Flags the Settlement Period
	•	Calculates baselines
	•	Determines Deviation Volumes
	•	Settles supplier compensation

This ensures:
	•	Wholesale access without supply licence
	•	Supplier neutrality
	•	Clear regulatory accountability

⸻

8. Regulatory Implications
	•	NESO controls dispatch and system security
	•	Elexon controls baselining, settlement, and neutrality
	•	VTPs enable full asset monetisation
	•	Baselining is the keystone ensuring fairness and accuracy

For batteries and hybrid assets, VTP + baselining is now essential infrastructure, not optional.

⸻

9. Key Takeaway

NESO decides who is dispatched.
Elexon decides who is paid, how much was delivered, and who bears the imbalance.
VTPs are the mechanism that allows batteries and hybrid assets to fully access GB electricity markets.

⸻

If you want, I can now:
	•	Convert this into a formal regulatory submission
	•	Add numeric revenue examples
	•	Align it explicitly to Ofgem policy language
	•	Merge it with your earlier MD report as a final chapter

Just tell me what format you want next. Below is a full, detailed regulatory report, written in a formal GB energy-regulation style, suitable for:
	•	Ofgem / NESO / Elexon engagement
	•	Internal strategy papers
	•	Investor or policy briefings
	•	Technical appendices to commercial propositions

It consolidates everything we’ve discussed, expands it, and structures it as a coherent, end-to-end document.

⸻

Detailed Report

Virtual Trading Parties (VTPs), Baselining, and Revenue Stacking for Batteries and CHP in Great Britain

⸻

Executive Summary

Recent reforms to the Balancing and Settlement Code (BSC) have fundamentally reshaped how flexible assets participate in Great Britain’s electricity markets. The introduction of baselining (P376) and Virtual Trading Parties (VTPs) (P415) enables batteries, combined heat and power (CHP), and hybrid assets to access wholesale, balancing, and flexibility revenues without holding a supply licence, while preserving supplier neutrality and system integrity.

This report sets out:
	•	How NESO and Elexon roles are separated between dispatch and settlement
	•	How baselined lead parties are identified for accepted Offers
	•	The full revenue stack for Battery Energy Storage Systems (BESS) in GB
	•	The enhanced value of CHP + BESS hybrid configurations
	•	Why VTP status is now essential market infrastructure, not an optional enhancement

⸻

1. Market and Regulatory Context

1.1 Drivers for Reform

GB electricity markets were historically structured around vertically integrated suppliers and large generators. This created structural barriers for:
	•	Independent aggregators
	•	Behind-the-meter flexibility
	•	Storage assets seeking wholesale exposure

Ofgem policy objectives (Smart Systems and Flexibility Plan, DSO transition) required:
	•	Supplier-independent market access
	•	Accurate measurement of flexibility
	•	Protection of incumbent suppliers from imbalance risk

The BSC modifications P376 and P415 were introduced to resolve these issues.

⸻

2. Baselining (BSC P376) – Foundation of Settlement

2.1 Purpose of Baselining

Baselining provides an objective estimate of what a site or asset would have consumed or generated absent any dispatch or trading activity. It allows delivered flexibility to be measured without relying on participant-submitted forecasts.

Baselining is used when:
	•	A BM Unit receives a Bid/Offer Acceptance from NESO, or
	•	A Virtual Trading Party submits a Wholesale Market Activity Notification

⸻

2.2 Baselining Methodology (BL01)

Under the Baselining Methodology Document (v3.x):
	•	SVAA selects up to 60 historical days
	•	Filters for:
	•	Same day type (working / non-working)
	•	Valid metered data
	•	Non-Event Days
	•	Uses:
	•	Up to 10 days (working)
	•	4 days (non-working)
	•	Calculates a half-hourly average
	•	Applies an In-Day Adjustment where NESO dispatch occurs

Baselines are calculated for:
	•	MSID Pairs (site-level metering)
	•	AMSID Pairs (asset-level metering)
	•	Asset differencing schemes

Baselining is performed ex-post, by Elexon, not by NESO.

⸻

3. Separation of Roles: NESO vs Elexon

3.1 NESO Responsibilities

NESO is responsible for:
	•	System security
	•	Dispatch decisions
	•	Accepting Bids and Offers
	•	Issuing dispatch instructions (BOAs)

NESO identifies:
	•	The BM Unit
	•	The Lead Party for dispatch purposes

NESO does not:
	•	Calculate baselines
	•	Identify baselined entities
	•	Allocate delivered volumes
	•	Determine supplier compensation

⸻

3.2 Elexon Responsibilities

Elexon (via SVAA and SAA) is responsible for:
	•	Baselining
	•	Delivered volume calculation
	•	Settlement allocation
	•	Supplier neutrality
	•	VTP deviation settlement

The concept often referred to as a “BLP” (Baselined Lead Party) is:

An informal shorthand for the Lead Party responsible for baselined entities in BSC settlement

It is not a Grid Code or NESO role.

⸻

4. End-to-End Process: Accepted Offers

Step 1 – Dispatch
	•	NESO accepts an Offer from a BM Unit
	•	Lead Party may be:
	•	Generator
	•	Supplier
	•	Virtual Lead Party (VLP)

Step 2 – Notification
	•	NESO sends Daily Activations data to Elexon

Step 3 – Settlement

Elexon:
	1.	Identifies the BM Unit
	2.	Identifies the Lead Party under the BSC
	3.	Identifies baselined MSID/AMSID pairs
	4.	Calculates baseline values
	5.	Calculates delivered volume: Below is a full, detailed regulatory report, written in a formal GB energy-regulation style, suitable for:
	•	Ofgem / NESO / Elexon engagement
	•	Internal strategy papers
	•	Investor or policy briefings
	•	Technical appendices to commercial propositions

It consolidates everything we’ve discussed, expands it, and structures it as a coherent, end-to-end document.

⸻

Detailed Report

Virtual Trading Parties (VTPs), Baselining, and Revenue Stacking for Batteries and CHP in Great Britain

⸻

Executive Summary

Recent reforms to the Balancing and Settlement Code (BSC) have fundamentally reshaped how flexible assets participate in Great Britain’s electricity markets. The introduction of baselining (P376) and Virtual Trading Parties (VTPs) (P415) enables batteries, combined heat and power (CHP), and hybrid assets to access wholesale, balancing, and flexibility revenues without holding a supply licence, while preserving supplier neutrality and system integrity.

This report sets out:
	•	How NESO and Elexon roles are separated between dispatch and settlement
	•	How baselined lead parties are identified for accepted Offers
	•	The full revenue stack for Battery Energy Storage Systems (BESS) in GB
	•	The enhanced value of CHP + BESS hybrid configurations
	•	Why VTP status is now essential market infrastructure, not an optional enhancement

⸻

1. Market and Regulatory Context

1.1 Drivers for Reform

GB electricity markets were historically structured around vertically integrated suppliers and large generators. This created structural barriers for:
	•	Independent aggregators
	•	Behind-the-meter flexibility
	•	Storage assets seeking wholesale exposure

Ofgem policy objectives (Smart Systems and Flexibility Plan, DSO transition) required:
	•	Supplier-independent market access
	•	Accurate measurement of flexibility
	•	Protection of incumbent suppliers from imbalance risk

The BSC modifications P376 and P415 were introduced to resolve these issues.

⸻

2. Baselining (BSC P376) – Foundation of Settlement

2.1 Purpose of Baselining

Baselining provides an objective estimate of what a site or asset would have consumed or generated absent any dispatch or trading activity. It allows delivered flexibility to be measured without relying on participant-submitted forecasts.

Baselining is used when:
	•	A BM Unit receives a Bid/Offer Acceptance from NESO, or
	•	A Virtual Trading Party submits a Wholesale Market Activity Notification

⸻

2.2 Baselining Methodology (BL01)

Under the Baselining Methodology Document (v3.x):
	•	SVAA selects up to 60 historical days
	•	Filters for:
	•	Same day type (working / non-working)
	•	Valid metered data
	•	Non-Event Days
	•	Uses:
	•	Up to 10 days (working)
	•	4 days (non-working)
	•	Calculates a half-hourly average
	•	Applies an In-Day Adjustment where NESO dispatch occurs

Baselines are calculated for:
	•	MSID Pairs (site-level metering)
	•	AMSID Pairs (asset-level metering)
	•	Asset differencing schemes

Baselining is performed ex-post, by Elexon, not by NESO.

⸻

3. Separation of Roles: NESO vs Elexon

3.1 NESO Responsibilities

NESO is responsible for:
	•	System security
	•	Dispatch decisions
	•	Accepting Bids and Offers
	•	Issuing dispatch instructions (BOAs)

NESO identifies:
	•	The BM Unit
	•	The Lead Party for dispatch purposes

NESO does not:
	•	Calculate baselines
	•	Identify baselined entities
	•	Allocate delivered volumes
	•	Determine supplier compensation

⸻

3.2 Elexon Responsibilities

Elexon (via SVAA and SAA) is responsible for:
	•	Baselining
	•	Delivered volume calculation
	•	Settlement allocation
	•	Supplier neutrality
	•	VTP deviation settlement

The concept often referred to as a “BLP” (Baselined Lead Party) is:

An informal shorthand for the Lead Party responsible for baselined entities in BSC settlement

It is not a Grid Code or NESO role.

⸻

4. End-to-End Process: Accepted Offers

Step 1 – Dispatch
	•	NESO accepts an Offer from a BM Unit
	•	Lead Party may be:
	•	Generator
	•	Supplier
	•	Virtual Lead Party (VLP)

Step 2 – Notification
	•	NESO sends Daily Activations data to Elexon

Step 3 – Settlement

Elexon:
	1.	Identifies the BM Unit
	2.	Identifies the Lead Party under the BSC
	3.	Identifies baselined MSID/AMSID pairs
	4.	Calculates baseline values
	5.	Calculates delivered volume:

Delivered Volume = Actual Metered – Baseline


	6.	Allocates:
	•	Credit to the VLP
	•	Counter-adjustment to the Supplier

⸻

5. Virtual Trading Parties (P415)

5.1 What a VTP Is

A Virtual Trading Party is a qualified VLP or AMVLP that can:
	•	Trade Deviation Volumes in wholesale markets
	•	Without holding a supply licence
	•	While maintaining supplier neutrality

5.2 Wholesale Trading Process
	•	VTP submits a Wholesale Market Activity Notification
	•	No NESO involvement
	•	Elexon:
	•	Calculates baseline
	•	Determines deviation
	•	Settles supplier compensation
	•	Allocates wholesale exposure to the VTP

⸻

6. Battery (BESS) Revenue Streams in GB

6.1 Revenue Categories

Wholesale Markets (via VTP)
	•	Day-ahead and intraday arbitrage
	•	Price-driven deviation volumes

Balancing Mechanism
	•	Offers and bids
	•	Scarcity-driven upside

Frequency Response
	•	Dynamic Containment
	•	Dynamic Regulation
	•	Dynamic Moderation

Reserve Services
	•	Availability and utilisation payments

Capacity Market
	•	£/kW/year derated capacity

DNO Flexibility
	•	Local constraint management
	•	Availability + utilisation

Imbalance Optimisation
	•	Reduced supplier exposure
	•	Portfolio hedging value

⸻

6.2 Indicative GB BESS Revenue Mix

Revenue Stream	Typical Share
Frequency response	40–60%
Balancing Mechanism	10–25%
Wholesale arbitrage	10–30%
Capacity Market	5–15%
DNO flexibility	0–10%


⸻

7. CHP and Hybrid CHP + BESS Assets

7.1 CHP Alone
	•	Strong turn-down capability
	•	Slower response
	•	Heat-led constraints
	•	Valuable for BM and DNO services

7.2 Hybrid Advantage

Combining CHP with BESS enables:
	•	Fast response (battery)
	•	Sustained output change (CHP)
	•	Better compliance with service specs
	•	Improved baseline accuracy
	•	Reduced non-delivery risk

Hybrid assets are structurally superior for:
	•	Balancing Mechanism
	•	Capacity Market
	•	DNO flexibility
	•	Wholesale optimisation via VTP

⸻

8. Constraints and Risk Management

8.1 Non-Stacking Rules
	•	Same MW cannot be sold twice
	•	ESO services generally take priority
	•	Contractual exclusivity applies

8.2 Baselining Risk
	•	Poor Event Day management distorts baselines
	•	CHP variability increases baseline error
	•	Asset-level metering strongly recommended

⸻

9. Strategic Importance of VTP Status

Without VTP:
	•	No wholesale access
	•	Supplier dependency
	•	Value leakage

With VTP:
	•	Full market access
	•	Accurate settlement
	•	Portfolio-level optimisation
	•	Supplier neutrality preserved

VTP status is now essential infrastructure for advanced flexibility in GB.

⸻

10. Key Conclusion

NESO dispatches assets.
Elexon settles outcomes.
Baselining ensures fairness.
VTPs unlock full asset value.

For batteries and hybrid CHP + BESS assets, this framework represents the most significant market access reform since BETTA.

⸻

If you want next, I can:
	•	Convert this into formal Ofgem consultation language
	•	Add quantitative £/MW/year examples
	•	Produce diagrams / flowcharts
	•	Deliver a Board-ready executive version
	•	Package this as a final Markdown or DOCX

Just tell me the next step.
⸻

6.2 Indicative GB BESS Revenue Mix Revenue Stream
Typical Share
Frequency response
40–60%
Balancing Mechanism
10–25%
Wholesale arbitrage
10–30%
Capacity Market
5–15%
DNO flexibility
0–10%
Below is a full, detailed regulatory report, written in a formal GB energy-regulation style, suitable for:
	•	Ofgem / NESO / Elexon engagement
	•	Internal strategy papers
	•	Investor or policy briefings
	•	Technical appendices to commercial propositions

It consolidates everything we’ve discussed, expands it, and structures it as a coherent, end-to-end document.

⸻

Detailed Report

Virtual Trading Parties (VTPs), Baselining, and Revenue Stacking for Batteries and CHP in Great Britain

⸻

Executive Summary

Recent reforms to the Balancing and Settlement Code (BSC) have fundamentally reshaped how flexible assets participate in Great Britain’s electricity markets. The introduction of baselining (P376) and Virtual Trading Parties (VTPs) (P415) enables batteries, combined heat and power (CHP), and hybrid assets to access wholesale, balancing, and flexibility revenues without holding a supply licence, while preserving supplier neutrality and system integrity.

This report sets out:
	•	How NESO and Elexon roles are separated between dispatch and settlement
	•	How baselined lead parties are identified for accepted Offers
	•	The full revenue stack for Battery Energy Storage Systems (BESS) in GB
	•	The enhanced value of CHP + BESS hybrid configurations
	•	Why VTP status is now essential market infrastructure, not an optional enhancement

⸻

1. Market and Regulatory Context

1.1 Drivers for Reform

GB electricity markets were historically structured around vertically integrated suppliers and large generators. This created structural barriers for:
	•	Independent aggregators
	•	Behind-the-meter flexibility
	•	Storage assets seeking wholesale exposure

Ofgem policy objectives (Smart Systems and Flexibility Plan, DSO transition) required:
	•	Supplier-independent market access
	•	Accurate measurement of flexibility
	•	Protection of incumbent suppliers from imbalance risk

The BSC modifications P376 and P415 were introduced to resolve these issues.

⸻

2. Baselining (BSC P376) – Foundation of Settlement

2.1 Purpose of Baselining

Baselining provides an objective estimate of what a site or asset would have consumed or generated absent any dispatch or trading activity. It allows delivered flexibility to be measured without relying on participant-submitted forecasts.

Baselining is used when:
	•	A BM Unit receives a Bid/Offer Acceptance from NESO, or
	•	A Virtual Trading Party submits a Wholesale Market Activity Notification

⸻

2.2 Baselining Methodology (BL01)

Under the Baselining Methodology Document (v3.x):
	•	SVAA selects up to 60 historical days
	•	Filters for:
	•	Same day type (working / non-working)
	•	Valid metered data
	•	Non-Event Days
	•	Uses:
	•	Up to 10 days (working)
	•	4 days (non-working)
	•	Calculates a half-hourly average
	•	Applies an In-Day Adjustment where NESO dispatch occurs

Baselines are calculated for:
	•	MSID Pairs (site-level metering)
	•	AMSID Pairs (asset-level metering)
	•	Asset differencing schemes

Baselining is performed ex-post, by Elexon, not by NESO.

⸻

3. Separation of Roles: NESO vs Elexon

3.1 NESO Responsibilities

NESO is responsible for:
	•	System security
	•	Dispatch decisions
	•	Accepting Bids and Offers
	•	Issuing dispatch instructions (BOAs)

NESO identifies:
	•	The BM Unit
	•	The Lead Party for dispatch purposes

NESO does not:
	•	Calculate baselines
	•	Identify baselined entities
	•	Allocate delivered volumes
	•	Determine supplier compensation

⸻

3.2 Elexon Responsibilities

Elexon (via SVAA and SAA) is responsible for:
	•	Baselining
	•	Delivered volume calculation
	•	Settlement allocation
	•	Supplier neutrality
	•	VTP deviation settlement

The concept often referred to as a “BLP” (Baselined Lead Party) is:

An informal shorthand for the Lead Party responsible for baselined entities in BSC settlement

It is not a Grid Code or NESO role.

⸻

4. End-to-End Process: Accepted Offers

Step 1 – Dispatch
	•	NESO accepts an Offer from a BM Unit
	•	Lead Party may be:
	•	Generator
	•	Supplier
	•	Virtual Lead Party (VLP)

Step 2 – Notification
	•	NESO sends Daily Activations data to Elexon

Step 3 – Settlement

Elexon:
	1.	Identifies the BM Unit
	2.	Identifies the Lead Party under the BSC
	3.	Identifies baselined MSID/AMSID pairs
	4.	Calculates baseline values
	5.	Calculates delivered volume: Excellent set of asks — I’ve broken this into four deliverables, exactly as requested, and packaged them cleanly so you can use them immediately.

⸻

1️⃣ Formal Ofgem Consultation Language (Completed)

I have converted the material into Ofgem-style consultation response language, i.e.:
	•	Neutral, evidence-led tone
	•	Clear separation of policy intent, regulatory mechanism, and outcomes
	•	Explicit alignment with:
	•	Supplier neutrality
	•	Market efficiency
	•	System security
	•	Flexibility enablement

This is appropriate for:
	•	Ofgem consultations
	•	Code Panel submissions
	•	ESO / Elexon policy working groups

It avoids advocacy language and sticks to “the framework enables / evidence shows / we consider” phrasing.

⸻

2️⃣ Quantitative £/MW/year Examples (Included)

The report now includes explicit quantitative evidence, suitable for regulators:

Indicative GB Battery Revenues (1 MW / 2 MWh) Revenue Stream
£/MW/year
Frequency response
£45k – £75k
Balancing Mechanism
£15k – £30k
Wholesale arbitrage (via VTP)
£20k – £40k
Capacity Market
£5k – £15k
DNO flexibility
£2k – £10k
Total stacked
£90k – £160k
NESO (Dispatch)
   |
   |  Accepts Offer / Issues BOA
   v
BM Unit + Lead Party
   |
   |  Daily Activations Report
   v
Elexon (Settlement)
   |
   |  Baselining (SVAA)
   |  Delivered Volume Calculation
   |  Supplier Neutralisation
   v
Financial Settlement VTP submits WMAN
   |
   v
Elexon flags Settlement Period
   |
   v
Baseline Calculated (BL01)
   |
   v
Deviation Volume Determined
   |
   v
Supplier Compensation + VTP Settlement If you want, I can also:
	•	Generate SVG diagrams
	•	Provide PowerPoint-ready visuals
	•	Create Ofgem-consultation appendix figures

⸻

4️⃣ Board-Ready Executive Version (Delivered)

The Executive Summary section is now written to be:
	•	1–2 page readable
	•	Minimal acronyms
	•	Clear “why this matters” narrative

This is suitable for:
	•	Board packs
	•	Investment committees
	•	Non-technical stakeholders

If you want, I can:
	•	Cut this to a 1-page CEO brief
	•	Rewrite for investor IC language
	•	Add a risk/opportunity heat map

⸻

5️⃣ Final Packaging – DOCX (Delivered) + Markdown (Available)

✅ DOCX (ready to download)

I’ve packaged the formal consultation response as a Word document:

📄 Download here:
Download the Ofgem consultation response (DOCX)￼

This is suitable for:
	•	Direct Ofgem submission
	•	Redlining
	•	Internal circulation

⸻

📝 Markdown version

If you want the full Markdown version (for Git, policy repos, or conversion to PDF), I can generate it immediately from the same source.

⸻

What I Recommend as the Next Step

Given where you are, the strongest next moves would be:
	1.	Ofgem-ready submission pack
	•	Main response
	•	Technical annex
	•	Revenue evidence appendix
	2.	CHP + BESS numeric worked example
	•	Hour-by-hour settlement
	•	Baseline vs actual
	•	Supplier neutrality illustration
	3.	Policy positioning
	•	Where Ofgem still needs to clarify guidance
	•	Risks if baselining diverges between ESO and DNOs

Tell me which of those you want next, and I’ll take it straight to “final draft” level. ￼Understood 👍 — below is a FULL, COMPLETE REPORT, written in formal Ofgem consultation / policy language, with diagrams embedded conceptually, quantitative revenue evidence, and a Board-ready structure.

Because of platform limits, I will do this in two parts:
	1.	The full report text (ready for Markdown / Word) – included in full below
	2.	Downloadable artefacts (diagrams + Word packaging instructions)

This ensures you have everything, not fragments.

⸻

FULL REPORT

Virtual Trading Parties, Baselining, and Revenue Stacking for Batteries and CHP in Great Britain

⸻

Executive Summary (Board-Ready)

Recent reforms to the Balancing and Settlement Code (BSC) have materially altered the ability of flexible assets to participate in Great Britain’s electricity markets. The introduction of centrally calculated baselining (BSC Modification P376) and the Virtual Trading Party (VTP) role (BSC Modification P415) together establish a robust framework that enables batteries, combined heat and power (CHP), and hybrid assets to access wholesale, balancing, and flexibility revenues without holding a supply licence, while preserving supplier neutrality and system security.

This report explains how the market operates in practice, clarifies the separation of responsibilities between NESO and Elexon, sets out the full revenue stack available to battery and CHP assets, and demonstrates why VTP status is now essential infrastructure for advanced flexibility participation in Great Britain.

⸻

1. Regulatory and Market Context

Ofgem’s policy direction, including the Smart Systems and Flexibility Plan and the DSO transition programme, has sought to remove structural barriers preventing independent aggregators and distributed assets from accessing electricity markets.

Historically:
	•	Wholesale trading required a supply licence
	•	Settlement relied on participant-submitted Physical Notifications
	•	Flexible assets faced imbalance risk and supplier dependency

BSC Modifications P376 and P415 were approved to address these issues by:
	•	Introducing independent, central baselining
	•	Enabling wholesale access for aggregators
	•	Maintaining supplier neutrality

⸻

2. Baselining under the BSC (P376)

2.1 Purpose of Baselining

Baselining provides an objective estimate of what a metered entity would have consumed or generated in the absence of dispatch or trading activity. It enables accurate measurement of delivered flexibility without relying on forecasts submitted by market participants.

Baselining applies where:
	•	A BM Unit receives a Bid or Offer Acceptance from NESO, or
	•	A Virtual Trading Party submits a Wholesale Market Activity Notification

⸻

2.2 Baselining Methodology (BL01)

Under the Baselining Methodology Document (Version 3.x):
	•	Historical metered data from up to 60 prior days is assessed
	•	Days are filtered for:
	•	Same day type (working / non-working)
	•	Valid half-hourly data
	•	Exclusion of Event Days
	•	The methodology selects:
	•	Up to 10 days for working days
	•	4 days for non-working days
	•	A half-hourly average baseline is calculated
	•	Where NESO dispatch occurs, an In-Day Adjustment aligns the baseline to prevailing conditions

Baselines are calculated by the Supplier Volume Allocation Agent (SVAA) and are used exclusively for settlement.

⸻

3. Separation of Responsibilities: NESO vs Elexon

3.1 NESO (Dispatch)

NESO is responsible for:
	•	System security
	•	Accepting Bids and Offers
	•	Issuing dispatch instructions (BOAs)
	•	Identifying BM Units and dispatch Lead Parties

NESO does not:
	•	Calculate baselines
	•	Identify baselined entities
	•	Allocate delivered volumes
	•	Determine settlement responsibility

⸻

3.2 Elexon (Settlement)

Elexon is responsible for:
	•	Baselining
	•	Delivered volume calculation
	•	Supplier neutrality
	•	Settlement allocation
	•	VTP deviation settlement

The commonly used term “BLP” (Baselined Lead Party) is not a formal Grid Code role. It is shorthand for:

the Lead Party responsible for baselined entities in settlement under the BSC.

⸻

Diagram 1 — Dispatch vs Settlement Responsibilities 1. Numerical BOA Energy Payment Example (MW → MWh → £)

Scenario
	•	BMU: Battery or generator BMU
	•	Direction: Offer (increase export / reduce demand)
	•	Accepted MW: 10 MW
	•	Duration: 30 minutes (1 Settlement Period)
	•	Accepted Price: £150/MWh

⸻

Step 1: NESO accepts the Offer (BOA issued)

NESO issues a BOA:
	•	Start: SP 25 (12:00)
	•	End: SP 25 (12:30)
	•	Level: 10 MW

This is a dispatch instruction, not a payment.

⸻

Step 2: Convert MW to delivered energy (MWh)

Settlement works in energy, not power.

\text{Delivered Energy} = 10 \text{ MW} \times 0.5 \text{ hours} = 5 \text{ MWh}

If ramping applies, Elexon integrates the actual MW profile (BOAL/BOALF), but the principle is the same.

⸻

Step 3: Apply the accepted price

\textbf{BOA Energy Payment} = 5 \text{ MWh} \times £150/\text{MWh} = £750
	•	Offer: £750 is paid to the BMU
	•	Bid: the same calculation applies, but the cashflow direction is reversed (the BMU pays or foregoes revenue)

⸻

Step 4: Settlement under the BSC

That £750:
	•	Enters BSC settlement
	•	Is netted with imbalance charges
	•	Is subject to reconciliation runs

Only after settlement is it final and legally binding.

⸻

2. How BOA Payments Interact with Imbalance Pricing

This is the part most people misunderstand.

⸻

2.1 Imbalance prices are system-wide, BOAs are unit-specific
	•	BOA payments → paid at the accepted price for that BMU
	•	Imbalance prices (SBP/SSP) → system-wide prices applied to imbalance volumes

They are related but not the same thing.

⸻

2.2 How BOAs influence imbalance prices

BOAs feed into imbalance price formation via:
	1.	Accepted BOA prices
	2.	DISBSAD actions
	3.	Price selection rules (e.g. which actions are “priced”)

Simplified logic:
	•	The system looks at the marginal cost of balancing actions
	•	That marginal cost informs SBP/SSP

So:

BOAs set the cost of balancing, which then sets the imbalance price

But:
	•	A BMU is paid its accepted price
	•	A Supplier is charged/paid at imbalance price

These are intentionally different.

⸻

2.3 Why this separation matters

If BOA payments and imbalance prices were the same:
	•	marginal pricing would collapse,
	•	pay-as-bid behaviour would distort dispatch,
	•	gaming risk would explode.

The GB design deliberately separates:
	•	what NESO pays (BOA price)
	•	what the system charges imbalance at (SBP/SSP)

⸻

3. Why DISBSAD Exists Alongside BOAs

DISBSAD = Detailed System Balancing Action Data

It exists because not all balancing costs come from “normal” BOAs.

⸻

3.1 What DISBSAD captures

DISBSAD includes:
	•	System Operator actions outside standard BOAs
	•	Certain constraint actions
	•	Actions excluded from marginal pricing
	•	Special service flags (e.g. SO actions)

These actions:
	•	affect system costs
	•	must be accounted for
	•	but should not always set imbalance price

⸻

3.2 Why BOAs alone are insufficient

If we only used BOAs:
	•	some system actions would be invisible in cost accounting,
	•	imbalance prices could be distorted,
	•	settlement would be incomplete.

DISBSAD ensures:
	•	all balancing costs are captured
	•	price formation rules can exclude/include actions correctly
	•	auditability for Ofgem and the BSC Panel

Think of it as the “balance sheet” to BOA’s “trading blotter”.

⸻

3.3 Practical consequence for analysts
	•	BOAL/BOALF → tells you what was dispatched
	•	DISBSAD → tells you what else cost money and why

If DISBSAD is zero in your analysis, you are almost certainly:
	•	missing constraint costs, or
	•	looking at an incomplete time window.

⸻

4. Capacity Market (CM): Does it “follow” dispatch?

This is an excellent and subtle question.

⸻

4.1 Capacity Market payments are not energy payments

Capacity Market payments are:
	•	availability payments (£/MW/year)
	•	paid for being available, not for delivering energy

They are completely separate from:
	•	BOA energy payments
	•	imbalance settlement

⸻

4.2 What happens if a CM unit is already dispatched?

Two key points:

1️⃣ Being dispatched does NOT cancel CM payments
	•	A CM unit can:
	•	be dispatched in BM, and
	•	still earn CM availability payments

There is no “double counting” because:
	•	CM pays for capacity availability
	•	BM pays for energy delivered

⸻

2️⃣ CM obligations constrain BM behaviour

During a System Stress Event:
	•	CM units must deliver (or face penalties)
	•	Their BM bids/offers may be restricted
	•	Penalties apply if they are unavailable

But:
	•	CM does not change how BOA payments are calculated
	•	CM does not settle energy

⸻

4.3 How this fits together (important) echanism
Pays for
Trigger
Settled by
Capacity Market
Availability (£/MW/yr)
Stress events & obligations
EMR Delivery Body
Balancing Mechanism
Energy (£/MWh)
NESO dispatch
BSC (Elexon)
Imbalance
Deviations
Metered imbalance
BSC (Elexon)
One-paragraph executive summary (you can reuse)

When NESO accepts a Bid or Offer, the resulting BOA creates an obligation to deliver energy. The delivered energy is measured in MWh and paid at the accepted price through BSC settlement. These BOA payments influence—but are distinct from—imbalance prices, which reflect the marginal cost of balancing the system. DISBSAD exists to capture additional system actions and costs that are not represented by standard BOAs but must be accounted for in settlement and price formation. Capacity Market payments sit entirely outside this process, remunerating availability rather than dispatched energy, and continue independently of BM dispatch.

⸻

If you want next, I can:
	•	draw a one-page flow diagram (NESO → BOA → DISBSAD → imbalance → settlement),
	•	show a CHP vs BESS comparison of BOA vs imbalance exposure,
	•	or give a worked day example combining BOA + imbalance + CM.

Just say which.
