def get_bm_market_kpis(bq_client, PROJECT_ID='inner-cinema-476211-u9', DATASET='uk_energy_prod'):
    """
    Get BM Market KPIs for today (48 periods):
    - Total £ (EBOCF bid + offer cashflow)
    - Total MWh (BOAV bid + offer volumes)
    - Net MWh (offer - bid from BOAV)
    - EWAP (Energy Weighted Average Price = cashflow ÷ volume)
    - Dispatch Intensity (acceptances per hour from BOALF)
    - Workhorse Index (active SPs / 48)
    
    Note: EBOCF/BOAV data typically lags by 1-2 days for settlement finalization
    """
    import pandas as pd
    import logging
    
    query = f"""
    WITH 
    -- Cashflows (EBOCF): Total £ spent/earned
    cashflows AS (
      SELECT
        settlementPeriod as period,
        SUM(CASE WHEN _direction = 'offer' THEN totalCashflow ELSE 0 END) as offer_cashflow_gbp,
        SUM(CASE WHEN _direction = 'bid' THEN ABS(totalCashflow) ELSE 0 END) as bid_cashflow_gbp,
        COUNT(DISTINCT bmUnit) as active_units_cf
      FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    ),
    -- Volumes (BOAV): Total MWh accepted
    volumes AS (
      SELECT
        settlementPeriod as period,
        SUM(CASE WHEN _direction = 'offer' THEN totalVolumeAccepted ELSE 0 END) as offer_mwh,
        SUM(CASE WHEN _direction = 'bid' THEN totalVolumeAccepted ELSE 0 END) as bid_mwh,
        COUNT(DISTINCT bmUnit) as active_units_vol
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boav`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    ),
    -- Acceptances (BOALF): Count for dispatch intensity
    acceptances AS (
      SELECT
        settlementPeriod as period,
        COUNT(DISTINCT acceptanceNumber) as acceptance_count,
        COUNT(DISTINCT bmUnit) as active_units_accept
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    )
    SELECT
      COALESCE(c.period, v.period, a.period) as period,
      -- Total cashflow (£)
      COALESCE(c.offer_cashflow_gbp, 0) as total_offer_gbp,
      COALESCE(c.bid_cashflow_gbp, 0) as total_bid_gbp,
      COALESCE(c.offer_cashflow_gbp, 0) + COALESCE(c.bid_cashflow_gbp, 0) as total_cashflow_gbp,
      -- Total volumes (MWh)
      COALESCE(v.offer_mwh, 0) as total_offer_mwh,
      COALESCE(v.bid_mwh, 0) as total_bid_mwh,
      COALESCE(v.offer_mwh, 0) + COALESCE(v.bid_mwh, 0) as total_volume_mwh,
      -- Net MWh (offer - bid)
      COALESCE(v.offer_mwh, 0) - COALESCE(v.bid_mwh, 0) as net_mwh,
      -- EWAP (Energy Weighted Average Price)
      CASE 
        WHEN COALESCE(v.offer_mwh, 0) > 0 
        THEN COALESCE(c.offer_cashflow_gbp, 0) / v.offer_mwh 
        ELSE 0 
      END as ewap_offer,
      CASE 
        WHEN COALESCE(v.bid_mwh, 0) > 0 
        THEN COALESCE(c.bid_cashflow_gbp, 0) / v.bid_mwh 
        ELSE 0 
      END as ewap_bid,
      -- Dispatch intensity (acceptances per hour = per 2 SPs)
      COALESCE(a.acceptance_count, 0) as acceptance_count,
      COALESCE(a.acceptance_count, 0) / 0.5 as acceptances_per_hour,
      -- Workhorse Index (active units)
      GREATEST(
        COALESCE(c.active_units_cf, 0),
        COALESCE(v.active_units_vol, 0),
        COALESCE(a.active_units_accept, 0)
      ) as active_units
    FROM cashflows c
    FULL OUTER JOIN volumes v ON c.period = v.period
    FULL OUTER JOIN acceptances a ON COALESCE(c.period, v.period) = a.period
    ORDER BY period
    """
    df = bq_client.query(query).to_dataframe()
    
    # If no data (likely because EBOCF/BOAV lag), return empty DataFrame
    if df.empty:
        logging.warning("⚠️  BM Market KPIs: No data available (EBOCF/BOAV typically lag 1-2 days)")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            'period', 'total_offer_gbp', 'total_bid_gbp', 'total_cashflow_gbp',
            'total_offer_mwh', 'total_bid_mwh', 'total_volume_mwh', 'net_mwh',
            'ewap_offer', 'ewap_bid', 'acceptance_count', 'acceptances_per_hour', 'active_units'
        ])
    
    return df
