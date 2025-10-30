🏆 COMPLETE BMRS DATASET INVENTORY
================================================================================
📊 Total Tables: 54
📈 Total Rows: 1,642,834,296
💾 Total Size: 288.5 GB

💰 Market & Trading Data
------------------------------------------------------------
✅ BOD          |  863,639,555 rows |  78351.7 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_bod
   📝 Bid Offer Data
   📄 All bids and offers submitted to the balancing mechanism for energy trading
   🔄 Real-time
   📜 Schema:
             column_name data_type
                 dataset    STRING
          settlementDate      DATE
        settlementPeriod     INT64
                timeFrom TIMESTAMP
                  timeTo TIMESTAMP
      bidOfferPairNumber     INT64
                bidPrice   NUMERIC
              offerPrice   NUMERIC
                  volume   NUMERIC
      nationalGridBmUnit    STRING
                  bmUnit    STRING
                _dataset    STRING
        _window_from_utc TIMESTAMP
          _window_to_utc TIMESTAMP
           _ingested_utc TIMESTAMP
         _source_columns    STRING
             _source_api    STRING
       _hash_source_cols    STRING
               _hash_key    STRING

✅ BOALF        |    9,286,678 rows |    943.1 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_boalf
   📝 Bid Offer Acceptance Level Flagged
   📄 Acceptance/rejection status of bids and offers submitted to the balancing mechanism
   🔄 Real-time
   📜 Schema:
         column_name data_type
             dataset    STRING
      settlementDate      DATE
    settlementPeriod     INT64
            timeFrom TIMESTAMP
              timeTo TIMESTAMP
           levelFrom     INT64
             levelTo     INT64
    notificationTime TIMESTAMP
notificationSequence     INT64
  nationalGridBmUnit    STRING
              bmUnit    STRING
            _dataset    STRING
    _window_from_utc TIMESTAMP
      _window_to_utc TIMESTAMP
       _ingested_utc TIMESTAMP
     _source_columns    STRING
         _source_api    STRING
   _hash_source_cols    STRING
           _hash_key    STRING

✅ IMBALNGC     |    1,059,282 rows |     46.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_imbalngc
   📝 Imbalance Prices at National Grid Company
   📄 System buy and sell prices for energy imbalances
   🔄 Settlement periods
   📜 Schema:
     column_name data_type
         dataset    STRING
          margin   NUMERIC
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
        boundary    STRING
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ QAS          |   11,409,393 rows |    568.3 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_qas
   📝 Balancing Services Adjustment Data
   📄 Balancing services costs and adjustments by service type
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
            amount   NUMERIC
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ DISBSAD      |    1,841,252 rows |    531.0 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_disbsad
   📝 Disbursement Schedule of Balancing Services Adjustment Data
   📄 System operator disbursements for balancing services and grid management
   🔄 Daily
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
    forecastDate      DATE
          margin   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ NETBSAD      |      234,279 rows |     28.0 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_netbsad
   📝 Net Balancing Services Adjustment Data
   📄 Net adjustments for balancing services costs
   🔄 Settlement periods
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
          margin   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ MID          |      625,197 rows |     30.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_mid
   📝 Market Index Data
   📄 Price indices and market reference data
   🔄 Daily
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
    forecastDate      DATE
           price   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP


⚡ Real-time System Data
------------------------------------------------------------
✅ FREQ         |   19,218,692 rows |    365.8 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_freq
   📝 System Frequency
   📄 Real-time GB electricity system frequency measurements
   🔄 2-second intervals
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
       spot_time TIMESTAMP
       frequency   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ FUELINST     |       13,600 rows |      4.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_fuelinst
   📝 Instantaneous Fuel Mix
   📄 Real-time generation breakdown by fuel type (coal, gas, nuclear, renewables)
   🔄 5 minutes
   📜 Schema:
      column_name data_type
          dataset    STRING
      publishTime TIMESTAMP
         fuelType    STRING
       generation   NUMERIC
         _dataset    STRING
 _window_from_utc TIMESTAMP
   _window_to_utc TIMESTAMP
    _ingested_utc TIMESTAMP
  _source_columns    STRING
      _source_api    STRING
