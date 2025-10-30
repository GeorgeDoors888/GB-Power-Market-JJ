# 🔌 BMRS Transmission Layer Data - Comprehensive Breakdown

## 📊 **Total BMRS Data Volume**: 53 Datasets • 876+ Million Records • 172+ GB

---

## 🏗️ **Data Architecture Overview**

The BMRS (Balancing Mechanism Reporting Service) transmission layer contains **53 core datasets** representing the complete UK wholesale electricity market and transmission system operations.

---

## 📈 **Core Market Data** (High-Volume Trading Data)

### **1. BOD - Bid-Offer Data**
- **📊 Records**: 573,568,931 (573M records)
- **💾 Size**: 119.8 GB
- **📝 Description**: Every bid and offer submitted by power stations for balancing the grid
- **🔄 Frequency**: Real-time (minute-by-minute)
- **💰 Commercial Value**: Primary wholesale trading data showing generator pricing strategies

### **2. BOALF - Bid-Offer Acceptance Level (Final)**
- **📊 Records**: 3,829,376 (3.8M records)
- **💾 Size**: 912.4 MB
- **📝 Description**: Final accepted bids/offers used for actual grid balancing
- **🔄 Frequency**: Real-time acceptances
- **💰 Commercial Value**: Shows which generators were actually called upon and at what price

### **3. QAS - Quality Assurance**
- **📊 Records**: 7,702,009 (7.7M records)
- **💾 Size**: 1.1 GB
- **📝 Description**: Data quality monitoring and validation metrics for market data
- **🔄 Frequency**: Continuous validation
- **💰 Commercial Value**: Ensures data integrity for financial settlements

---

## ⚡ **System Operations** (Grid Stability & Control)

### **4. FREQ - Frequency Data**
- **📊 Records**: 19,172,608 (19M records)
- **💾 Size**: 2.3 GB
- **📝 Description**: Real-time grid frequency measurements (target: 50Hz)
- **🔄 Frequency**: Sub-second measurements
- **⚡ System Value**: Critical indicator of supply-demand balance

### **5. MILS - Market Index Level (Settlement)**
- **📊 Records**: 5,001,668 (5M records)
- **💾 Size**: 2.9 GB
- **📝 Description**: Settlement period market index pricing for imbalance calculations
- **🔄 Frequency**: Half-hourly settlement periods
- **💰 Commercial Value**: Primary pricing reference for imbalance charges

### **6. MELS - Market Index Level (Energy)**
- **📊 Records**: 772,539 records
- **💾 Size**: 455.8 MB
- **📝 Description**: Energy market index prices and volumes
- **🔄 Frequency**: Half-hourly
- **💰 Commercial Value**: Energy market pricing reference

---

## 🔥 **Generation & Fuel Data** (Power Station Operations)

### **7. FUELINST - Fuel Type Instructions**
- **📊 Records**: 2,451,640 (2.4M records)
- **💾 Size**: 438.0 MB
- **📝 Description**: Real-time fuel type generation levels and dispatch instructions
- **🔄 Frequency**: Real-time operational data
- **🌍 Environmental Value**: Shows renewable vs fossil fuel generation mix

### **8. FUELHH - Fuel Type Half-Hourly**
- **📊 Records**: 303,240 records
- **💾 Size**: 53.0 MB
- **📝 Description**: Half-hourly generation by fuel type (Coal, Gas, Wind, Nuclear, etc.)
- **🔄 Frequency**: Every 30 minutes
- **🌍 Environmental Value**: Historical fuel mix for carbon analysis

### **9. WINDFOR - Wind Forecasts**
- **📊 Records**: 22,338 records
- **💾 Size**: 3.4 MB
- **📝 Description**: Wind generation forecasts for renewable planning
- **🔄 Frequency**: Daily forecasts
- **🌍 Environmental Value**: Renewable energy prediction and planning

---

## 🏭 **Unit-Level Data** (Individual Power Station Performance)

### **10. UOU2T3YW - Unit Output (2-52 weeks ahead)**
- **📊 Records**: 244,233,190 (244M records)
- **💾 Size**: 40.9 GB
- **📝 Description**: Individual power station output forecasts up to 1 year ahead
- **🔄 Frequency**: Weekly planning cycles
- **📊 Planning Value**: Long-term capacity and maintenance planning

### **11. UOU2T14D - Unit Output (2-14 days ahead)**
- **📊 Records**: 20,484,074 (20M records)
- **💾 Size**: 3.3 GB
- **📝 Description**: Medium-term individual unit output forecasts
- **🔄 Frequency**: Daily planning updates
- **📊 Planning Value**: Operational planning and scheduling

