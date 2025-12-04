let ws;
function connectWS() {
  const status = document.getElementById("connectionStatus");
  status.classList.remove("connected", "error");
  status.querySelector(".label").innerText = "Connecting...";
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => {
    status.classList.add("connected");
    status.querySelector(".label").innerText = "Live";
  };
  ws.onerror = () => {
    status.classList.add("error");
    status.querySelector(".label").innerText = "Error";
  };
  ws.onmessage = evt => {
    try {
      const data = JSON.parse(evt.data);
      renderKPIs(data);
      renderInsights(data);
      refreshChartsAndMap();
    } catch (e) {
      console.error("WS message error:", e);
    }
  };
  ws.onclose = () => {
    status.classList.add("error");
    status.querySelector(".label").innerText = "Disconnected";
    setTimeout(connectWS, 5000);
  };
}
connectWS();

function renderKPIs(data) {
  const row = document.getElementById("kpiRow");
  const vlp = (data.vlp || [])[0] || {};
  const wind = (data.wind || [])[0] || {};
  const bm = (data.bm_price || [])[0] || {};
  row.innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">VLP Total Capacity</div>
      <div class="kpi-value">${vlp.total_capacity_mw ?? 0} MW</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Wind Avg Error</div>
      <div class="kpi-value">${((wind.pct_err || 0) * 100).toFixed(1)}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">SBP Next</div>
      <div class="kpi-value">£${(bm.sbp_next || 0).toFixed(0)}/MWh</div>
    </div>
  `;
}

function renderInsights(data) {
  const box = document.getElementById("insights");
  let out = [];
  if (data.wind && data.wind.length) {
    const avgErr = data.wind.reduce((a,b)=>a+(b.pct_err||0),0) / data.wind.length;
    out.push(`🌬 Wind error ~ ${(avgErr*100).toFixed(1)}%`);
  }
  if (data.constraints && data.constraints.length) {
    const high = data.constraints.filter(x => (x.constraint_prob||0) > 0.4).length;
    out.push(`⚠ ${high} GSPs have constraint probability >40%`);
  }
  if (!out.length) out = ["No insights yet."];
  box.innerHTML = out.map(x=>`<div>${x}</div>`).join("");
}

function refreshChartsAndMap() {
  const ts = Date.now();
  ["chartVlp","chartWind","chartBm","chartSpreads","chartProj"].forEach(id => {
    const el = document.getElementById(id);
    const base = el.src.split("?")[0];
    el.src = base + "?t=" + ts;
  });
  const iframe = document.getElementById("mapFrame");
  const base = iframe.src.split("?")[0];
  iframe.src = base + "?t=" + ts;
}