_hash_source_cols    STRING
        _hash_key    STRING

✅ FUELHH       |    1,422,520 rows |     50.2 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_fuelhh
   📝 Half Hourly Fuel Mix
   📄 Generation by fuel type aggregated to half-hourly periods
   🔄 30 minutes
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
        fuelType    STRING
      generation   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP


📊 Demand & Generation
------------------------------------------------------------
✅ INDDEM       |    1,030,932 rows |     41.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_inddem
   📝 Initial National Demand Forecast
   📄 Initial demand forecasts for the GB electricity system
   🔄 Daily
   📜 Schema:
     column_name data_type
         dataset    STRING
          demand   NUMERIC
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
        boundary    STRING
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ INDGEN       |    1,058,706 rows |     43.3 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_indgen
   📝 Initial National Generation Forecast
   📄 Initial generation forecasts for the GB electricity system
   🔄 Daily
   📜 Schema:
     column_name data_type
         dataset    STRING
      generation   NUMERIC
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
        boundary    STRING
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ INDO         |          968 rows |      0.0 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_indo
   📝 Initial National Demand Outturn
   📄 Actual initial demand outturn data
   🔄 Settlement periods
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
          demand   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ ITSDO        |          968 rows |      0.0 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_itsdo
   📝 Initial Transmission System Demand Outturn
   📄 Initial transmission system demand actuals
   🔄 Settlement periods
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
          demand   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ TSDF         |    1,054,134 rows |     39.8 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_tsdf
   📝 Transmission System Demand Forecast
   📄 Forecasts of transmission system demand
   🔄 Regular updates
   📜 Schema:
     column_name data_type
         dataset    STRING
          demand   NUMERIC
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
        boundary    STRING
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ TSDFD        |        9,178 rows |      0.3 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_tsdfd
   📝 Transmission System Demand Forecast Daily
   📄 Daily transmission system demand forecasts
   🔄 Daily
   📜 Schema:
      column_name data_type
          dataset    STRING
      publishTime TIMESTAMP
     forecastDate      DATE
           demand   NUMERIC
         _dataset    STRING
 _window_from_utc TIMESTAMP
   _window_to_utc TIMESTAMP
    _ingested_utc TIMESTAMP
  _source_columns    STRING
      _source_api    STRING
_hash_source_cols    STRING
        _hash_key    STRING

✅ TSDFW        |       49,470 rows |      1.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_tsdfw
   📝 Transmission System Demand Forecast Weekly
   📄 Weekly transmission system demand forecasts
   🔄 Weekly
   📜 Schema:
      column_name data_type
          dataset    STRING
      publishTime TIMESTAMP
             year     INT64
             week     INT64
           demand   NUMERIC
         _dataset    STRING
 _window_from_utc TIMESTAMP
   _window_to_utc TIMESTAMP
    _ingested_utc TIMESTAMP
  _source_columns    STRING
      _source_api    STRING
_hash_source_cols    STRING
        _hash_key    STRING


