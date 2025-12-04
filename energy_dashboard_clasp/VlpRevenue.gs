/**
 * VLP Revenue Dashboard - BigQuery Integration
 * Queries v_btm_bess_inputs view for live revenue data
 */

const PROJECT_ID = 'inner-cinema-476211-u9';
const DATASET = 'uk_energy_prod';
const VIEW_NAME = 'v_btm_bess_inputs';

/**
 * Get latest VLP revenue data for current settlement period
 */
function getLatestVlpRevenue() {
  const query = `
    SELECT 
      settlementDate,
      settlementPeriod,
      ts_halfhour,
      duos_band,
      ssp_charge as market_price,
      bm_revenue_per_mwh,
      dc_revenue_per_mwh,
      dm_revenue_per_mwh,
      dr_revenue_per_mwh,
      cm_revenue_per_mwh,
      triad_value_per_mwh,
      ppa_price,
      total_stacked_revenue_per_mwh,
      total_cost_per_mwh,
      net_margin_per_mwh,
      trading_signal,
      negative_pricing
    FROM \`${PROJECT_ID}.${DATASET}.${VIEW_NAME}\`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 1
  `;
  
  try {
    const result = runBigQuery(query);
    if (result && result.length > 0) {
      return result[0];
    }
    return null;
  } catch (e) {
    console.error('Error fetching latest VLP revenue: ' + e.toString());
    return null;
  }
}

/**
 * Get last 48 periods (24 hours) for forecast chart
 */
function getLast48Periods() {
  const query = `
    SELECT 
      settlementDate,
      settlementPeriod,
      ts_halfhour,
      duos_band,
      ssp_charge as market_price,
      total_stacked_revenue_per_mwh as total_revenue,
      total_cost_per_mwh as total_cost,
      net_margin_per_mwh as profit,
      trading_signal
    FROM \`${PROJECT_ID}.${DATASET}.${VIEW_NAME}\`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 48
  `;
  
  try {
    const result = runBigQuery(query);
    return result || [];
  } catch (e) {
    console.error('Error fetching 48-period data: ' + e.toString());
    return [];
  }
}

/**
 * Get service breakdown for current period
 */
function getServiceBreakdown() {
  const latest = getLatestVlpRevenue();
  if (!latest) return null;
  
  return {
    'PPA Discharge': latest.ppa_price || 150.0,
    'DC (Dynamic Containment)': latest.dc_revenue_per_mwh || 78.75,
    'DM (Dynamic Moderation)': latest.dm_revenue_per_mwh || 40.29,
    'DR (Dynamic Regulation)': latest.dr_revenue_per_mwh || 60.44,
    'CM (Capacity Market)': latest.cm_revenue_per_mwh || 12.59,
    'BM (Balancing Mechanism)': latest.bm_revenue_per_mwh || 0.0,
    'Triad Avoidance': latest.triad_value_per_mwh || 0.0,
    'Negative Pricing': latest.negative_pricing ? latest.market_price : 0.0
  };
}

/**
 * Get stacking scenarios comparison
 */
function getStackingScenarios() {
  return [
    {
      scenario: 'Conservative',
      services: 'DC + CM + PPA',
      services_list: ['DC', 'CM', 'PPA'],
      annual_revenue: 599008,
      revenue_per_mwh: 241.34,
      risk: 'Low',
      description: 'Reliable base load revenue'
    },
    {
      scenario: 'Balanced',
      services: 'DC + DM + CM + PPA + BM',
      services_list: ['DC', 'DM', 'CM', 'PPA', 'BM'],
      annual_revenue: 749008,
      revenue_per_mwh: 301.78,
      risk: 'Medium',
      description: 'Multiple frequency services'
    },
    {
      scenario: 'Aggressive',
      services: 'DC + DM + DR + CM + PPA + BM + TRIAD',
      services_list: ['DC', 'DM', 'DR', 'CM', 'PPA', 'BM', 'TRIAD'],
      annual_revenue: 999008,
      revenue_per_mwh: 402.50,
      risk: 'High',
      description: 'Maximum revenue stack'
    },
    {
      scenario: 'Opportunistic',
      services: 'DC + CM + PPA + Negative Pricing',
      services_list: ['DC', 'CM', 'PPA', 'NEGATIVE'],
      annual_revenue: 624008,
      revenue_per_mwh: 251.41,
      risk: 'Low-Medium',
      description: 'Capture pricing events'
    }
  ];
}

/**
 * Get trading signals summary for last 48 periods
 */
