/**
 * One-time layout function.
 * Creates/clears the "BtM Calculator" sheet and
 * writes a fully-labelled BESS + CHP single-SP calculator
 * with instructions and definitions in cell notes.
 */
function setupBtmCalculator() {
  const ss = SpreadsheetApp.getActive();
  const sheetName = 'BtM Calculator';
  let sh = ss.getSheetByName(sheetName);
  if (!sh) {
    sh = ss.insertSheet(sheetName);
  }
  sh.clear();

  // Column widths for readability
  sh.setColumnWidths(1, 3, 220);

  // ------------------------------------------------------------------
  // 0) CONFIGURATION REFERENCE
  // ------------------------------------------------------------------
  sh.getRange('E1').setValue('📋 Configuration Reference');
  sh.getRange('E1').setFontWeight('bold').setFontSize(10).setBackground('#f3f3f3');
  
  sh.getRange('E2').setValue('BigQuery Dataset:');
  sh.getRange('F2').setValue('uk_energy_prod.v_btm_bess_inputs').setFontSize(9);
  sh.getRange('F2').setNote('View name: inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs');
  
  sh.getRange('E3').setValue('DUoS Rates (p/kWh):');
  sh.getRange('F3').setValue('Red: 17.64, Amber: 4.57, Green: 1.11').setFontSize(9);
  sh.getRange('F3').setNote('Red: 16:00-19:30 weekdays\nAmber: 08:00-16:00, 19:30-22:00 weekdays\nGreen: All other times + weekends');
  
  sh.getRange('E4').setValue('Levies (£/MWh):');
  sh.getRange('F4').setValue('TNUoS: 12.50, BSUoS: 4.50, CCL: 7.75').setFontSize(9);
  sh.getRange('F4').setNote('Full breakdown:\nTNUoS: £12.50\nBSUoS: £4.50\nCCL: £7.75\nRO: £61.90\nFiT: £11.50\nTotal: £98.15/MWh');

  // ------------------------------------------------------------------
  // 1) TITLE + ASSET CONFIGURATION (BESS + CHP)
  // ------------------------------------------------------------------
  sh.getRange('A1').setValue('BtM BESS + CHP Single Settlement Period Calculator');
  sh.getRange('A1').setFontWeight('bold').setFontSize(12);

  sh.getRange('A3').setValue('--- Asset configuration ---').setFontWeight('bold');

  // BESS configuration (BYD Cube-T as default)
  sh.getRange('A4').setValue('BESS technology');
  sh.getRange('B4').setValue('BYD MC10C-B5010-E-R2M01');
  const techRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['BYD MC10C-B5010-E-R2M01', 'Tesla Megapack 2XL', 'Sungrow PowerTitan', 'Custom'], true)
    .setAllowInvalid(true)
    .build();
  sh.getRange('B4').setDataValidation(techRule);
  sh.getRange('B4').setNote(
    'Battery container type. Default: BYD MC Cube-T ESS MC10C-B5010-E-R2M01.\n' +
    'Datasheet usable DC energy ≈ 5,010 kWh per system; nominal power 2×1,252.5 kW.\n' +
    'You can overwrite this text if you use a different asset.'
  );

  sh.getRange('A5').setValue('Number of BESS containers');
  sh.getRange('B5').setValue(2);
  sh.getRange('B5').setNote(
    'How many identical BESS containers are installed at the site.\n' +
    'For 2× BYD MC10C-B5010-E-R2M01, total usable energy ≈ 10 MWh and power ≈ 2.5 MW.'
  );

  sh.getRange('A6').setValue('Usable energy per container (MWh)');
  sh.getRange('B6').setValue(5.0);
  sh.getRange('B6').setNote(
    'Usable energy per container in MWh (at BOL).\n' +
    'From datasheet: 5,010 kWh ≈ 5.01 MWh. Adjust if using SAT / degraded values.'
  );

  sh.getRange('A7').setValue('Total usable BESS energy (MWh)');
  sh.getRange('B7').setFormula('=B5*B6');
  sh.getRange('B7').setNote(
    'Total usable BESS energy = number of containers × usable energy per container.\n' +
    'This should be the maximum SoC (MWh) you ever allow the optimiser to use.'
  );

  sh.getRange('A8').setValue('BESS rated power (MW)');
  sh.getRange('B8').setValue(2.5);
  sh.getRange('B8').setNote(
    'Total BESS export/import capability in MW.\n' +
    'For 2× BYD MC10 cubes, nominal power ≈ 2.5 MW (2×1.2525 MW).'
  );

  // CHP configuration
  sh.getRange('A10').setValue('CHP electrical capacity (MW)');
  sh.getRange('B10').setValue(1.0);
  sh.getRange('B10').setNote(
    'Installed CHP electrical capacity in MW.\n' +
    'This determines the maximum CHP output per Settlement Period (capacity × SP hours).'
  );

  sh.getRange('A11').setValue('Max CHP output this SP (MWh)');
  sh.getRange('B11').setFormula('=B10*$B$16');
  sh.getRange('B11').setNote(
    'Maximum CHP electrical output for the current Settlement Period.\n' +
    '= CHP capacity (MW) × Settlement Period hours.'
  );

  // ------------------------------------------------------------------
  // 2) INPUT / PARAMETER BLOCK
  // ------------------------------------------------------------------
  sh.getRange('A13').setValue('--- Input / Parameter ---').setFontWeight('bold');

  // Asset Source dropdown
  sh.getRange('A14').setValue('Asset Source');
  sh.getRange('B14').setValue('BESS');
  const sourceRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['BESS', 'CHP', 'Both'], true)
    .setAllowInvalid(false)
    .build();
  sh.getRange('B14').setDataValidation(sourceRule);
  sh.getRange('B14').setNote(
    'Select which asset is being dispatched:\n' +
    '• BESS – Battery discharge only\n' +
    '• CHP – Combined Heat & Power only\n' +
    '• Both – Co-optimised dispatch'
  );

  sh.getRange('A15').setValue('Discharged MWh (BESS)');
  sh.getRange('B15').setValue(1);
  sh.getRange('C15').setValue('(MWh this SP)');
  sh.getRange('B15').setNote(
    'BESS energy discharged in this Settlement Period, in MWh.\n' +
    'For a 0.5h SP and 2 MW discharge, this would be 1 MWh.'
  );

  sh.getRange('A16').setValue('Settlement Period hours');
  sh.getRange('B16').setValue(0.5);
  sh.getRange('C16').setValue('(0.5 for GB SP)');
  sh.getRange('B16').setNote(
    'Duration of one Settlement Period in hours.\n' +
    'GB is 0.5 hours per SP. Set to 1.0 if you ever use hourly blocks.'
  );

  // Energy route with dropdown
  sh.getRange('A17').setValue('Energy Route');
  sh.getRange('B17').setValue('BM');
  sh.getRange('C17').setValue('(BM, PPA, Wholesale, ESO Util, BtM Avoided)');
  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['BM', 'PPA', 'Wholesale', 'ESO Util', 'BtM Avoided'], true)
    .setAllowInvalid(false)
    .build();
  sh.getRange('B17').setDataValidation(rule);
  sh.getRange('B17').setNote(
    'Choose the primary energy route for this discharged MWh:\n' +
    '• BM          – Balancing Mechanism offer\n' +
    '• PPA         – Fixed/floating Power Purchase Agreement export\n' +
    '• Wholesale   – DA/ID sale via VTP\n' +
    '• ESO Util    – ESO service utilisation energy (e.g. DC)\n' +
    '• BtM Avoided – BESS serves site load and avoids import (no export sale).\n' +
    'Only ONE energy route can apply to a given physical MWh.'
  );

  // Prices
  sh.getRange('A19').setValue('BM price (£/MWh)');
  sh.getRange('B19').setValue(220);
  sh.getRange('B19').setNumberFormat('£0.00');
  sh.getRange('B19').setNote('Accepted BM Offer price in £/MWh for this SP.');

  sh.getRange('A20').setValue('PPA price (£/MWh)');
  sh.getRange('B20').setValue(150);
  sh.getRange('B20').setNumberFormat('£0.00');
  sh.getRange('B20').setNote('Export PPA price in £/MWh applicable to this SP.');

  sh.getRange('A21').setValue('Wholesale price (£/MWh)');
  sh.getRange('B21').setValue(130);
  sh.getRange('B21').setNumberFormat('£0.00');
  sh.getRange('B21').setNote('Day-ahead / intraday wholesale price for this SP.');

  sh.getRange('A22').setValue('ESO utilisation price (£/MWh)');
  sh.getRange('B22').setValue(180);
  sh.getRange('B22').setNumberFormat('£0.00');
  sh.getRange('B22').setNote(
    'Utilisation rate for ESO service (e.g. Dynamic Containment, FR) in £/MWh.'
  );

  sh.getRange('A23').setValue('Full import cost (£/MWh)');
  sh.getRange('B23').setValue(140);
  sh.getRange('C23').setValue('(energy + DUoS + levies)');
  sh.getRange('B23').setNumberFormat('£0.00');
  sh.getRange('B23').setNote(
    'Total cost to import 1 MWh from grid behind the meter:\n' +
    'energy + DUoS + TNUoS + BSUoS + RO + FiT + CfD + CCL + ECO + WHD + AAHEDC.\n' +
    'Used as the “value” of BtM avoided import when Energy Route = BtM Avoided.'
  );

  sh.getRange('A25').setValue('CM revenue (equiv £/MWh)');
  sh.getRange('B25').setValue(5);
  sh.getRange('C25').setValue('(CM £/kW/year converted to £/MWh)');
  sh.getRange('B25').setNumberFormat('£0.00');
  sh.getRange('B25').setNote(
    'Capacity Market revenue expressed as an equivalent £/MWh.\n' +
    'Derived from £/kW/year divided by expected dispatched MWh.'
  );

  sh.getRange('A26').setValue('Availability £/MW/h');
  sh.getRange('B26').setValue(10);
  sh.getRange('C26').setValue('(ESO/DSO availability rate)');
  sh.getRange('B26').setNumberFormat('£0.00');
  sh.getRange('B26').setNote(
    'Availability payment in £/MW/h for ESO or DSO flexibility services.\n' +
    'This is paid on MW of availability, not on energy delivered.'
  );

  sh.getRange('A28').setValue('Charging cost £/MWh (net)');
  sh.getRange('B28').setValue(120);
  sh.getRange('C28').setValue('(all-in cost per discharged MWh incl. efficiency)');
  sh.getRange('B28').setNumberFormat('£0.00');
  sh.getRange('B28').setNote(
    'Net cost per discharged MWh, including:\n' +
    '• Import energy + DUoS + levies at charge times\n' +
    '• Efficiency losses (so cost is per discharged MWh, not per charged MWh).'
  );

  // ------------------------------------------------------------------
  // 3) CHP PARAMETERS
  // ------------------------------------------------------------------
  sh.getRange('A30').setValue('--- CHP parameters ---').setFontWeight('bold');

  sh.getRange('A31').setValue('CHP Fuel Cost (£/MWh_el)');
  sh.getRange('B31').setValue(80);
  sh.getRange('B31').setNumberFormat('£0.00');
  sh.getRange('C31').setValue('(Gas cost / electrical efficiency)');
  sh.getRange('B31').setNote(
    'Fuel cost per MWh of electrical output.\n' +
    'For example: gas £/MWh_th ÷ electrical efficiency (%).'
  );

  sh.getRange('A32').setValue('CHP Heat Value (£/MWh_th)');
  sh.getRange('B32').setValue(20);
  sh.getRange('B32').setNumberFormat('£0.00');
  sh.getRange('C32').setValue('(Value of heat captured)');
  sh.getRange('B32').setNote(
    'Monetary value of useful heat per thermal MWh.\n' +
    'This is credited against the fuel cost to give a net electrical marginal cost.'
  );

  sh.getRange('A33').setValue('CHP Marginal Cost (£/MWh)');
  sh.getRange('B33').setValue(60);
  sh.getRange('B33').setNumberFormat('£0.00');
  sh.getRange('C33').setValue('(Derived: Fuel - Heat Value)');
  sh.getRange('B33').setNote(
    'Net marginal cost of 1 MWh electrical from CHP after accounting for fuel cost\n' +
    'and the value of recovered heat.\n' +
    'In the optimiser you compare this to BESS net cost/value per MWh.'
  );

  // ------------------------------------------------------------------
  // 4) SoC PARAMETERS
  // ------------------------------------------------------------------
  sh.getRange('A35').setValue('--- SoC parameters ---').setFontWeight('bold');

  sh.getRange('A36').setValue('SoC at start (MWh)');
  sh.getRange('B36').setValue(3);
  sh.getRange('C36').setValue('(state of charge at SP start)');
  sh.getRange('B36').setNote(
    'BESS state of charge at the start of this SP, in MWh.\n' +
    'Must be between SoC minimum and SoC maximum.'
  );

  sh.getRange('A37').setValue('SoC minimum (MWh)');
  sh.getRange('B37').setFormula('=0.1*$B$7');
  sh.getRange('B37').setNote(
    'Minimum allowed SoC in MWh.\n' +
    'Default is 10% of total usable BESS energy.'
  );

  sh.getRange('A38').setValue('SoC maximum (MWh)');
  sh.getRange('B38').setFormula('=$B$7');
  sh.getRange('B38').setNote(
    'Maximum allowed SoC in MWh (by default, full usable capacity).'
  );

  sh.getRange('A39').setValue('Max charge power (MW)');
  sh.getRange('B39').setFormula('=$B$8');
  sh.getRange('B39').setNote(
    'Maximum BESS charge power in MW (import).\n' +
    'Default = rated BESS power.'
  );

  sh.getRange('A40').setValue('Max discharge power (MW)');
  sh.getRange('B40').setFormula('=$B$8');
  sh.getRange('B40').setNote(
    'Maximum BESS discharge power in MW (export).\n' +
    'Default = rated BESS power.'
  );

  sh.getRange('A41').setValue('Round-trip efficiency (%)');
  sh.getRange('B41').setValue(85);
  sh.getRange('C41').setValue('');
  sh.getRange('B41').setNote(
    'Round-trip efficiency of the BESS.\n' +
    'E.g. 85% means 1 MWh discharged required ≈1/0.85 MWh charging energy.'
  );

  // ------------------------------------------------------------------
  // 5) DERIVED VALUES (with formulas)
  // ------------------------------------------------------------------
  sh.getRange('A43').setValue('--- Derived values ---').setFontWeight('bold');

  sh.getRange('A44').setValue('Discharge power (MW)');
  sh.getRange('B44').setFormula('=IFERROR(B15/B16,0)');
  sh.getRange('B44').setNote(
    'Instantaneous BESS power based on discharge energy and SP length:\n' +
    'Discharge power (MW) = Discharged MWh ÷ SP hours.'
  );

  sh.getRange('A45').setValue('SoC at end (MWh)');
  sh.getRange('B45').setFormula('=B36-B15');
  sh.getRange('B45').setNote(
    'SoC at end = SoC at start – discharged MWh.\n' +
    'Charging would be modelled with a positive term added here.'
  );

  // Energy revenue based on selected route
  sh.getRange('A46').setValue('Energy revenue (£)');
  sh.getRange('B46').setFormula(
    '=B15*SWITCH(B17,' +
    '"BM",B19,' +
    '"PPA",B20,' +
    '"Wholesale",B21,' +
    '"ESO Util",B22,' +
    '"BtM Avoided",B23,' +
    '0)'
  );
  sh.getRange('B46').setNumberFormat('£0.00');
  sh.getRange('B46').setNote(
    'Revenue (or value) from the chosen energy route ONLY:\n' +
    '= Discharged MWh × selected price.\n' +
    'For BtM Avoided, this is the avoided import cost.'
  );

  // CM revenue
  sh.getRange('A47').setValue('CM revenue (£)');
  sh.getRange('B47').setFormula('=B15*B25');
  sh.getRange('B47').setNumberFormat('£0.00');
  sh.getRange('B47').setNote(
    'Capacity Market revenue for this SP expressed as £.\n' +
    '= Discharged MWh × CM revenue equivalent (£/MWh).'
  );

  // Availability revenue
  sh.getRange('A48').setValue('Availability revenue (£)');
  sh.getRange('B48').setFormula('=B44*B26*B16');
  sh.getRange('B48').setNumberFormat('£0.00');
  sh.getRange('B48').setNote(
    'Availability payment = Power (MW) × £/MW/h × SP hours.\n' +
    'This can be paid even if no energy is dispatched, depending on product rules.'
  );

  // Total stacked revenue
  sh.getRange('A49').setValue('Total stacked revenue (£)');
  sh.getRange('B49').setFormula('=B46+B47+B48');
  sh.getRange('B49').setNumberFormat('£0.00');
  sh.getRange('B49').setNote(
    'Total revenue / value for this SP = Energy revenue + CM + availability.'
  );

  // Charging cost
  sh.getRange('A50').setValue('Charging cost (£)');
  sh.getRange('B50').setFormula('=B15*B28');
  sh.getRange('B50').setNumberFormat('£0.00');
  sh.getRange('B50').setNote(
    'Total cost of charging to produce this discharged MWh.\n' +
    '= Discharged MWh × net charging cost per discharged MWh.'
  );

  // Margin
  sh.getRange('A51').setValue('Margin on this 1 MWh (£)');
  sh.getRange('B51').setFormula('=B49-B50');
  sh.getRange('B51').setNumberFormat('£0.00');
  sh.getRange('B51').setNote(
    'EBITDA-like margin for this SP and this BESS discharge.\n' +
    'Includes energy value + CM + availability – net charging cost.\n' +
    'Does not include fixed O&M, capex, etc.'
  );

  // Make headings bold
  sh.getRange('A3:A3').setFontWeight('bold');
  sh.getRange('A13:A13').setFontWeight('bold');
  sh.getRange('A30:A30').setFontWeight('bold');
  sh.getRange('A35:A35').setFontWeight('bold');
  sh.getRange('A43:A43').setFontWeight('bold');

  // ------------------------------------------------------------------
  // 6) BIGQUERY LOOKUP BLOCK (Top Right)
  // ------------------------------------------------------------------
  sh.getRange('E21').setValue('Settlement Date');
  sh.getRange('E21').setFontWeight('bold');
  sh.getRange('F21').setValue(new Date());
  sh.getRange('F21').setNumberFormat('yyyy-mm-dd');

  sh.getRange('E22').setValue('Settlement Period');
  sh.getRange('E22').setFontWeight('bold');
  sh.getRange('F22').setValue(1);
  const spRule = SpreadsheetApp.newDataValidation()
    .requireNumberBetween(1, 48)
    .setAllowInvalid(false)
    .setHelpText('Enter a Settlement Period between 1 and 48.')
    .build();
  sh.getRange('F22').setDataValidation(spRule);
  sh.getRange('F22').setNote('Enter SP 1–48');
}