🌪️ Forecasting Data
------------------------------------------------------------
✅ NDF          |       47,572 rows |      1.6 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ndf
   📝 National Demand Forecast
   📄 Updated national demand forecasts
   🔄 Multiple daily updates
   📜 Schema:
     column_name data_type
         dataset    STRING
          demand   NUMERIC
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
        boundary    STRING
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ NDFD         |        9,841 rows |      0.3 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ndfd
   📝 National Demand Forecast Daily
   📄 Daily national demand forecasts
   🔄 Daily
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
    forecastDate      DATE
          demand   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ NDFW         |       49,317 rows |      1.8 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ndfw
   📝 National Demand Forecast Weekly
   📄 Weekly national demand forecasts
   🔄 Weekly
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
            year     INT64
            week     INT64
          demand   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ WINDFOR      |       51,830 rows |      1.7 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_windfor
   📝 Wind Generation Forecast
   📄 Forecasts of wind generation output
   🔄 Regular updates
   📜 Schema:
      column_name data_type
          dataset    STRING
      publishTime TIMESTAMP
        startTime TIMESTAMP
       generation   NUMERIC
         _dataset    STRING
 _window_from_utc TIMESTAMP
   _window_to_utc TIMESTAMP
    _ingested_utc TIMESTAMP
  _source_columns    STRING
      _source_api    STRING
_hash_source_cols    STRING
        _hash_key    STRING


🏭 Unit Performance
------------------------------------------------------------
✅ UOU2T3YW     |  244,377,030 rows |  15308.7 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_uou2t3yw
   📝 Unit Output Unit Data (3 Year Window)
   📄 Historical unit output data over 3-year rolling window
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
          fuelType    STRING
nationalGridBmUnit    STRING
            bmUnit    STRING
       publishTime TIMESTAMP
              week     INT64
              year     INT64
      outputUsable    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ UOU2T14D     |   20,502,170 rows |   1124.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_uou2t14d
   📝 Unit Output Unit Data (14 Day Window)
   📄 Unit output data over 14-day rolling window
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
          fuelType    STRING
nationalGridBmUnit    STRING
            bmUnit    STRING
       publishTime TIMESTAMP
      forecastDate      DATE
      outputUsable    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ FOU2T3YW     |    1,669,815 rows |    122.2 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_fou2t3yw
   📝 Forecast Output Unit Data (3 Year Window)
   📄 Historical forecast output data over 3-year rolling window
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
          fuelType    STRING
       publishTime TIMESTAMP
        systemZone    STRING
calendarWeekNumber     INT64
              year     INT64
      outputUsable    STRING
       biddingZone    STRING
interconnectorName    STRING
    interconnector      BOOL
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ FOU2T14D     |      117,819 rows |      9.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_fou2t14d
   📝 Forecast Output Unit Data (14 Day Window)
   📄 Forecast output data over 14-day rolling window
   🔄 Settlement periods
   📜 Schema:
         column_name data_type
             dataset    STRING
            fuelType    STRING
         publishTime TIMESTAMP
          systemZone    STRING
        forecastDate      DATE
forecastDateTimezone    STRING
        outputUsable    STRING
         biddingZone    STRING
  interconnectorName    STRING
      interconnector      BOOL
            _dataset    STRING
    _window_from_utc TIMESTAMP
      _window_to_utc TIMESTAMP
       _ingested_utc TIMESTAMP

✅ NOU2T3YW     |       73,935 rows |      3.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_nou2t3yw
   📝 Notice Output Unit Data (3 Year Window)
   📄 Historical notice data over 3-year rolling window
   🔄 As submitted
   📜 Schema:
       column_name data_type
           dataset    STRING
       publishTime TIMESTAMP
        systemZone    STRING
calendarWeekNumber     INT64
              year     INT64
      outputUsable    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ NOU2T14D     |        7,371 rows |      0.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_nou2t14d
   📝 Notice Output Unit Data (14 Day Window)
   📄 Notice data over 14-day rolling window
   🔄 As submitted
   📜 Schema:
         column_name data_type
             dataset    STRING
         publishTime TIMESTAMP
          systemZone    STRING
        forecastDate      DATE
forecastDateTimezone    STRING
        outputUsable    STRING
            _dataset    STRING
    _window_from_utc TIMESTAMP
      _window_to_utc TIMESTAMP
       _ingested_utc TIMESTAMP


