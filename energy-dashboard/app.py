# app.py
import os
import json
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# ==== Config via env ====
CODEX_BASE   = os.environ.get("CODEX_BASE", "https://jibber-jabber-production.up.railway.app")
CODEX_TOKEN  = os.environ.get("CODEX_TOKEN")  # set in Railway -> Variables
PROJECT      = os.environ.get("BQ_PROJECT", "jibber-jabber-knowledge")
DATASET      = os.environ.get("BQ_DATASET", "uk_energy_insights")
REFRESH_MIN  = int(os.environ.get("REFRESH_MIN", "5"))

# Optional overrides for table names (comma-separated)
OVERRIDE_TABLES = {
    "demand": os.environ.get("TABLE_DEMAND"),
    "fuel": os.environ.get("TABLE_FUEL"),
    "bmu": os.environ.get("TABLE_BMU"),
    "balancing_costs": os.environ.get("TABLE_BAL_COSTS"),
}

# Candidate tables (ordered) we'll probe; override beats these
CANDIDATES = {
    "demand": [
        "fes_electricity_demand_summary_data_table_ed1",  # you listed this
        "demand_24h",                                     # generic
        "bmrs_mid",                                       # market index data often contains demand series
    ],
    "fuel": [
        "fuel_by_type",       # generic
        "generation_mix",     # generic
        "bmrs_fuelinst_iris", # if mirrored here via views
    ],
    "bmu": [
        "bmrs_data",                # your note "balancing mechanism data"
        "balancing_mechanism_bmu",  # generic
    ],
    "balancing_costs": [
        "daily_balancing_volume_balancing_services_use_of_system",
        "balancing_costs",
        "constraint_breakdown",
    ],
}

# ---------------- Helpers ----------------
def codex_query(sql: str, timeout: int = 60, max_results: int = 2000):
    url = f"{CODEX_BASE}/query_bigquery"
    headers = {"Content-Type": "application/json"}
    if CODEX_TOKEN:
        headers["Authorization"] = f"Bearer {CODEX_TOKEN}"

    payload = {"sql": sql, "timeout": timeout, "max_results": max_results}
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout + 5)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Codex error {r.status_code}: {r.text}")
    data = r.json()
    if not data.get("success", False):
        raise HTTPException(status_code=502, detail=f"BigQuery error: {data.get('error')}")
    return data["data"]

def list_tables():
    sql = f"""
      SELECT table_name
      FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.TABLES`
      ORDER BY table_name
      LIMIT 500
    """
    rows = codex_query(sql, timeout=60, max_results=500)
    return {r["table_name"] for r in rows}

def pick_table(kind: str, available: set) -> str | None:
    override = OVERRIDE_TABLES.get(kind)
    if override:
        return override
    for t in CANDIDATES.get(kind, []):
        if t in available:
            return t
    return None

def fq(table: str) -> str:
    return f"`{PROJECT}.{DATASET}.{table}`"

app = FastAPI(title="UK Energy Dashboard (via Codex)")

