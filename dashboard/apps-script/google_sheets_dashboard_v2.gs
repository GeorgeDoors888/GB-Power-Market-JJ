// google_sheets_dashboard_v2.gs — v2.2
const VERCEL_PROXY = 'https://gb-power-market-jj.vercel.app/api/proxy-v2';
const PROJECT = 'inner-cinema-476211-u9';
const DATASET = 'uk_energy_prod';
const TZ = 'Europe/London';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('⚡ Power Market')
    .addItem('🔄 Refresh Now (today)', 'refreshDashboardToday')
    .addItem('📊 Rebuild Chart', 'rebuildDashboardChart')
    .addItem('⏰ Set 5‑min Auto‑Refresh', 'set5MinTrigger')
    .addItem('🛑 Stop Auto‑Refresh', 'clearTriggers')
    .addSeparator()
    .addItem('🗓 Rebuild Calendar (month)', 'rebuildCalendarSheet')
    .addItem('🧲 Toggle IC vs Spread Overlay', 'toggleICOverlay')
    .addSeparator()
    .addItem('🚀 One‑Click Setup', 'Setup_Dashboard_AutoRefresh')
    .addToUi();
}

function todayDateStr_YYYY_MM_DD() {
  return Utilities.formatDate(new Date(), TZ, 'yyyy-MM-dd');
}

function ensureStructure() {
  const ss = SpreadsheetApp.getActive();
  const need = ['Live Dashboard','Chart Data','Live_Raw_Prices','Live_Raw_Gen','Live_Raw_BOA','Live_Raw_IC','Audit_Log','Calendar'];
  need.forEach(n => { if (!ss.getSheetByName(n)) ss.insertSheet(n); });
  const sh = ss.getSheetByName('Live Dashboard');
  if (sh.getLastRow() === 0) {
    sh.appendRow(['SP','Time','SSP £/MWh','SBP £/MWh','Demand MW','Generation MW','BOALF Actions','BOD Offer £/MWh','BOD Bid £/MWh','IC Net MW']);
  }
  const cal = ss.getSheetByName('Calendar');
  if (cal.getLastRow() === 0) {
    cal.appendRow(['Calendar Controls']);
    cal.appendRow(['Month (YYYY‑MM):','']);
    cal.getRange('B2').setDataValidation(SpreadsheetApp.newDataValidation()
      .requireValueInList(generateMonthList(), true).setAllowInvalid(false).build());
  }
}

function generateMonthList() {
  const now = new Date();
  const out = [];
  for (let i=0;i<36;i++) {
    const d = new Date(now.getFullYear(), now.getMonth()-i, 1);
    out.push(Utilities.formatDate(d, TZ, 'yyyy-MM'));
  }
  return out;
}

function stampAudit(status, msg) {
  try {
    const ss = SpreadsheetApp.getActive();
    const sh = ss.getSheetByName('Audit_Log');
    if (!sh) return;
    if (sh.getLastRow() < 1) sh.appendRow(['Timestamp','Status','Message','User']);
    const user = Session.getActiveUser().getEmail() || Session.getEffectiveUser().getEmail() || 'unknown';
    sh.appendRow([new Date(), status, msg, user]);
    if (sh.getLastRow() > 1001) sh.deleteRows(2, sh.getLastRow()-1001);
  } catch(e) { Logger.log(e); }
}

function proxyGet(sql) {
  const url = VERCEL_PROXY + '?path=/query_bigquery_get&sql=' + encodeURIComponent(sql);
  const resp = UrlFetchApp.fetch(url, { method: 'get', muteHttpExceptions: true, validateHttpsCertificates: true });
  const code = resp.getResponseCode();
  const body = resp.getContentText();
  if (code !== 200) throw new Error(`HTTP ${code}: ${body.substring(0,300)}`);
  const json = JSON.parse(body);
  if (!json.success) throw new Error(`Query failed: ${json.error || 'unknown'}`);
  return json.data || [];
}

function pingHealth() {
  const url = VERCEL_PROXY + '?path=/health';
  const resp = UrlFetchApp.fetch(url, { method: 'get', muteHttpExceptions: true, validateHttpsCertificates: true });
  return { code: resp.getResponseCode(), body: resp.getContentText().slice(0,500), ok: resp.getResponseCode() === 200 };
}

function sqlSystemPrices(ymd) {
  return `
    WITH prices AS (
      SELECT DATE(settlementDate) d, settlementPeriod sp, dataProvider, AVG(price) price
      FROM \`${PROJECT}.${DATASET}.bmrs_mid\`
      WHERE DATE(settlementDate) = DATE('${ymd}')
      GROUP BY d, sp, dataProvider
    )
    SELECT sp,
           MAX(CASE WHEN dataProvider='N2EXMIDP' THEN price END) AS ssp,
           MAX(CASE WHEN dataProvider='APXMIDP' THEN price END) AS sbp
    FROM prices
    GROUP BY sp
    ORDER BY sp`;
}