🔧 Technical Parameters
------------------------------------------------------------
✅ MELS         |  106,993,379 rows |  51864.8 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_mels
   📝 Marginal Energy Loss Stations
   📄 Marginal energy loss factors for individual power stations
   🔄 Half-hourly
   📜 Schema:
         column_name data_type
             dataset    STRING
      settlementDate      DATE
    settlementPeriod     INT64
            timeFrom TIMESTAMP
              timeTo TIMESTAMP
           levelFrom     INT64
             levelTo     INT64
    notificationTime TIMESTAMP
notificationSequence     INT64
  nationalGridBmUnit    STRING
              bmUnit    STRING
            _dataset    STRING
    _window_from_utc TIMESTAMP
      _window_to_utc TIMESTAMP
       _ingested_utc TIMESTAMP
     _source_columns    STRING
         _source_api    STRING
   _hash_source_cols    STRING
           _hash_key    STRING

✅ MILS         |  104,276,749 rows |  50350.3 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_mils
   📝 Marginal Imbalance Loss Stations
   📄 Marginal loss factors for balancing mechanism units
   🔄 Half-hourly
   📜 Schema:
         column_name data_type
             dataset    STRING
      settlementDate      DATE
    settlementPeriod     INT64
            timeFrom TIMESTAMP
              timeTo TIMESTAMP
           levelFrom     INT64
             levelTo     INT64
    notificationTime TIMESTAMP
notificationSequence     INT64
  nationalGridBmUnit    STRING
              bmUnit    STRING
            _dataset    STRING
    _window_from_utc TIMESTAMP
      _window_to_utc TIMESTAMP
       _ingested_utc TIMESTAMP
     _source_columns    STRING
         _source_api    STRING
   _hash_source_cols    STRING
           _hash_key    STRING

✅ MELNGC       |    1,057,860 rows |     43.3 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_melngc
   📝 Miscellaneous Energy Loss National Grid Company
   📄 Energy losses within the transmission system
   🔄 Settlement periods
   📜 Schema:
     column_name data_type
         dataset    STRING
          margin   NUMERIC
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
        boundary    STRING
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ RDRE         |       63,277 rows |      4.7 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_rdre
   📝 Run Down Rate Export
   📄 Maximum rate at which units can decrease export
   🔄 As submitted
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
             rate1   NUMERIC
            elbow2   NUMERIC
             rate2   NUMERIC
            elbow3   NUMERIC
             rate3   NUMERIC
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ RDRI         |           52 rows |      0.0 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_rdri
   📝 Run Down Rate Import
   📄 Maximum rate at which units can decrease import
   🔄 As submitted
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
             rate1   NUMERIC
            elbow2   NUMERIC
             rate2   NUMERIC
            elbow3   NUMERIC
             rate3   NUMERIC
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ RURE         |      397,241 rows |     34.0 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_rure
   📝 Run Up Rate Export
   📄 Maximum rate at which units can increase export
   🔄 As submitted
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
             rate1   NUMERIC
            elbow2   NUMERIC
             rate2   NUMERIC
            elbow3   NUMERIC
             rate3   NUMERIC
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ RURI         |        5,073 rows |      0.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ruri
   📝 Run Up Rate Import
   📄 Maximum rate at which units can increase import
   🔄 As submitted
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
             rate1   NUMERIC
            elbow2   NUMERIC
             rate2   NUMERIC
            elbow3   NUMERIC
             rate3   NUMERIC
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP


🚫 Constraints & Losses
------------------------------------------------------------
✅ OCNMF3Y      |      149,885 rows |      6.1 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ocnmf3y
   📝 Operational Constraints Notice Market Forecast (3 Year)
   📄 Operational constraints forecasts over 3-year window
   🔄 As required
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
            week     INT64
            year     INT64
         surplus   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ OCNMF3Y2     |      109,430 rows |      4.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ocnmf3y2
   📝 Operational Constraints Notice Market Forecast (3 Year Secondary)
   📄 Secondary operational constraints forecasts over 3-year window
   🔄 As required
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
            week     INT64
            year     INT64
          margin   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ OCNMFD       |       12,571 rows |      0.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ocnmfd
   📝 Operational Constraints Notice Market Forecast Daily
   📄 Daily operational constraints forecasts
   🔄 Daily
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
    forecastDate      DATE
         surplus   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ OCNMFD2      |       12,571 rows |      0.5 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ocnmfd2
   📝 Operational Constraints Notice Market Forecast Daily Secondary
   📄 Secondary daily operational constraints forecasts
   🔄 Daily
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
    forecastDate      DATE
          margin   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ SEL          |      607,034 rows |     41.2 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_sel
   📝 System Energy Loss
   📄 System-wide energy losses
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
             level     INT64
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ SIL          |      107,480 rows |      7.6 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_sil
   📝 System Imbalance Loss
   📄 System imbalance and associated losses
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
             level     INT64
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP


📡 Non-BM & Special
------------------------------------------------------------
✅ NONBM        |      311,968 rows |     11.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_nonbm
   📝 Non-Balancing Mechanism BMRA
   📄 Data for generators not participating in the balancing mechanism
   🔄 Half-hourly
   📜 Schema:
     column_name data_type
         dataset    STRING
     publishTime TIMESTAMP
       startTime TIMESTAMP
  settlementDate      DATE
settlementPeriod     INT64
      generation   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ TEMP         |       30,024 rows |      1.0 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_temp
   📝 Temperature Data
   📄 Temperature measurements from weather stations
   🔄 Regular intervals
   📜 Schema:
     column_name data_type
         dataset    STRING
 measurementDate      DATE
     publishTime TIMESTAMP
     temperature   NUMERIC
        _dataset    STRING
_window_from_utc TIMESTAMP
  _window_to_utc TIMESTAMP
   _ingested_utc TIMESTAMP

✅ MDV          |        1,319 rows |      0.1 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_mdv
   📝 Meter Data Version
   📄 Metering data versions and updates
   🔄 As required
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
         volumeMax   NUMERIC
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP


🌍 Transmission Zones
------------------------------------------------------------
✅ MZT          |      187,912 rows |     12.3 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_mzt
   📝 Market Zone Transmission
   📄 Market zone transmission data
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
         periodMin     INT64
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ MNZT         |      280,703 rows |     18.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_mnzt
   📝 Market National Zone Transmission
   📄 National market zone transmission data
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
         periodMin     INT64
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ NDZ          |      342,357 rows |     21.4 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ndz
   📝 National Demand Zone
   📄 Demand data by national zones
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
            notice    STRING
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ NTB          |       95,331 rows |      5.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_ntb
   📝 National Transmission Boundary
   📄 Transmission boundary flows and constraints
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
            notice    STRING
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ NTO          |       95,289 rows |      5.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_nto
   📝 National Transmission Outturn
   📄 Actual transmission system outturns
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
            notice    STRING
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP

✅ MDP          |        1,512 rows |      0.1 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_mdp
   📝 Market Domain Pricing
   📄 Market domain pricing data
   🔄 Settlement periods
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
         periodMax     INT64
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP


🔍 ADDITIONAL DATASETS
------------------------------
✅ bmrs_costs           |      130,824 rows |    176.2 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_costs
   📜 Schema:
                          column_name data_type
                       settlementDate TIMESTAMP
                     settlementPeriod     INT64
                            startTime TIMESTAMP
                      createdDateTime TIMESTAMP
                      systemSellPrice   FLOAT64
                       systemBuyPrice   FLOAT64
                        bsadDefaulted      BOOL
                  priceDerivationCode    STRING
                 reserveScarcityPrice   FLOAT64
                   netImbalanceVolume   FLOAT64
                  sellPriceAdjustment   FLOAT64
                   buyPriceAdjustment   FLOAT64
                     replacementPrice   FLOAT64
      replacementPriceReferenceVolume   FLOAT64
            totalAcceptedOfferVolume   FLOAT64
               totalAcceptedBidVolume   FLOAT64
            totalAdjustmentSellVolume   FLOAT64
             totalAdjustmentBuyVolume   FLOAT64
 totalSystemTaggedAcceptedOfferVolume   FLOAT64
   totalSystemTaggedAcceptedBidVolume   FLOAT64
