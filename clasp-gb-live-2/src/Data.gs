const PUBLICATION_TABLE_ID = 'publication_dashboard_live';

/**
 * Fetches data from the publication table.
 */
function fetchData() {
  const query = `SELECT * FROM \`${PROJECT_ID}.${DATASET}.${PUBLICATION_TABLE_ID}\` LIMIT 1`;
  
  Logger.log('Querying: ' + query);
  const results = executeBigQuery(query);

  if (!results || results.length === 0) {
    Logger.log('Error: Publication table is empty');
    return null;
  }

  const row = results[0].f;
  
  const data = {
    reportDate: row[0].v,
    kpis: {
      vlpRevenue: parseFloat(row[1].v || '0').toFixed(2),
      wholesaleAvg: parseFloat(row[2].v || '0').toFixed(2),
      frequency: parseFloat(row[3].v || '50.0').toFixed(2),
      totalGen: parseFloat(row[4].v || '0').toFixed(2),
      windGen: parseFloat(row[5].v || '0').toFixed(2),
      demand: parseFloat(row[6].v || '0').toFixed(2)
    },
    generationMix: (row[7].v || []).map(item => [
      addFuelEmoji(item.v.f[0].v),
      parseFloat((parseFloat(item.v.f[1].v) / 1000).toFixed(1))
    ]),
    interconnectors: (row[8].v || []).map(item => [
      addInterconnectorFlag(item.v.f[0].v),
      parseFloat(item.v.f[1].v)
    ]),
    intraday: {
      wind: (row[9].v || []).map(val => { const v = parseFloat(val.v); return v === -999 ? null : v; }),
      windForecast: (row[10].v || []).map(val => { const v = parseFloat(val.v); return v === -999 ? null : v; }),
      demand: (row[11].v || []).map(val => { const v = parseFloat(val.v); return v === -999 ? null : v; }),
      price: (row[12].v || []).map(val => { const v = parseFloat(val.v); return v === -999 ? null : v; }),
      frequency: (row[13].v || []).map(val => { const v = parseFloat(val.v); return v === -999 ? null : v; })
    },
    outages: (row[14].v || []).map(item => ({
      assetName: item.v.f[0].v,
      fuelType: addFuelEmoji(item.v.f[1].v),
      unavailMw: parseFloat(item.v.f[2].v),
      cause: item.v.f[3].v
    })),
    constraintAnalysis: (row[15].v || []).map(item => {
      if (!item.v || !item.v.f) return null;
      return {
        region: item.v.f[0].v,
        dnoArea: item.v.f[1].v,
        gspGroup: item.v.f[2].v,
        fuelGroup: item.v.f[3].v,
        nActions: parseInt(item.v.f[4].v),
        totalMwAdjusted: parseFloat(item.v.f[5].v),
        shareOfTotalPct: parseFloat(item.v.f[6].v)
      };
    }).filter(item => item !== null)
  };
  
  Logger.log('Successfully parsed data');
  return data;
}

/**
 * Adds emoji to fuel type.
 */
function addFuelEmoji(fuelType) {
  if (!fuelType) return '';
  const ft = fuelType.toString().toUpperCase();
  
  // Direct Map for Standard Codes
  const map = {
    'WIND': '🌬️ WIND',
    'NUCLEAR': '⚛️ NUCLEAR',
    'CCGT': '🏭 CCGT',
    'BIOMASS': '🌿 BIOMASS',
    'INTFR': '🇫🇷 INTFR',
    'INTELEC': '🇫🇷 INTELEC',
    'INTIFA2': '🇫🇷 INTIFA2',
    'NPSHYD': '💧 NPSHYD',
    'OTHER': '❓ OTHER',
    'INTVKL': '🇩🇰 INTVKL',
    'INTGRNL': '🇮🇪 INTGRNL',
    'OCGT': '🛢️ OCGT',
    'INTEW': '🇮🇪 INTEW',
    'COAL': '🪨 COAL',
    'OIL': '🛢️ OIL',
    'INTIRL': '🇮🇪 INTIRL',
    'INTNED': '🇳🇱 INTNED',
    'INTNEM': '🇧🇪 INTNEM',
    'INTNSL': '🇳🇴 INTNSL',
    'PS': '🔋 PS'
  };
  
  if (map[ft]) return map[ft];

  // Fuzzy Match for Constraint Analysis
  if (ft.includes('WIND')) return '🌬️ ' + fuelType;
  if (ft.includes('CCGT') || ft.includes('GAS')) return '🏭 ' + fuelType;
  if (ft.includes('NUCLEAR')) return '⚛️ ' + fuelType;
  if (ft.includes('BIOMASS')) return '🌿 ' + fuelType;
  if (ft.includes('HYDRO') || ft.includes('NPSHYD')) return '💧 ' + fuelType;
  if (ft.includes('PS') || ft.includes('PUMPED')) return '🔋 ' + fuelType;
  if (ft.includes('COAL')) return '🪨 ' + fuelType;
  if (ft.includes('SOLAR')) return '☀️ ' + fuelType;
  if (ft.includes('OTHER')) return '❓ ' + fuelType;
  if (ft.includes('INTERCONNECTOR')) return '🌍 ' + fuelType;

  return fuelType;
}