function sqlGenDemand(ymd) {
  return `
    WITH gen AS (
      SELECT settlementPeriod sp, AVG(generation) gen_mw
      FROM \`${PROJECT}.${DATASET}.bmrs_indgen_iris\`
      WHERE DATE(settlementDate)=DATE('${ymd}') AND boundary='N'
      GROUP BY sp
    ),
    dem AS (
      SELECT settlementPeriod sp, ABS(AVG(demand)) demand_mw
      FROM \`${PROJECT}.${DATASET}.bmrs_inddem_iris\`
      WHERE DATE(settlementDate)=DATE('${ymd}') AND boundary='N'
      GROUP BY sp
    )
    SELECT COALESCE(gen.sp,dem.sp) sp, gen.gen_mw, dem.demand_mw
    FROM gen FULL OUTER JOIN dem USING(sp)
    ORDER BY sp`;
}

function sqlBOALF(ymd) {
  return `
    SELECT settlementPeriod sp, COUNT(*) boalf_count, AVG(acceptedVolumeMW) boalf_avg_mw
    FROM \`${PROJECT}.${DATASET}.bmrs_boalf\`
    WHERE DATE(settlementDate)=DATE('${ymd}')
    GROUP BY sp
    ORDER BY sp`;
}

function sqlBOD(ymd) {
  return `
    SELECT settlementPeriod sp,
           AVG(NULLIF(offerPrice,0)) offer_avg,
           AVG(NULLIF(bidPrice,0))   bid_avg
    FROM \`${PROJECT}.${DATASET}.bmrs_bod\`
    WHERE DATE(settlementDate)=DATE('${ymd}')
    GROUP BY sp
    ORDER BY sp`;
}

function sqlICNet(ymd) {
  return `
    WITH ic AS (
      SELECT settlementPeriod sp, SUM(generation) ic_net_mw
      FROM \`${PROJECT}.${DATASET}.bmrs_indgen_iris\`
      WHERE DATE(settlementDate)=DATE('${ymd}') AND fuelType IN ('IFA','IFA2','NSL','Moyle','BritNed','Eleclink','EWIC','Viking','NEMO') 
      GROUP BY sp
    )
    SELECT sp, ic_net_mw FROM ic
    ORDER BY sp`;
}

function refreshDashboardToday() {
  ensureStructure();
  const started = new Date();
  const ymd = todayDateStr_YYYY_MM_DD();
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName('Live Dashboard');
  const chartData = ss.getSheetByName('Chart Data');

  try {
    const p = proxyGet(sqlSystemPrices(ymd));
    const gd = proxyGet(sqlGenDemand(ymd));
    const bo = proxyGet(sqlBOALF(ymd));
    const bod = proxyGet(sqlBOD(ymd));
    const ic = proxyGet(sqlICNet(ymd));

    const idx = {};
    const rows = [];
    for (let sp=1; sp<=48; sp++) idx[sp] = { sp, ssp:null, sbp:null, gen:null, dem:null, boalf:null, offer:null, bid:null, ic:null };
    p.forEach(r => { if (idx[r.sp]) { idx[r.sp].ssp=r.ssp; idx[r.sp].sbp=r.sbp; } });
    gd.forEach(r => { if (idx[r.sp]) { idx[r.sp].gen=r.gen_mw; idx[r.sp].dem=r.demand_mw; } });
    bo.forEach(r => { if (idx[r.sp]) { idx[r.sp].boalf=r.boalf_count; } });
    bod.forEach(r => { if (idx[r.sp]) { idx[r.sp].offer=r.offer_avg; idx[r.sp].bid=r.bid_avg; } });
    ic.forEach(r => { if (idx[r.sp]) { idx[r.sp].ic=r.ic_net_mw; } });

    dash.getRange(2,1,Math.max(1,dash.getLastRow()-1),dash.getLastColumn()).clearContent();
    chartData.clearContents(); chartData.appendRow(['SP','Time','SSP £/MWh','SBP £/MWh','Demand MW','Generation MW','BOALF Actions','BOD Offer £/MWh','BOD Bid £/MWh','IC Net MW']);

    for (let sp=1; sp<=48; sp++) {
      const row = [sp, `SP${sp}`, idx[sp].ssp, idx[sp].sbp, idx[sp].dem, idx[sp].gen, idx[sp].boalf, idx[sp].offer, idx[sp].bid, idx[sp].ic];
      rows.push(row);
      chartData.appendRow(row);
    }
    if (rows.length) dash.getRange(2,1,rows.length,rows[0].length).setValues(rows);
    const last = 1 + rows.length;
    ss.setNamedRange('NR_DASH_TODAY', chartData.getRange(1,1,rows.length+1,10));

    const elapsed = ((new Date())-started)/1000;
    stampAudit('ok', `Refresh complete for ${ymd} (${elapsed.toFixed(1)}s, ${rows.length} rows)`);
  } catch (e) {
    stampAudit('error', e.message);
    throw e;
  }
}