---

## 📊 **Demand & Forecasting** (System Load Planning)

### **12. INDDEM - Individual Demand**
- **📊 Records**: 539,262 records
- **💾 Size**: 92.8 MB
- **📝 Description**: Individual demand forecasts by region/zone
- **🔄 Frequency**: Half-hourly forecasts
- **📊 Planning Value**: Regional demand planning

### **13. NDF - National Demand Forecast**
- **📊 Records**: 17,406 records
- **💾 Size**: 2.9 MB
- **📝 Description**: National electricity demand forecasts
- **🔄 Frequency**: Day-ahead and weekly forecasts
- **📊 Planning Value**: System-wide demand planning

### **14. TEMP - Temperature Forecasts**
- **📊 Records**: 17,548 records
- **💾 Size**: 2.4 MB
- **📝 Description**: Weather temperature predictions for demand correlation
- **🔄 Frequency**: Daily meteorological forecasts
- **🌡️ Weather Value**: Heating/cooling demand correlation

---

## 💰 **Financial & Settlement** (Market Pricing & Costs)

### **15. IMBALNGC - Imbalance NGC**
- **📊 Records**: 566,226 records
- **💾 Size**: 99.6 MB
- **📝 Description**: Imbalance settlement data and National Grid costs
- **🔄 Frequency**: Half-hourly settlement
- **💰 Financial Value**: System balancing cost allocation

### **16. MELNGC - Market Energy Level NGC**
- **📊 Records**: 566,208 records
- **💾 Size**: 97.4 MB
- **📝 Description**: Market energy levels and National Grid pricing
- **🔄 Frequency**: Half-hourly market periods
- **💰 Financial Value**: Energy market pricing and volume data

### **17. DISBSAD - Disaggregated Balancing Services Adjustment Data**
- **📊 Records**: 1,464,784 (1.4M records)
- **💾 Size**: 146.0 MB
- **📝 Description**: Detailed breakdown of balancing services costs
- **🔄 Frequency**: Half-hourly cost allocation
- **💰 Financial Value**: Granular balancing cost analysis

---

## 🚨 **System Alerts & Constraints** (Grid Security)

### **18. TSDF - Transmission System Demand Forecast**
- **📊 Records**: 548,730 records
- **💾 Size**: 92.3 MB
- **📝 Description**: Transmission system demand forecasting data
- **🔄 Frequency**: Regular forecasting cycles
- **⚡ System Value**: Transmission planning and capacity management

### **19. NETBSAD - Net Balancing Services Adjustment Data**
- **📊 Records**: 167,443 records
- **💾 Size**: 30.3 MB
- **📝 Description**: Net balancing services costs and adjustments
- **🔄 Frequency**: Daily settlement summaries
- **💰 Financial Value**: Daily balancing cost summaries

---

## 🔍 **Additional Specialized Datasets** (35+ more tables)

The remaining 35+ datasets include:
- **Outage data** (planned and unplanned generation unavailability)
- **Reserve requirements** (system security margins)
- **Interconnector flows** (international electricity trade)
- **Reactive power** (voltage control services)
- **System warnings** (grid stability alerts)
- **Market index variations** (pricing volatility measures)
- **Forecast accuracies** (prediction vs actual performance)

---

## 🎯 **Data Usage Categories**

### **Real-Time Operations** (Sub-minute data)
- Grid frequency monitoring
- Bid-offer acceptances
- Emergency response data

### **Market Trading** (Minute-by-minute)
- Bid-offer submissions
- Price formation
- Volume transactions

### **Settlement** (Half-hourly)
- Market clearing prices
- Imbalance calculations
- Cost allocations

### **Planning** (Daily/Weekly/Annual)
- Demand forecasts
- Generation planning
- Maintenance scheduling

---

## 💡 **Key Insights**

1. **Market Complexity**: 573M bid-offer records show the intense competition in UK electricity markets
2. **System Stability**: 19M frequency measurements demonstrate continuous grid monitoring
3. **Renewable Integration**: Wind forecasts and fuel mix data track the energy transition
4. **Financial Scale**: Multi-gigabyte datasets reflect billion-pound daily electricity trading
5. **Operational Precision**: Sub-second data collection ensures grid reliability

This BMRS transmission data represents the **most comprehensive view of UK electricity wholesale markets and transmission operations available**, providing unprecedented insight into how Britain's electricity system operates in real-time.

---

**🔗 Integration Ready**: All 53 datasets are integrated in BigQuery `uk_energy_insights` for cross-analysis with UKPN distribution data and NESO system operation data.
