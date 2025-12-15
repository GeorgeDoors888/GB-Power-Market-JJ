/**
 * Creates charts for the dashboard.
 */
function createCharts(sheet, data) {
  if (!data) return;

  // 1. CLEANUP: Remove all existing charts to prevent duplicates/random placement
  const charts = sheet.getCharts();
  for (let i = 0; i < charts.length; i++) {
    sheet.removeChart(charts[i]);
  }

  // KPI Sparklines
  // We need to target the merged ranges in Row 7 (which merges A7:B8, C7:D8, etc.)
  // Columns: 
  // 1 (A): VLP Revenue
  // 3 (C): Wholesale Price
  // 5 (E): Frequency
  // 7 (G): Total Gen
  // 9 (I): Wind Gen
  // 11 (K): Demand

  const kpiData = [
    data.intraday.price,  // For Wholesale Price (Col 3)
    data.intraday.wind,   // For Wind Gen (Col 9)
    data.intraday.demand  // For Demand (Col 11)
  ];
  
  // Map data indices to Sheet Columns
  // User requested Bar Charts (Column Charts) for Total Gen, Wind, and Demand
  const kpiMap = [
    { col: 3, data: data.intraday.price, color: '#e74c3c', type: 'column' },  // Price (Red Column)
    { col: 7, data: data.intraday.demand, color: '#f39c12', type: 'column' }, // Total Gen (Orange Column) - using demand data as proxy
    { col: 9, data: data.intraday.wind, color: '#2ecc71', type: 'column' },   // Wind (Green Column)
    { col: 11, data: data.intraday.demand, color: '#3498db', type: 'column' } // Demand (Blue Column)
  ];
  
  kpiMap.forEach(item => {
    if (item.data && item.data.length > 0) {
      const range = sheet.getRange(7, item.col, 1, 1); // Target top-left of merged range
      // Handle nulls by converting to 0 (safe for Sparklines)
      // Using 0 ensures the formula is valid: {1, 0, 3} instead of {1,,3}
      const safeData = item.data.map(v => v === null ? 0 : v);
      
      // Using "column" chart type for all to show HH profile
      range.setFormula(`=SPARKLINE({${safeData.join(',')}}, {"charttype","column";"color","${item.color}";"highcolor","${item.color}";"negcolor","#c0392b"})`);
    }
  });

  // Frequency Sparkline (Col 5) - Deviation from 50Hz
  // We want to show when frequency is going negative (<50) and positive (>50)
  if (data.intraday.frequency && data.intraday.frequency.length > 0) {
    // Calculate deviation: val - 50. Handle nulls (missing future data)
    // Using 0 for missing data (implies 50Hz / no deviation) to prevent formula errors
    const freqDeviation = data.intraday.frequency.map(f => f === null ? 0 : (f - 50).toFixed(3));
    const freqRange = sheet.getRange(7, 5, 1, 1);
    // Use column chart with negcolor
    // Positive (Green) = >50Hz, Negative (Red) = <50Hz
    freqRange.setFormula(`=SPARKLINE({${freqDeviation.join(',')}}, {"charttype","column";"color","#2ecc71";"negcolor","#e74c3c";"axis",true})`);
  }


  // Generation Mix Chart (Bar Chart instead of Pie)
  // REMOVED as per user request (data is in table)


  // Intraday Charts
  if (data.intraday.price && data.intraday.price.length > 0) {
    // Create temporary data for chart
    const tempData = data.intraday.price.map((price, i) => [i + 1, price]);
    const tempRange = sheet.getRange(35, 1, tempData.length, 2); // Move down to 35
    tempRange.setValues(tempData);
    tempRange.setFontColor('#ffffff'); // Hide data
    
    const priceChart = sheet.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(tempRange)
      .setPosition(35, 4, 0, 0)
      .setOption('title', 'Intraday Price (£/MWh)')
      .setOption('legend', {position: 'none'})
      .setOption('hAxis', {title: 'Settlement Period'})
      .setOption('vAxis', {title: 'Price (£/MWh)'})
      .build();
    
    sheet.insertChart(priceChart);
  }

  // Wind Analysis Chart (New)
  if (data.intraday.wind && data.intraday.wind.length > 0) {
    const length = Math.max(data.intraday.wind.length, (data.intraday.windForecast || []).length);
    const windData = [];
    
    // [Period, Actual, Forecast]
    for (let i = 0; i < length; i++) {
      windData.push([
        i + 1, 
        data.intraday.wind[i] || null, 
        (data.intraday.windForecast || [])[i] || null
      ]);
    }

    // Store hidden data in Column Z (26) to be completely out of the way
    const windRange = sheet.getRange(35, 26, windData.length, 3); 
    windRange.setValues(windData);
    windRange.setFontColor('#ffffff'); // Hide data

    const windChart = sheet.newChart()
      .setChartType(Charts.ChartType.COMBO)
      .addRange(windRange)
      .setPosition(32, 1, 0, 0) // Position at A32 (under Wind Analysis header)
      .setOption('title', '🌬️ Intraday Wind: Actual vs Forecast (GW)')
      .setOption('series', {
        0: {labelInLegend: 'Actual', color: '#2ecc71', type: 'area'},
        1: {labelInLegend: 'Forecast', color: '#3498db', type: 'line', lineDashStyle: [4, 4]}
      })
      .setOption('legend', {position: 'top'})
      .setOption('hAxis', {title: 'Settlement Period'})
      .setOption('vAxis', {title: 'GW'})
      .build();
    
    sheet.insertChart(windChart);
  }
}