/**
 * Creates/clears the "BtM Daily" sheet.
 * Sets up a 48-SP table with SoC chaining and revenue formulas.
 */
function setupBtmDailyView() {
  const ss = SpreadsheetApp.getActive();
  const sheetName = 'BtM Daily';
  let sh = ss.getSheetByName(sheetName);
  if (!sh) {
    sh = ss.insertSheet(sheetName);
  }
  sh.clear();

  // 1) Header info
  sh.getRange('A1').setValue('BtM Daily View (48 SPs)');
  sh.getRange('A1').setFontWeight('bold').setFontSize(14);
  sh.getRange('A2').setValue('Date:');
  sh.getRange('B1').setValue(new Date()); // Date input
  sh.getRange('B1').setNumberFormat('yyyy-mm-dd');
  
  sh.getRange('A2').setValue('Start SoC (MWh):');
  sh.getRange('B2').setValue(3.0); // Initial SoC

  // 2) Table Headers (Row 3)
  const headers = [
    'SP', 'Net BESS MWh', 'Energy Route', 
    'BM Price', 'PPA Price', 'Wholesale Price', 'ESO Util Price', 'Full Import Cost', 
    'CM Equiv', 'Avail £/MW/h', 'Charge Cost £/MWh', 
    'SoC Start', 'SoC End', 'Power (MW)', 
    'Energy Rev', 'CM Rev', 'Avail Rev', 'Total Rev', 'Charge Cost', 'Margin'
  ];
  // Columns A to T (1 to 20)
  sh.getRange(3, 1, 1, headers.length).setValues([headers]);
  sh.getRange(3, 1, 1, headers.length).setFontWeight('bold').setBackground('#f3f3f3');

  // 3) Populate Rows 4 to 51 (SP 1 to 48)
  const sps = [];
  for (let i = 1; i <= 48; i++) {
    sps.push([i]);
  }
  sh.getRange(4, 1, 48, 1).setValues(sps); // Column A: SP numbers

  // Dropdown for Energy Route (Column C)
  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['BM', 'PPA', 'Wholesale', 'ESO Util', 'BtM Avoided'], true)
    .setAllowInvalid(false)
    .build();
  sh.getRange('C4:C51').setDataValidation(rule);
  sh.getRange('C4:C51').setValue('BM'); // Default

  // Default values for prices (just placeholders)
  sh.getRange('D4:D51').setValue(220); // BM
  sh.getRange('E4:E51').setValue(150); // PPA
  sh.getRange('F4:F51').setValue(130); // Wholesale
  sh.getRange('G4:G51').setValue(180); // ESO Util
  sh.getRange('H4:H51').setValue(140); // Import Cost
  sh.getRange('I4:I51').setValue(5);   // CM Equiv
  sh.getRange('J4:J51').setValue(10);  // Avail
  sh.getRange('K4:K51').setValue(120); // Charge Cost

  // Net BESS MWh (Column B) - Default 0
  sh.getRange('B4:B51').setValue(0);

  // SoC Logic (Columns L and M)
  // L4 (Start SoC for SP1) = B2
  sh.getRange('L4').setFormula('=$B$2');
  // M4 (End SoC for SP1) = Start - Net Discharge
  // Note: Positive BESS MWh = Discharge, Negative = Charge
  sh.getRange('M4').setFormula('=L4 - B4');

  // L5 onwards: Start SoC = End SoC of previous SP
  sh.getRange('L5:L51').setFormula('=OFFSET(M5,-1,0)');
  sh.getRange('M5:M51').setFormula('=L5 - B5');

  // Power (MW) (Column N) = MWh / 0.5
  sh.getRange('N4:N51').setFormula('=B4/0.5');

  // Revenue Formulas (Columns O to T)
  
  // Energy Revenue (O)
  // If BESS MWh > 0 (Discharge), use selected price. If < 0 (Charge), 0 revenue (cost handled separately).
  // Price selection logic:
  // BM=D, PPA=E, Wholesale=F, ESO=G, BtM=H
  const priceSwitch = 'SWITCH(C4, "BM",D4, "PPA",E4, "Wholesale",F4, "ESO Util",G4, "BtM Avoided",H4, 0)';
  sh.getRange('O4:O51').setFormula(`=IF(B4>0, B4 * ${priceSwitch}, 0)`);

  // CM Revenue (P) = MWh * CM Equiv (I)
  sh.getRange('P4:P51').setFormula('=IF(B4>0, B4 * I4, 0)');

  // Availability Revenue (Q) = MW * Avail Price * 0.5
  // Assuming availability is paid on capacity (MW) for the duration
  // Using ABS(Power) as availability might be provided while charging too? 
  // For simplicity, let's assume availability is based on the Power MW derived from flow.
  sh.getRange('Q4:Q51').setFormula('=ABS(N4) * J4 * 0.5');

  // Total Revenue (R)
  sh.getRange('R4:R51').setFormula('=O4+P4+Q4');

  // Charging Cost (S)
  // If BESS MWh < 0 (Charging), Cost = ABS(MWh) * Charge Cost (K)
  // If BESS MWh > 0 (Discharging), we might attribute cost of goods sold?
  // The prompt implies "Charging cost £/MWh" is a parameter.
  // Let's assume K is "Cost to charge 1 MWh".
  // If row is charging (B < 0): Cost = -B * K
  // If row is discharging (B > 0): Cost = B * K (Cost of Goods Sold logic from Calculator)
  // The calculator used: Discharged MWh * Net Charging Cost. Let's stick to that.
  sh.getRange('S4:S51').setFormula('=IF(B4>0, B4 * K4, 0)'); 
  // Note: This ignores the cost incurred *during* the charging event itself in this P&L view, 
  // effectively matching the "Margin on this 1 MWh" logic of the single calculator.

  // Margin (T)
  sh.getRange('T4:T51').setFormula('=R4 - S4');

  // Formatting
  sh.getRange('D4:K51').setNumberFormat('£#,##0.00');
  sh.getRange('O4:T51').setNumberFormat('£#,##0.00');
  sh.getRange('L4:M51').setNumberFormat('0.00');
  sh.getRange('N4:N51').setNumberFormat('0.00');
}