/**
 * Maps GSP Group ID to Name.
 */
function getGspGroupName(gspId) {
  const map = {
    '_P': 'North Scotland (SHEPD)',
    '_N': 'South Scotland (SP)',
    '_A': 'Eastern England',
    '_B': 'East Midlands',
    '_C': 'London',
    '_D': 'North Wales & Merseyside',
    '_E': 'West Midlands',
    '_F': 'North East England',
    '_G': 'North West England',
    '_H': 'Southern England',
    '_J': 'South East England',
    '_K': 'South Wales',
    '_L': 'South West England',
    '_M': 'Yorkshire'
  };
  return map[gspId] || gspId;
}

/**
 * Adds flag to interconnector name.
 */
function addInterconnectorFlag(name) {
  const map = {
    'ElecLink': '🇫🇷 ElecLink',
    'East-West': '🇮🇪 East-West',
    'IFA': '🇫🇷 IFA',
    'Greenlink': '🇮🇪 Greenlink',
    'IFA2': '🇫🇷 IFA2',
    'Moyle': '🇮🇪 Moyle',
    'BritNed': '🇳🇱 BritNed',
    'Nemo': '🇧🇪 Nemo',
    'NSL': '🇳🇴 NSL',
    'Viking Link': '🇩🇰 Viking Link'
  };
  return map[name] || name;
}

/**
 * Displays data on the sheet.
 */