# -------------- API --------------
@app.get("/api/summary")
def api_summary():
    """
    Returns:
      {
        "now": "...",
        "current_demand": {"value": ..., "unit": "..."},
        "fuel_mix": [{"fuel":"Gas","mw":...}, ...],
        "demand_24h": [{"ts":"...","demand":...}, ...],
        "top_bmus": [{"bmu":"...","mw":...}, ...],
        "balancing_costs": [{"ts":"...","cost_gbp":...}, ...],
        "used_tables": {...}
      }
    """
    available = list_tables()

    # Decide tables
    tbl_demand = pick_table("demand", available)
    tbl_fuel   = pick_table("fuel", available)
    tbl_bmu    = pick_table("bmu", available)
    tbl_costs  = pick_table("balancing_costs", available)

    used = {"demand": tbl_demand, "fuel": tbl_fuel, "bmu": tbl_bmu, "balancing_costs": tbl_costs}

    # 1) Current demand (latest row)
    current_demand = None
    demand_24h = []
    if tbl_demand:
        # Try to be flexible about column names; we'll attempt common patterns
        sql_current = f"""
          SELECT
            CAST(timestamp AS STRING) AS ts,
            value AS demand_mw
          FROM {fq(tbl_demand)}
          WHERE timestamp IS NOT NULL
          ORDER BY timestamp DESC
          LIMIT 1
        """
        try:
            rows = codex_query(sql_current, timeout=60, max_results=1)
            if rows:
                current_demand = {
                    "value": rows[0]["demand_mw"],
                    "unit": "MW",
                    "ts": rows[0]["ts"],
                }
        except Exception:
            current_demand = None

        # Last 24h series
        sql_24h = f"""
          SELECT
            CAST(timestamp AS STRING) AS ts,
            value AS demand_mw
          FROM {fq(tbl_demand)}
          WHERE TIMESTAMP(timestamp) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
          ORDER BY timestamp
          LIMIT 500
        """
        try:
            demand_24h = codex_query(sql_24h, timeout=60, max_results=500)
        except Exception:
            demand_24h = []

    # 2) Fuel mix (skip for now - needs specific table structure)
    fuel_mix = []

    # 3) Top 10 BMUs by output (latest half-hour)
    top_bmus = []
    if tbl_bmu:
        sql_bmu = f"""
          SELECT
            bmu_id AS bmu,
            level_mw AS mw
          FROM {fq(tbl_bmu)}
          WHERE TIMESTAMP(timestamp) IS NOT NULL
          ORDER BY timestamp DESC, level_mw DESC
          LIMIT 10
        """
        try:
            top_bmus = codex_query(sql_bmu, timeout=60, max_results=20)
        except Exception:
            top_bmus = []

    # 4) Current balancing costs (latest rows)
    balancing_costs = []
    if tbl_costs:
        sql_costs = f"""
          SELECT
            CAST(settlement_date AS STRING) AS ts,
            total_daily_bsuos_charge_gbp AS cost_gbp
          FROM {fq(tbl_costs)}
          WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
          ORDER BY settlement_date
          LIMIT 100
        """
        try:
            balancing_costs = codex_query(sql_costs, timeout=60, max_results=100)
        except Exception:
            balancing_costs = []

    return JSONResponse({
        "now": datetime.utcnow().isoformat() + "Z",
        "current_demand": current_demand,
        "fuel_mix": fuel_mix,
        "demand_24h": demand_24h,
        "top_bmus": top_bmus,
        "balancing_costs": balancing_costs,
        "used_tables": used,
        "refresh_minutes": REFRESH_MIN
    })