/**
 * Create a "GB Live" style KPI strip driven by BtM Daily.
 * 
 * Requirements:
 *  - BtM Daily sheet must exist and use the structure from setupBtmDailyView():
 *    • B4:B51  Net BESS MWh
 *    • R4:R51  Total revenue (£)
 *    • S4:S51  Charging cost (£)
 *    • T4:T51  Margin (£)
 *    • L4:M51  SoC start/end
 *    • B1      Date
 */
function setupGBLiveKPIs() {
  const ss = SpreadsheetApp.getActive();
  const sheetName = 'GB Live';
  let sh = ss.getSheetByName(sheetName);
  if (!sh) {
    sh = ss.insertSheet(sheetName);
  }
  sh.clear();
  sh.setColumnWidths(1, 12, 120);

  // Title + date
  sh.getRange('A1').setValue('GB Live – BtM BESS KPIs');
  sh.getRange('A1').setFontWeight('bold').setFontSize(14);
  sh.getRange('A2').setValue('Date');
  sh.getRange('B2').setFormula("='BtM Daily'!B1");
  sh.getRange('B2').setNumberFormat('yyyy-mm-dd');

  // KPI layout (labels in odd columns, values in even columns)
  // Row 4: Revenue stack
  sh.getRange('A4').setValue('💷 Total BESS revenue (today)');
  sh.getRange('B4').setFormula("=SUM('BtM Daily'!R4:R51)");
  sh.getRange('B4').setNumberFormat('£#,##0');

  sh.getRange('D4').setValue('💸 Total charging cost');
  sh.getRange('E4').setFormula("=SUM('BtM Daily'!S4:S51)");
  sh.getRange('E4').setNumberFormat('£#,##0');

  sh.getRange('G4').setValue('📊 Net margin (BESS)');
  sh.getRange('H4').setFormula("=SUM('BtM Daily'!T4:T51)");
  sh.getRange('H4').setNumberFormat('£#,##0');

  // Row 5: Volumes + performance
  sh.getRange('A5').setValue('⚡ Total discharged MWh');
  sh.getRange('B5').setFormula("=SUMIF('BtM Daily'!B4:B51,\">0\",'BtM Daily'!B4:B51)");
  sh.getRange('B5').setNumberFormat('0.0');

  sh.getRange('D5').setValue('🔋 Total charging MWh');
  sh.getRange('E5').setFormula("=-SUMIF('BtM Daily'!B4:B51,\"<0\",'BtM Daily'!B4:B51)");
  sh.getRange('E5').setNumberFormat('0.0');

  sh.getRange('G5').setValue('✅ Profitable SPs');
  sh.getRange('H5').setFormula("=COUNTIF('BtM Daily'!T4:T51,\">0\")");
  sh.getRange('H5').setNumberFormat('0');

  sh.getRange('J5').setValue('❌ Loss-making SPs');
  sh.getRange('K5').setFormula("=COUNTIF('BtM Daily'!T4:T51,\"<0\")");
  sh.getRange('K5').setNumberFormat('0');

  // Row 6: SoC and unit economics
  sh.getRange('A6').setValue('📉 Min SoC (MWh)');
  sh.getRange('B6').setFormula("=MIN('BtM Daily'!L4:M51)");
  sh.getRange('B6').setNumberFormat('0.0');

  sh.getRange('D6').setValue('📈 Max SoC (MWh)');
  sh.getRange('E6').setFormula("=MAX('BtM Daily'!L4:M51)");
  sh.getRange('E6').setNumberFormat('0.0');

  sh.getRange('G6').setValue('💷 Avg revenue / discharged MWh');
  sh.getRange('H6').setFormula(
    "=IFERROR(SUM('BtM Daily'!R4:R51)/" +
    "SUMIF('BtM Daily'!B4:B51,\">0\",'BtM Daily'!B4:B51),0)"
  );
  sh.getRange('H6').setNumberFormat('£#,##0.00');

  // --- Styling to feel like a KPI strip ---

  // Base style
  const labelRanges = ['A4:A6','D4:D6','G4:G6','J5:J5'];
  labelRanges.forEach(r => {
    sh.getRange(r).setFontWeight('bold').setHorizontalAlignment('left');
  });

  const valueRanges = ['B4:B6','E4:E6','H4:H6','K5:K5'];
  valueRanges.forEach(r => {
    sh.getRange(r)
      .setFontWeight('bold')
      .setHorizontalAlignment('center')
      .setFontSize(12);
  });

  // Colour blocks (roughly aligned with your design palette)
  // Primary KPI cards (revenue / margin): blue
  sh.getRange('A4:B4').setBackground('#006FBD').setFontColor('#ffffff');
  sh.getRange('D4:E4').setBackground('#004A80').setFontColor('#ffffff');
  sh.getRange('G4:H4').setBackground('#006FBD').setFontColor('#ffffff');

  // Volume + count metrics: secondary blue
  sh.getRange('A5:B5').setBackground('#004A80').setFontColor('#ffffff');
  sh.getRange('D5:E5').setBackground('#004A80').setFontColor('#ffffff');
  sh.getRange('G5:H5').setBackground('#004A80').setFontColor('#ffffff');
  sh.getRange('J5:K5').setBackground('#004A80').setFontColor('#ffffff');

  // SoC + unit economics: accent amber / blue
  sh.getRange('A6:B6').setBackground('#F5A623').setFontColor('#000000');
  sh.getRange('D6:E6').setBackground('#F5A623').setFontColor('#000000');
  sh.getRange('G6:H6').setBackground('#006FBD').setFontColor('#ffffff');

  // Freeze top rows
  sh.setFrozenRows(3);
}