totalSystemTaggedAdjustmentSellVolume   FLOAT64
 totalSystemTaggedAdjustmentBuyVolume   FLOAT64
                             _dataset    STRING
                     _window_from_utc TIMESTAMP
                       _window_to_utc TIMESTAMP
                        _ingested_utc TIMESTAMP
                      _source_columns    STRING
                          _source_api    STRING
                    _hash_source_cols    STRING
                            _hash_key    STRING
✅ bmrs_pn              |  131,856,258 rows |  50370.6 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_pn
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate TIMESTAMP
  settlementPeriod     INT64
          timeFrom TIMESTAMP
            timeTo TIMESTAMP
         levelFrom     INT64
           levelTo     INT64
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP
   _source_columns    STRING
       _source_api    STRING
 _hash_source_cols    STRING
         _hash_key    STRING
✅ bmrs_qpn             |  116,845,177 rows |  44827.9 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_qpn
   📜 Schema:
       column_name data_type
           dataset    STRING
    settlementDate TIMESTAMP
  settlementPeriod     INT64
          timeFrom TIMESTAMP
            timeTo TIMESTAMP
         levelFrom     INT64
           levelTo     INT64
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
  _window_from_utc TIMESTAMP
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP
   _source_columns    STRING
       _source_api    STRING
 _hash_source_cols    STRING
         _hash_key    STRING
✅ bmrs_rdri_new        |          810 rows |      0.0 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_rdri_new
   📜 Schema:
       column_name data_type
            elbow2   NUMERIC
       other_field    STRING
  _window_from_utc TIMESTAMP
           dataset    STRING
    settlementDate      DATE
  settlementPeriod     INT64
              time TIMESTAMP
             rate1   NUMERIC
             rate2   NUMERIC
            elbow3   NUMERIC
             rate3   NUMERIC
nationalGridBmUnit    STRING
            bmUnit    STRING
          _dataset    STRING
    _window_to_utc TIMESTAMP
     _ingested_utc TIMESTAMP
✅ bmrs_remit           |          706 rows |      0.3 MB
   📍 bq://jibber-jabber-knowledge/uk_energy_insights/bmrs_remit
   📜 Schema:
        column_name data_type
        publishTime TIMESTAMP
               mrid    STRING
     revisionNumber     INT64
        createdTime TIMESTAMP
        messageType    STRING
     messageHeading    STRING
          eventType    STRING
 unavailabilityType    STRING
      participantId    STRING
   registrationCode    STRING
            assetId    STRING
          assetType    STRING
       affectedUnit    STRING
    affectedUnitEIC    STRING
       affectedArea    STRING
        biddingZone    STRING
           fuelType    STRING
     normalCapacity   NUMERIC
  availableCapacity   NUMERIC
unavailableCapacity   NUMERIC
        eventStatus    STRING
     eventStartTime TIMESTAMP
       eventEndTime TIMESTAMP
              cause    STRING
 relatedInformation    STRING
            dataset    STRING
            _source    STRING
      _processed_at TIMESTAMP
      outageProfile ARRAY<STRUCT<startTime TIMESTAMP, endTime TIMESTAMP, capacity NUMERIC>>

🎯 ANALYSIS READY DATASETS
========================================
Your complete UK energy market data platform includes:
• Real-time electricity system monitoring
• Complete balancing mechanism trading data
• Generation and demand forecasting
• System constraints and losses
• Unit-level performance data
• Market pricing and adjustments

🚀 Ready for comprehensive energy market