function displayData(sheet, data) {
  if (!data) return;

  const sheetName = sheet.getName();
  const isV2 = sheetName.toLowerCase().includes('v2');
  Logger.log('Displaying data. Sheet: ' + sheetName + ', isV2: ' + isV2);

  // Display KPIs
  const kpiValues = [
    data.kpis.vlpRevenue,
    data.kpis.wholesaleAvg,
    data.kpis.frequency,
    data.kpis.totalGen,
    data.kpis.windGen,
    data.kpis.demand
  ];

  for (let i = 0; i < kpiValues.length; i++) {
    const col = i * 2 + 1;
    sheet.getRange(6, col).setValue(kpiValues[i]);
  }

  // Display generation mix
  if (data.generationMix && data.generationMix.length > 0) {
    // Both v1 and v2 use cols A and B for Gen Mix
    sheet.getRange(13, 1, data.generationMix.length, 2).setValues(data.generationMix);

    // Add Sparkline Bars in Column C (Share of Total)
    const totalGen = parseFloat(data.kpis.totalGen);
    const formulas = data.generationMix.map((row, i) => {
      const sheetRow = 13 + i;
      const val = parseFloat(row[1]);
      const color = val < 0 ? "#e74c3c" : "#3498db"; // Red if negative, Blue if positive
      Logger.log(`Row ${i}: ${row[0]} = ${val} GW. Color: ${color}`);
      return [`=SPARKLINE(ABS(B${sheetRow}), {"charttype","bar";"max",${totalGen};"color1","${color}"})`];
    });
    sheet.getRange(13, 3, formulas.length, 1).setFormulas(formulas);
  }

  // Display interconnectors
  if (data.interconnectors && data.interconnectors.length > 0) {
    if (isV2) {
      // v2 Layout:
      // Col G: Connection Name
      // Col H-I (Merged): Sparkline Graphic
      // Col J: Flow Value (MW)
      
      // 1. Write Names to G and Values to J
      const v2InterData = data.interconnectors.map(row => [row[0], '', '', row[1]]); // G, H, I, J
      sheet.getRange(13, 7, v2InterData.length, 4).setValues(v2InterData);

      // 2. Write Sparklines to H (which fills H-I merge)
      const interFormulas = data.interconnectors.map((row, i) => {
        const sheetRow = 13 + i;
        const val = parseFloat(row[1]); // Flow value
        // Green if Import (>=0), Red if Export (<0)
        const color = val >= 0 ? "#2ecc71" : "#e74c3c"; 
        // Max capacity ~2000MW (IFA) - using ABS(J) for magnitude
        return [`=SPARKLINE(ABS(J${sheetRow}), {"charttype","bar";"max",2000;"color1","${color}"})`];
      });
      sheet.getRange(13, 8, interFormulas.length, 1).setFormulas(interFormulas);

    } else {
      // v1: Connection in D (col 4), Flow in E (col 5)
      sheet.getRange(13, 4, data.interconnectors.length, 2).setValues(data.interconnectors);
    }
  }

  // Display Outages (v2 only)
  if (isV2 && data.outages && data.outages.length > 0) {
    // Outages start at row 32 (below Wind Analysis header at 30)
    // Move to Right Side (Column G) to avoid Chart on Left
    
    // Clear previous outages first
    sheet.getRange('G32:L50').clearContent();
    
    // Headers
    sheet.getRange('G31:J31').setValues([['Asset Name', 'Fuel Type', 'Unavail (MW)', 'Cause']]);
    sheet.getRange('G31:J31').setFontWeight('bold').setBackground('#ecf0f1');
    
    const outageData = data.outages.map(o => [o.assetName, o.fuelType, o.unavailMw, o.cause]);
    sheet.getRange(32, 7, outageData.length, 4).setValues(outageData);
  }

  // Display Constraint Analysis (v2 only)
  if (isV2 && data.constraintAnalysis && data.constraintAnalysis.length > 0) {
    // Start at Row 55
    const startRow = 55;
    
    // Clear previous data
    sheet.getRange(startRow, 1, 25, 8).clearContent(); // Cleared 8 cols

    // Headers
    const headers = [['Region', 'DNO Area', 'GSP Group', 'Fuel', 'Actions', 'Total MW', '% Share', 'Visual']];
    sheet.getRange(startRow, 1, 1, 8).setValues(headers)
      .setFontWeight('bold')
      .setBackground('#ecf0f1')
      .setBorder(true, true, true, true, true, true, '#bdc3c7', SpreadsheetApp.BorderStyle.SOLID);
      
    const constraintData = data.constraintAnalysis.map(c => [
      c.region, 
      c.dnoArea, 
      getGspGroupName(c.gspGroup), 
      addFuelEmoji(c.fuelGroup), 
      c.nActions, 
      c.totalMwAdjusted, 
      c.shareOfTotalPct / 100
    ]);
    
    if (constraintData.length > 0) {
      sheet.getRange(startRow + 1, 1, constraintData.length, 7).setValues(constraintData);
      // Format % column
      sheet.getRange(startRow + 1, 7, constraintData.length, 1).setNumberFormat("0.00%");
      
      // Add Sparkline for Share in Col H
      const shareFormulas = constraintData.map((row, i) => {
        const val = row[6]; // % share
        // Blue bar proportional to share
        return [`=SPARKLINE(${val}, {"charttype","bar";"max",1;"color1","#3498db"})`];
      });
      sheet.getRange(startRow + 1, 8, shareFormulas.length, 1).setFormulas(shareFormulas);
      
      // Apply Borders to Data
      sheet.getRange(startRow + 1, 1, constraintData.length, 8)
           .setBorder(true, true, true, true, true, true, '#bdc3c7', SpreadsheetApp.BorderStyle.SOLID);
    }
  }
}