// ------------------------------------------------------------------
// BIGQUERY INTEGRATION (Placeholder for now)
// ------------------------------------------------------------------
// PROJECT_ID and DATASET are defined in Code.gs
const VIEW = 'v_btm_bess_inputs';

function populatePricesFromBigQuery() {
  const ui = SpreadsheetApp.getUi();
  ui.alert('BigQuery integration requires enabling the BigQuery API service in Apps Script.\n\nOnce enabled, this function can query ' + PROJECT_ID + '.' + DATASET + '.' + VIEW);
}

// ------------------------------------------------------------------
// DEBUG / SELF-TEST
// ------------------------------------------------------------------
function debugWhatIsWorking() {
  const ss = SpreadsheetApp.getActive();
  const msg = [];
  msg.push('Sheets: ' + ss.getSheets().map(s => s.getName()).join(', '));
  
  const gbLive = ss.getSheetByName('GB Live');
  msg.push('GB Live B4 formula: ' + (gbLive ? gbLive.getRange('B4').getFormula() : 'Sheet missing'));
  
  const btmDaily = ss.getSheetByName('BtM Daily');
  msg.push('BtM Daily B4 value: ' + (btmDaily ? btmDaily.getRange('B4').getValue() : 'Sheet missing'));
  
  SpreadsheetApp.getUi().alert(msg.join('\n'));
}

// ------------------------------------------------------------------
// MENU
// ------------------------------------------------------------------
function createBtmMenu() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('BtM Tools')
    .addItem('Setup BtM Calculator', 'setupBtmCalculator')
    .addItem('Setup BtM Daily View', 'setupBtmDailyView')
    .addItem('Setup GB Live KPIs', 'setupGBLiveKPIs')
    .addSeparator()
    .addItem('Populate prices from BigQuery (single SP)', 'populatePricesFromBigQuery')
    .addItem('Debug: Check Status', 'debugWhatIsWorking')
    .addToUi();
}