# -------------- UI --------------
@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>UK Energy Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #0b1220; color: #e6eefc; }}
    header {{ padding: 16px 20px; background: #0e1730; position: sticky; top: 0; z-index: 10; }}
    .grid {{ display: grid; gap: 16px; padding: 16px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }}
    .card {{ background: #121a35; border: 1px solid #1e2a52; border-radius: 12px; padding: 12px 12px 20px; }}
    h1 {{ font-size: 18px; margin: 0; }}
    h2 {{ font-size: 15px; margin: 0 0 8px; color: #9fb4ff; }}
    .stat {{ font-size: 28px; font-weight: 600; }}
    .sub {{ color: #96a7cc; font-size: 13px; }}
    .footer {{ padding: 8px 16px; color: #7f96d4; font-size: 12px; }}
  </style>
</head>
<body>
<header>
  <h1>UK Energy Dashboard — {PROJECT}.{DATASET}</h1>
  <div class="sub">Auto-refreshing every <span id="rfm"></span> minutes</div>
</header>

<div class="grid">
  <div class="card">
    <h2>Current Demand</h2>
    <div id="demandStat" class="stat">—</div>
    <div class="sub" id="demandTs">—</div>
  </div>

  <div class="card">
    <h2>Generation Mix (latest)</h2>
    <canvas id="fuelPie"></canvas>
  </div>

  <div class="card" style="grid-column: 1/-1;">
    <h2>Demand — last 24 hours</h2>
    <canvas id="demandLine"></canvas>
  </div>

  <div class="card">
    <h2>Top 10 BMUs by Output (latest)</h2>
    <canvas id="bmuBar"></canvas>
  </div>

  <div class="card">
    <h2>Balancing Costs — last 30 days</h2>
    <canvas id="costsLine"></canvas>
  </div>

  <div class="card">
    <h2>Tables Used</h2>
    <pre id="tablesUsed" style="white-space:pre-wrap;"></pre>
  </div>
</div>

<div class="footer">Powered by Codex → BigQuery • {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}Z</div>

<script>
  const REFRESH_MIN = {REFRESH_MIN};
  document.getElementById('rfm').textContent = REFRESH_MIN;

  let fuelPie, demandLine, bmuBar, costsLine;

  async function fetchSummary() {{
    const r = await fetch('/api/summary');
    if (!r.ok) throw new Error('API error '+r.status);
    return r.json();
  }}

  function numFmt(x, dp=0) {{
    if (x === null || x === undefined) return '—';
    return Number(x).toLocaleString(undefined, {{ maximumFractionDigits: dp }});
  }}

  async function draw() {{
    try {{
      const data = await fetchSummary();

      // Current demand
      const cd = data.current_demand;
      document.getElementById('demandStat').textContent = cd ? numFmt(cd.value) + ' MW' : '—';
      document.getElementById('demandTs').textContent = cd ? 'as of ' + cd.ts : '—';

      // Fuel pie
      const fm = (data.fuel_mix || []).filter(x => x.fuel && x.mw != null);
      const fLabels = fm.map(x => x.fuel);
      const fData = fm.map(x => x.mw);
      if (fuelPie) fuelPie.destroy();
      fuelPie = new Chart(document.getElementById('fuelPie'), {{
        type: 'pie',
        data: {{ labels: fLabels, datasets: [{{ data: fData }}] }},
        options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
      }});

      // Demand line
      const d24 = (data.demand_24h || []).filter(x => x.ts && x.demand_mw != null);
      if (demandLine) demandLine.destroy();
      demandLine = new Chart(document.getElementById('demandLine'), {{
        type: 'line',
        data: {{
          labels: d24.map(x => x.ts),
          datasets: [{{ label: 'Demand (MW)', data: d24.map(x => x.demand_mw), tension: 0.2 }}]
        }},
        options: {{
          responsive: true,
          scales: {{
            x: {{ ticks: {{ maxTicksLimit: 8 }} }},
            y: {{ beginAtZero: true }}
          }}
        }}
      }});

      // BMU bar
      const bmus = (data.top_bmus || []).filter(x => x.bmu && x.mw != null).slice(0, 10);
      if (bmuBar) bmuBar.destroy();
      bmuBar = new Chart(document.getElementById('bmuBar'), {{
        type: 'bar',
        data: {{
          labels: bmus.map(x => x.bmu),
          datasets: [{{ label: 'MW', data: bmus.map(x => x.mw) }}]
        }},
        options: {{ responsive: true, indexAxis: 'y' }}
      }});

      // Costs line
      const costs = (data.balancing_costs || []).filter(x => x.ts && x.cost_gbp != null);
      if (costsLine) costsLine.destroy();
      costsLine = new Chart(document.getElementById('costsLine'), {{
        type: 'line',
        data: {{
          labels: costs.map(x => x.ts),
          datasets: [{{ label: 'Cost (£)', data: costs.map(x => x.cost_gbp), tension: 0.2 }}]
        }},
        options: {{ responsive: true }}
      }});

      // Tables used
      document.getElementById('tablesUsed').textContent = JSON.stringify(data.used_tables, null, 2);

    }} catch (e) {{
      console.error(e);
      alert('Failed to load dashboard data. Check server logs.');
    }}
  }}

  draw();
  setInterval(draw, REFRESH_MIN * 60 * 1000);
</script>
</body>
</html>
    """)

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}