function getTradingSignals() {
  const periods = getLast48Periods();
  if (!periods || periods.length === 0) return null;
  
  const signals = {
    'DISCHARGE_HIGH': 0,
    'DISCHARGE_MODERATE': 0,
    'CHARGE_CHEAP': 0,
    'CHARGE_PAID': 0,
    'HOLD': 0
  };
  
  let total_profit = 0;
  let profitable_periods = 0;
  
  periods.forEach(p => {
    if (p.trading_signal && signals.hasOwnProperty(p.trading_signal)) {
      signals[p.trading_signal]++;
    }
    total_profit += p.profit || 0;
    if (p.profit > 0) profitable_periods++;
  });
  
  return {
    signals: signals,
    avg_profit: total_profit / periods.length,
    profitable_pct: (profitable_periods / periods.length) * 100,
    total_periods: periods.length
  };
}

/**
 * Get cost breakdown for current period
 */
function getCostBreakdown() {
  const latest = getLatestVlpRevenue();
  if (!latest) return null;
  
  // Calculate DUoS based on band
  const duos_rates = {
    'RED': 17.64,
    'AMBER': 4.57,
    'GREEN': 1.11
  };
  
  const duos = duos_rates[latest.duos_band] || 1.11;
  const levies = 98.15; // Fixed levies
  
  return {
    market_price: latest.market_price || 0,
    duos: duos,
    tnuos: 12.50,
    bsuos: 4.50,
    ccl: 7.75,
    ro: 61.90,
    fit: 11.50,
    total_levies: levies,
    total_cost: (latest.market_price || 0) + duos + levies
  };
}

/**
 * Get profit analysis by DUoS band
 */
function getProfitByBand() {
  const query = `
    SELECT 
      duos_band,
      AVG(net_margin_per_mwh) as avg_profit,
      MIN(net_margin_per_mwh) as min_profit,
      MAX(net_margin_per_mwh) as max_profit,
      COUNT(*) as period_count
    FROM \`${PROJECT_ID}.${DATASET}.${VIEW_NAME}\`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY duos_band
    ORDER BY 
      CASE duos_band 
        WHEN 'GREEN' THEN 1 
        WHEN 'AMBER' THEN 2 
        WHEN 'RED' THEN 3 
      END
  `;
  
  try {
    return runBigQuery(query) || [];
  } catch (e) {
    console.error('Error fetching profit by band: ' + e.toString());
    return [];
  }
}

/**
 * Check for data quality issues
 */
function checkDataQuality() {
  const latest = getLatestVlpRevenue();
  if (!latest) {
    return { status: 'ERROR', message: 'No data available' };
  }
  
  const issues = [];
  
  // Check for zero prices
  if (latest.market_price === 0) {
    issues.push('⚠️ Zero market price detected');
  }
  
  // Check for stale data (>1 hour old)
  const dataAge = (new Date() - new Date(latest.ts_halfhour)) / (1000 * 60);
  if (dataAge > 60) {
    issues.push(`⚠️ Data is ${Math.round(dataAge)} minutes old`);
  }
  
  // Check for anomalous profits
  if (latest.net_margin_per_mwh < -100) {
    issues.push('⚠️ Very negative profit margin');
  }
  
  if (issues.length > 0) {
    return { status: 'WARNING', message: issues.join(', ') };
  }
  
  return { status: 'OK', message: '✅ Data quality good' };
}

/**
 * Service compatibility matrix
 */
function getServiceCompatibility() {
  return [
    { service1: 'DC', service2: 'DM', compatible: true, note: 'Different response speeds' },
    { service1: 'DC', service2: 'DR', compatible: true, note: 'Can co-exist' },
    { service1: 'DC', service2: 'BM', compatible: true, note: 'BM is discretionary' },
    { service1: 'DC', service2: 'CM', compatible: true, note: 'Availability + response' },
    { service1: 'DC', service2: 'PPA', compatible: true, note: 'Always compatible' },
    { service1: 'DC', service2: 'TRIAD', compatible: true, note: 'Different windows' },
    { service1: 'DM', service2: 'DR', compatible: true, note: 'Different response speeds' },
    { service1: 'DM', service2: 'BM', compatible: true, note: 'Can stack' },
    { service1: 'DR', service2: 'BM', compatible: false, note: '⚠️ Continuous vs discrete control conflict' },
    { service1: 'BM', service2: 'CM', compatible: true, note: 'BM participation OK' },
    { service1: 'TRIAD', service2: 'PPA', compatible: true, note: 'Discharge during peak' },
    { service1: 'NEGATIVE', service2: 'ALL', compatible: true, note: '✅ Compatible when charging' }
  ];
}
