# UK Energy Data Source Distinction Guide

## 📊 **Data Source Overview** (386 Total Tables)

### 🏢 **ELEXON/BMRS Data** - 116 Tables
**Source:** Balancing Mechanism Reporting Service (wholesale electricity market)
**Prefix:** `bmrs_*`
**Coverage:** Wholesale market operations, trading, and system balancing

#### Categories:
- **Market Trading (7 tables):** BOD (bid/offer data), BOALF (accepted offers/bids)
- **System Balancing (6 tables):** Frequency response, MELs/MILs (imbalance data)
- **Generation Data (6 tables):** Fuel mix, generation output by technology
- **Demand & Forecasting (8 tables):** System demand, imbalance forecasts
- **Grid Operations (7 tables):** Transmission system data, availability
- **Interconnectors (4 tables):** Cross-border electricity flows
- **Wind & Renewables (2 tables):** Wind generation forecasts
- **Technical & Monitoring (11 tables):** Quality assurance, system warnings
- **Other BMRS Data (65 tables):** Additional wholesale market datasets

---

### 🌐 **NESO Portal Data** - 171 Tables
**Source:** National Energy System Operator (system operations & planning)
**Prefix:** `neso_*` or contains keywords like `bsuos`, `carbon_intensity`, `capacity_market`
**Coverage:** System operations, balancing costs, carbon intensity, capacity planning

#### Categories:
- **BSUoS & Balancing (146 tables):** Balancing Services Use of System charges, monthly forecasts, tariffs
- **Forecasting (13 tables):** Demand forecasts, constraint predictions
- **Capacity Market (3 tables):** Capacity auction data, market unit registrations
- **Carbon Intensity (3 tables):** Real-time and regional carbon intensity data
- **Constraint Management (2 tables):** Network constraint costs and limits
- **Other NESO Data (4 tables):** Catalog and organizational data

---

### 🔌 **UKPN Distribution Data** - 10 Tables
**Source:** UK Power Networks (Distribution Network Operator for London, South East, East England)
**Prefix:** `ukpn_*`
**Coverage:** Distribution network operations, charges, and technical data

#### Tables:
- **Network Infrastructure:** 33kV circuits, transformer data, fault levels
- **Tariffs & Charges:** DUoS (Distribution Use of System) charges
- **Low Carbon:** Electric vehicle and heat pump connection data
- **Operations:** Network losses, operational restrictions

---

### 🏗️ **Other DNO Data** - 1 Table
**Source:** General Distribution Network Operator data
**Coverage:** Geographic boundaries and license areas

#### Table:
- **GIS Boundaries:** GB DNO license area boundaries for mapping

---

### ⚡ **Other System Operations** - 11 Tables
**Source:** Various system operation datasets not clearly categorized above
**Coverage:** Additional demand forecasts, wind predictions, operational data

---

### ❓ **Unclassified Tables** - 77 Tables
**Source:** Various energy industry sources requiring further categorization
**Examples:** Constraint limits, tariff data, industry notifications, auction data

---

## 🔍 **How to Query by Data Source**

### BigQuery Views Created:
1. **`elexon_bmrs_data_view`** - Lists all ELEXON/BMRS tables
2. **`neso_portal_data_view`** - Lists all NESO Portal tables
3. **`dno_distribution_data_view`** - Lists all DNO/distribution tables

### SQL Examples:

```sql
-- All ELEXON wholesale market data
SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
LIMIT 1000;

-- All NESO balancing cost data
SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.*`
WHERE _TABLE_SUFFIX LIKE '%bsuos%';

-- All UKPN distribution data
SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.ukpn_duos_charges_annex1`
LIMIT 1000;

-- Carbon intensity from NESO
SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.neso_carbon_intensity__current_intensity`
LIMIT 1000;
```

## 📈 **Data Hierarchy**

```
UK Electricity System Data
├── Transmission Level (ELEXON/BMRS)
│   ├── Wholesale Market Trading
│   ├── System Balancing
│   └── Grid Operations
├── System Operations (NESO)
│   ├── Balancing Costs (BSUoS)
│   ├── Carbon Intensity
│   ├── Capacity Planning
│   └── Forecasting
└── Distribution Level (DNOs)
    ├── UKPN (London, South East, East)
    ├── Network Infrastructure
    └── Tariffs & Charges
```

## 🎯 **Key Distinctions**

| Data Source     | Level        | Focus                     | Time Granularity | Key Tables                        |
| --------------- | ------------ | ------------------------- | ---------------- | --------------------------------- |
| **ELEXON/BMRS** | Transmission | Wholesale market, trading | 30min - daily    | bmrs_bod, bmrs_freq               |
| **NESO Portal** | System ops   | Balancing, planning       | Daily - monthly  | bsuos forecasts, carbon intensity |
| **UKPN**        | Distribution | Network operations        | Static/annual    | duos_charges, network_losses      |
| **Other DNOs**  | Distribution | Regional networks         | Various          | license_areas                     |

This structure allows you to easily distinguish between transmission-level wholesale market data (ELEXON), system operation data (NESO), and distribution network data (DNOs) for comprehensive UK electricity system analysis.