function rebuildDashboardChart() {
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName('Live Dashboard');
  const chartData = ss.getSheetByName('Chart Data');
  dash.getCharts().forEach(c => dash.removeChart(c));
  const range = chartData.getRange('A1:J49');
  let builder = dash.newChart()
    .asComboChart().addRange(range).setPosition(1,12,0,0).setNumHeaders(1)
    .setOption('legend', { position: 'bottom' })
    .setOption('hAxis', { slantedText: true })
    .setOption('series', {
      0: { targetAxisIndex: 1, type: 'line' },
      1: { targetAxisIndex: 1, type: 'line' },
      2: { targetAxisIndex: 0, type: 'area', areaOpacity: 0.25 },
      3: { targetAxisIndex: 0, type: 'area', areaOpacity: 0.25 },
      4: { targetAxisIndex: 0, type: 'line' },
      5: { targetAxisIndex: 1, type: 'line', lineDashStyle: [4,4] },
      6: { targetAxisIndex: 1, type: 'line', lineDashStyle: [4,4] },
      7: { targetAxisIndex: 0, type: 'line' }
    })
    .setOption('vAxes', { 0: { title: 'MW' }, 1: { title: '£/MWh' } })
    .setOption('title', 'GB Power — Today (IC vs Spread overlay incl.)');
  dash.insertChart(builder.build());
  stampAudit('ok', 'Chart rebuilt');
}

function toggleICOverlay() { rebuildDashboardChart(); }

function set5MinTrigger() {
  clearTriggers();
  ScriptApp.newTrigger('refreshDashboardToday').timeBased().everyMinutes(5).create();
  stampAudit('ok', '5‑min auto‑refresh enabled');
}
function clearTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  stampAudit('ok', 'All triggers cleared');
}

function Setup_Dashboard_AutoRefresh() {
  ensureStructure();
  refreshDashboardToday();
  rebuildDashboardChart();
  set5MinTrigger();
}

// Calendar (daily SSP/SBP)
function rebuildCalendarSheet() {
  const ss = SpreadsheetApp.getActive();
  const cal = ss.getSheetByName('Calendar');
  ensureStructure();
  const monthSel = cal.getRange('B2').getValue() || Utilities.formatDate(new Date(), TZ, 'yyyy-MM');
  const y = monthSel.split('-')[0], m = monthSel.split('-')[1];
  const first = `${monthSel}-01`;
  const sql = `
    WITH hh AS (
      SELECT DATE(settlementDate) d, settlementPeriod sp,
             AVG(CASE WHEN dataProvider='N2EXMIDP' THEN price END) ssp,
             AVG(CASE WHEN dataProvider='APXMIDP' THEN price END) sbp
      FROM \`${PROJECT}.${DATASET}.bmrs_mid\`
      WHERE DATE(settlementDate) BETWEEN DATE('${first}') AND DATE(DATE_ADD('${first}', INTERVAL 1 MONTH) - 1)
      GROUP BY d, sp
    ),
    daily AS ( SELECT d, AVG(ssp) ssp_day, AVG(sbp) sbp_day FROM hh GROUP BY d )
    SELECT * FROM daily ORDER BY d`;
  const rows = proxyGet(sql);
  cal.getRange(4,1,cal.getMaxRows()-3,cal.getMaxColumns()).clearContent();
  cal.getRange('A4').setValue(`Month: ${monthSel} (SSP/SBP daily avg)`);
  cal.getRange(5,1,1,7).setValues([['Mon','Tue','Wed','Thu','Fri','Sat','Sun']]);
  const start = new Date(parseInt(y), parseInt(m)-1, 1);
  const startDow = (start.getDay()+6)%7;
  const daysInMonth = new Date(parseInt(y), parseInt(m), 0).getDate();
  const map = {}; rows.forEach(o => map[o.d]=o);
  let r=6,c=startDow+1;
  for (let day=1; day<=daysInMonth; day++) {
    const dStr = Utilities.formatDate(new Date(parseInt(y), parseInt(m)-1, day), TZ, 'yyyy-MM-dd');
    const obj = map[dStr] || {};
    cal.getRange(r,c).setValue(`${day}\nSSP ${obj.ssp_day||''}\nSBP ${obj.sbp_day||''}`);
    c++; if (c>7){c=1;r++;}
  }
}
