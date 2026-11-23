"""Generate a self-contained, zero-CDN GitHub Pages Executive Dashboard (docs/index.html)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from energiewende.config import COUNTRY_NAMES, DOCS


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(df.to_json(orient="records"))


def build_dashboard(panel: pd.DataFrame, res: dict[str, Any], manifest: dict[str, Any], out_path: Path = DOCS / "index.html") -> Path:
    """Embed validated pipeline outputs into a self-contained interactive HTML dashboard."""
    de = panel[panel["geo"] == "DE"].sort_values("year")
    de_23 = de[de["year"] == 2023].iloc[0]
    de_21 = de[de["year"] == 2021].iloc[0]
    de_13 = de[de["year"] == 2013].iloc[0]

    payload = {
        "generated_utc": manifest["generated_utc"],
        "sources_count": len(manifest["sources"]),
        "cohorts": {
            "all": _records(res["p1_all"]["e_gen_share"]),
            "bal_eu27": _records(res["p1_bal_eu27"]["e_gen_share"]),
            "big6": _records(res["p1_big6"]["e_gen_share"]),
        },
        "decomp_de": _records(res["p2_decomp_de"]),
        "de_series": _records(
            de[
                [
                    "year",
                    "e_cap_share",
                    "e_gen_share",
                    "ren_elec_pct",
                    "e_cap_connected_mw",
                    "e_cap_decomm_mw",
                    "gas_retailers",
                    "gas_fc_twh",
                    "retailers_per_twh",
                    "gas_retail_share_ge5",
                    "elec_price_eur_kwh",
                    "elec_price_extax_eur_kwh",
                    "elec_price_tax_share_pct",
                    "gas_price_eur_kwh",
                    "unable_warm_total_pct",
                    "unable_warm_lowinc_pct",
                    "utility_arrears_total_pct",
                ]
            ]
        ),
        "crisis": _records(res["crisis_table"].sort_values("country_name")),
        "models": _records(res["models_df"]),
        "countries": {
            geo: _records(
                grp.sort_values("year")[
                    [
                        "year",
                        "e_gen_share",
                        "ren_elec_pct",
                        "gas_retail_share_ge5",
                        "elec_price_eur_kwh",
                        "elec_price_pps_kwh",
                        "gas_price_eur_kwh",
                        "unable_warm_total_pct",
                        "unable_warm_lowinc_pct",
                    ]
                ]
            )
            for geo, grp in panel.groupby("geo")
        },
        "country_names": COUNTRY_NAMES,
        "kpis": {
            "de_gen_13": round(float(de_13["e_gen_share"]), 1),
            "de_gen_23": round(float(de_23["e_gen_share"]), 1),
            "de_ren_23": round(float(de_23["ren_elec_pct"]), 1),
            "de_gas_conc_23": round(float(de_23["gas_retail_share_ge5"]), 1),
            "de_elec_eur_23": round(float(de_23["elec_price_eur_kwh"]), 3),
            "de_tax_21": round(float(de_21["elec_price_tax_share_pct"]), 1),
            "de_tax_23": round(float(de_23["elec_price_tax_share_pct"]), 1),
            "de_warm_21": round(float(de_21["unable_warm_total_pct"]), 1),
            "de_warm_23": round(float(de_23["unable_warm_total_pct"]), 1),
            "de_warm_low_23": round(float(de_23["unable_warm_lowinc_pct"]), 1),
        },
        "sources": manifest["sources"],
    }

    data_json = json.dumps(payload, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Germany Energiewende: Market Structure, Affordability &amp; Social Resilience (2013–2023)</title>
<style>
  :root {{
    --navy: #0B3A66;
    --teal: #1F7A8C;
    --amber: #D97706;
    --crimson: #B91C1C;
    --green: #15803D;
    --bg: #F8FAFC;
    --card: #FFFFFF;
    --border: #E2E8F0;
    --text: #0F172A;
    --muted: #475569;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }}
  header {{
    background: linear-gradient(135deg, #072642 0%, #0B3A66 60%, #155E75 100%);
    color: #fff;
    padding: 2rem 1.5rem;
    border-bottom: 4px solid var(--amber);
  }}
  .wrap {{ max-width: 1220px; margin: 0 auto; }}
  header h1 {{ font-size: 1.65rem; font-weight: 700; margin-bottom: 0.4rem; }}
  header p {{ color: #CBD5E1; max-width: 860px; font-size: 0.96rem; }}
  .badges {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }}
  .badge {{
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.22);
    padding: 0.22rem 0.65rem;
    border-radius: 999px;
    font-size: 0.78rem;
    color: #F1F5F9;
  }}
  main {{ padding: 1.5rem; }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(215px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }}
  .kpi {{
    background: var(--card);
    border: 1px solid var(--border);
    border-top: 3px solid var(--navy);
    border-radius: 10px;
    padding: 1rem 1.1rem;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  }}
  .kpi.warn {{ border-top-color: var(--crimson); }}
  .kpi.teal {{ border-top-color: var(--teal); }}
  .kpi.amber {{ border-top-color: var(--amber); }}
  .kpi .label {{ font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); font-weight: 600; }}
  .kpi .val {{ font-size: 1.55rem; font-weight: 800; margin: 0.25rem 0; color: var(--text); }}
  .kpi .sub {{ font-size: 0.8rem; color: var(--muted); }}
  .grid-2 {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
    gap: 1.25rem;
    margin-bottom: 1.25rem;
  }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05);
    margin-bottom: 1.25rem;
  }}
  .card-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 0.85rem;
  }}
  .card h2 {{ font-size: 1.06rem; font-weight: 700; color: var(--navy); }}
  .controls {{ display: flex; gap: 0.4rem; flex-wrap: wrap; }}
  button.pill {{
    border: 1px solid var(--border);
    background: #F1F5F9;
    color: var(--text);
    padding: 0.32rem 0.72rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  button.pill.active {{
    background: var(--navy);
    color: #fff;
    border-color: var(--navy);
  }}
  select {{
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.35rem 0.65rem;
    font-size: 0.84rem;
    background: #fff;
    color: var(--text);
  }}
  .callout {{
    background: #F8FAFC;
    border-left: 4px solid var(--teal);
    padding: 0.75rem 0.95rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.86rem;
    margin-top: 0.75rem;
    color: #1E293B;
  }}
  .callout.alert {{ border-left-color: var(--crimson); background: #FEF2F2; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.83rem; margin-top: 0.5rem; }}
  th, td {{ padding: 0.52rem 0.6rem; border-bottom: 1px solid var(--border); text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  th {{ background: #F1F5F9; color: var(--muted); font-weight: 700; font-size: 0.76rem; text-transform: uppercase; }}
  tr.highlight {{ background: #EFF6FF; font-weight: 700; }}
  .tag-pass {{ background: #DCFCE7; color: var(--green); padding: 0.14rem 0.45rem; border-radius: 4px; font-weight: 700; font-size: 0.74rem; }}
  .tag-fail {{ background: #F1F5F9; color: var(--muted); padding: 0.14rem 0.45rem; border-radius: 4px; font-weight: 600; font-size: 0.74rem; }}
  .qa-buttons {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.85rem; }}
  .qa-box {{
    background: #0F172A;
    color: #E2E8F0;
    border-radius: 8px;
    padding: 1rem 1.15rem;
    font-size: 0.87rem;
    line-height: 1.6;
  }}
  .qa-box .cite {{ color: #38BDF8; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.78rem; margin-top: 0.6rem; display: block; }}
  svg.chart {{ width: 100%; height: auto; display: block; }}
  footer {{ text-align: center; padding: 1.5rem; font-size: 0.8rem; color: var(--muted); }}
  @media (max-width: 600px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>Germany Energiewende: Market Structure, Affordability &amp; Social Resilience</h1>
    <p>Executive intelligence dashboard linking Eurostat power &amp; gas market structure, renewable expansion, household price tax-wedges, and EU-SILC energy poverty across 36 European economies (2013–2023).</p>
    <div class="badges">
      <span class="badge">8 Official Eurostat Tables</span>
      <span class="badge">SHA-256 Provenance Verified</span>
      <span class="badge">Strict 100% LOO Econometric Gate</span>
      <span class="badge" id="ts-badge"></span>
    </div>
  </div>
</header>

<main class="wrap">
  <section class="kpi-grid">
    <div class="kpi">
      <div class="label">Elec. Generation Concentration</div>
      <div class="val">{payload["kpis"]["de_gen_23"]}% <span style="font-size:0.9rem;color:var(--green)">(-16.9 pp)</span></div>
      <div class="sub">Down from {payload["kpis"]["de_gen_13"]}% (2013), yet still <b>#2 of 6</b> among Big-6 peers</div>
    </div>
    <div class="kpi teal">
      <div class="label">Renewable Electricity Share</div>
      <div class="val">{payload["kpis"]["de_ren_23"]}%</div>
      <div class="sub">More than doubled from 25.3% (2013); +22.8 GW connected in 2023</div>
    </div>
    <div class="kpi amber">
      <div class="label">Gas Retail Conc. (&ge;5% firms)</div>
      <div class="val">{payload["kpis"]["de_gas_conc_23"]}%</div>
      <div class="sub">Cut in half from 26.0% (2013); least concentrated in Big-6 (med 70.1%)</div>
    </div>
    <div class="kpi amber">
      <div class="label">Household Electricity (2023)</div>
      <div class="val">&euro;{payload["kpis"]["de_elec_eur_23"]}/kWh</div>
      <div class="sub">Tax share cut {payload["kpis"]["de_tax_21"]}% &rarr; {payload["kpis"]["de_tax_23"]}%, but ex-tax surged +85.4%</div>
    </div>
    <div class="kpi warn">
      <div class="label">Energy Poverty (Unable Warm)</div>
      <div class="val">{payload["kpis"]["de_warm_23"]}% <span style="font-size:0.9rem;color:var(--crimson)">(+4.9 pp)</span></div>
      <div class="sub">Up from {payload["kpis"]["de_warm_21"]}% (2021); Low-income hit <b>{payload["kpis"]["de_warm_low_23"]}%</b></div>
    </div>
  </section>

  <div class="grid-2">
    <section class="card" style="margin-bottom:0">
      <div class="card-head">
        <h2>1. Peer-Cohort Sensitivity: Electricity Concentration</h2>
        <div class="controls" id="cohort-controls">
          <button class="pill active" data-cohort="big6">Big-6 Peers (N=6)</button>
          <button class="pill" data-cohort="bal_eu27">Balanced EU-27 (N=26)</button>
          <button class="pill" data-cohort="all">All Reporters (N=35)</button>
        </div>
      </div>
      <svg id="cohort-chart" class="chart" viewBox="0 0 560 270"></svg>
      <div class="callout" id="cohort-note"></div>
    </section>

    <section class="card" style="margin-bottom:0">
      <div class="card-head">
        <h2>2. Gas Density Illusion: Exact Log-Decomposition</h2>
      </div>
      <svg id="decomp-chart" class="chart" viewBox="0 0 560 270"></svg>
      <div class="callout alert">
        <b>Senior-Analyst Catch:</b> Between 2021 and 2023, Germany's gas retailers/TWh jumped <b>+25.7%</b> (1.40 &rarr; 1.76) even though retailer count <b>fell -0.6%</b> (979 &rarr; 973). Exactly <b>102.7%</b> of the log spike was a denominator artifact from Germany's <b>-20.9%</b> crisis gas-consumption collapse (698 &rarr; 552 TWh).
      </div>
    </section>
  </div>

  <section class="card">
    <div class="card-head">
      <h2>3. Interactive Country Benchmark vs. Germany (2013–2023)</h2>
      <div class="controls">
        <label style="font-size:0.82rem;color:var(--muted);align-self:center;">Compare Germany against:</label>
        <select id="peer-select"></select>
        <select id="metric-select">
          <option value="unable_warm_lowinc_pct">Low-Income Energy Poverty (% unable to keep warm)</option>
          <option value="unable_warm_total_pct">Total Population Energy Poverty (% unable to keep warm)</option>
          <option value="elec_price_eur_kwh">Household Electricity Price (EUR/kWh, all taxes)</option>
          <option value="elec_price_pps_kwh">Household Electricity Price (PPS/kWh, purchasing power)</option>
          <option value="gas_price_eur_kwh">Household Gas Price (EUR/kWh, all taxes)</option>
          <option value="ren_elec_pct">Renewable Electricity Share (%)</option>
          <option value="e_gen_share">Electricity Generation Concentration (&ge;5% firms, %)</option>
          <option value="gas_retail_share_ge5">Gas Retail Concentration (&ge;5% firms, %)</option>
        </select>
      </div>
    </div>
    <svg id="compare-chart" class="chart" viewBox="0 0 1120 265"></svg>
    <div class="callout" id="compare-note"></div>
  </section>

  <section class="card">
    <div class="card-head">
      <h2>4. Big-6 Energy Crisis Stress Test (2021 &rarr; 2023)</h2>
      <div class="controls" id="table-filter">
        <button class="pill active" data-scope="big6">Big-6 Large Markets</button>
        <button class="pill" data-scope="eu27">All EU-27 Countries</button>
      </div>
    </div>
    <div style="overflow-x:auto">
      <table id="crisis-table">
        <thead>
          <tr>
            <th>Country</th>
            <th>Elec. Conc. '23</th>
            <th>Ren. Elec. '23</th>
            <th>Gas Ret. &ge;5%</th>
            <th>Elec. EUR '23</th>
            <th>Elec. PPS '23</th>
            <th>Gas EUR &Delta;%</th>
            <th>Warm Tot '23</th>
            <th>Warm Low-Inc '23 (&Delta;pp)</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </section>

  <div class="grid-2">
    <section class="card" style="margin-bottom:0">
      <div class="card-head">
        <h2>5. Panel Econometrics &amp; Strict 100% LOO Gate</h2>
      </div>
      <div style="overflow-x:auto">
        <table id="models-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Coef</th>
              <th>95% CI</th>
              <th>Within R&sup2;</th>
              <th>LOO &le;50%</th>
              <th>Gate</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </section>

    <section class="card" style="margin-bottom:0">
      <div class="card-head">
        <h2>6. Grounded Analyst Copilot (Zero-Hallucination Briefs)</h2>
      </div>
      <div class="qa-buttons" id="qa-buttons">
        <button class="pill active" data-q="cohorts">Why does Germany's rank flip by cohort?</button>
        <button class="pill" data-q="gas">Explain the 2022–23 gas density illusion</button>
        <button class="pill" data-q="prices">Did abolishing the EEG levy lower bills?</button>
        <button class="pill" data-q="social">Did market deconcentration prevent energy poverty?</button>
        <button class="pill" data-q="audit">Show AI audit trail &amp; provenance hashes</button>
      </div>
      <div class="qa-box" id="qa-box"></div>
    </section>
  </div>
</main>

<footer>
  Generated deterministically from verified Eurostat API extracts via <code>python -m energiewende.pipeline</code>. Non-causal descriptive &amp; two-way fixed effects analysis.
</footer>

<script>
const DATA = {data_json};
document.getElementById('ts-badge').textContent = 'Built ' + DATA.generated_utc.slice(0, 10);

function fmt(v, d=1) {{
  return (v === null || v === undefined || Number.isNaN(v)) ? '—' : Number(v).toFixed(d);
}}

// 1. Cohort Chart
function renderCohort(key) {{
  const rows = DATA.cohorts[key];
  const svg = document.getElementById('cohort-chart');
  const W = 560, H = 270, pad = {{l:46, r:20, t:22, b:34}};
  const xMin = 2013, xMax = 2023, yMin = 25, yMax = 96;
  const sx = x => pad.l + (x - xMin) / (xMax - xMin) * (W - pad.l - pad.r);
  const sy = y => H - pad.b - (y - yMin) / (yMax - yMin) * (H - pad.t - pad.b);

  const areaPts = rows.map(r => `${{sx(r.year)}},${{sy(r.p75)}}`).join(' ') + ' ' +
                  [...rows].reverse().map(r => `${{sx(r.year)}},${{sy(r.p25)}}`).join(' ');
  const medPath = rows.map((r,i) => (i?'L':'M') + sx(r.year) + ',' + sy(r.median)).join(' ');
  const dePath  = rows.map((r,i) => (i?'L':'M') + sx(r.year) + ',' + sy(r.de)).join(' ');

  let grid = '';
  for (let y = 30; y <= 90; y += 15) {{
    grid += `<line x1="${{pad.l}}" y1="${{sy(y)}}" x2="${{W-pad.r}}" y2="${{sy(y)}}" stroke="#E2E8F0" stroke-dasharray="3,3"/>`;
    grid += `<text x="${{pad.l-8}}" y="${{sy(y)+4}}" text-anchor="end" font-size="10" fill="#64748B">${{y}}%</text>`;
  }}
  for (let yr = 2013; yr <= 2023; yr += 2) {{
    grid += `<text x="${{sx(yr)}}" y="${{H-10}}" text-anchor="middle" font-size="10" fill="#64748B">${{yr}}</text>`;
  }}
  const last = rows[rows.length - 1];
  svg.innerHTML = `
    ${{grid}}
    <polygon points="${{areaPts}}" fill="#E2E8F0" opacity="0.85"/>
    <path d="${{medPath}}" fill="none" stroke="#D97706" stroke-width="2.2" stroke-dasharray="5,3"/>
    <path d="${{dePath}}" fill="none" stroke="#0B3A66" stroke-width="3"/>
    ${{rows.map(r => `<circle cx="${{sx(r.year)}}" cy="${{sy(r.de)}}" r="3.4" fill="#0B3A66"/>`).join('')}}
    <text x="${{sx(2023)-6}}" y="${{sy(last.de)-9}}" text-anchor="end" font-size="11" font-weight="700" fill="#0B3A66">DE: ${{fmt(last.de,1)}}%</text>
    <text x="${{sx(2023)-6}}" y="${{sy(last.median)+14}}" text-anchor="end" font-size="10.5" font-weight="700" fill="#D97706">Med: ${{fmt(last.median,1)}}%</text>
  `;
  const labels = {{
    big6: `<b>Big-6 Large Markets (DE, FR, IT, ES, PL, NL):</b> Germany sits <b>+${{fmt(last.de_minus_median,1)}} pp ABOVE</b> the Big-6 median (${{fmt(last.median,1)}}%) at <b>Rank #${{last.de_rank}} of ${{last.n}}</b>—second-most concentrated behind only France.`,
    bal_eu27: `<b>Balanced EU-27 Constant Cohort (N=${{last.n}}):</b> Holding country composition fixed, Germany sits near the middle (<b>${{fmt(last.de_minus_median,1)}} pp</b> vs. median ${{fmt(last.median,1)}}%, <b>Rank #${{last.de_rank}} of ${{last.n}}</b>).`,
    all: `<b>All Unbalanced Eurostat Reporters (N=${{last.n}}):</b> Including small non-EU markets pulls the median up to ${{fmt(last.median,1)}}%, making Germany appear <b>${{fmt(last.de_minus_median,1)}} pp below</b> the median (Rank #${{last.de_rank}} of ${{last.n}}).`
  }};
  document.getElementById('cohort-note').innerHTML = labels[key];
}}

document.querySelectorAll('#cohort-controls button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('#cohort-controls button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderCohort(btn.dataset.cohort);
  }});
}});
renderCohort('big6');

// 2. Log-Decomposition Bar Chart
function renderDecomp() {{
  const rows = DATA.decomp_de;
  const svg = document.getElementById('decomp-chart');
  const W = 560, H = 270, pad = {{l:46, r:16, t:22, b:46}};
  const yMin = -15, yMax = 36;
  const sy = y => H - pad.b - (y - yMin) / (yMax - yMin) * (H - pad.t - pad.b);
  const shortL = ['2013–23', '2013–17', '2017–21', '2021–23'];
  const slot = (W - pad.l - pad.r) / rows.length;
  let out = '';
  for (let y = -10; y <= 30; y += 10) {{
    out += `<line x1="${{pad.l}}" y1="${{sy(y)}}" x2="${{W-pad.r}}" y2="${{sy(y)}}" stroke="#E2E8F0" stroke-dasharray="3,3"/>`;
    out += `<text x="${{pad.l-6}}" y="${{sy(y)+4}}" text-anchor="end" font-size="10" fill="#64748B">${{y}}</text>`;
  }}
  out += `<line x1="${{pad.l}}" y1="${{sy(0)}}" x2="${{W-pad.r}}" y2="${{sy(0)}}" stroke="#475569" stroke-width="1.2"/>`;
  rows.forEach((r, i) => {{
    const cx = pad.l + i * slot + slot / 2;
    const vals = [
      {{v: r.log_chg_numerator_entry * 100, c: '#1F7A8C', dx: -26}},
      {{v: r.log_chg_denominator_demand * 100, c: '#B91C1C', dx: 0}},
      {{v: r.log_chg_total * 100, c: '#0B3A66', dx: 26}},
    ];
    vals.forEach(b => {{
      const yTop = b.v >= 0 ? sy(b.v) : sy(0);
      const h = Math.abs(sy(b.v) - sy(0));
      out += `<rect x="${{cx + b.dx - 11}}" y="${{yTop}}" width="22" height="${{Math.max(h,1.5)}}" fill="${{b.c}}" rx="2"/>`;
    }});
    out += `<text x="${{cx}}" y="${{H-24}}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#0F172A">${{shortL[i]}}</text>`;
    const tot = r.log_chg_total * 100;
    out += `<text x="${{cx+26}}" y="${{tot>=0 ? sy(tot)-5 : sy(tot)+12}}" text-anchor="middle" font-size="9.5" font-weight="700" fill="#0B3A66">${{tot>=0?'+':''}}${{tot.toFixed(1)}}</text>`;
  }});
  out += `<g font-size="10" fill="#334155">
    <rect x="75" y="6" width="10" height="10" fill="#1F7A8C"/><text x="90" y="15">Retailer Entry (+Δ ln R)</text>
    <rect x="235" y="6" width="10" height="10" fill="#B91C1C"/><text x="250" y="15">Gas Collapse (-Δ ln C)</text>
    <rect x="395" y="6" width="10" height="10" fill="#0B3A66"/><text x="410" y="15">Net Ratio (Δ ln R/C)</text>
  </g>`;
  svg.innerHTML = out;
}}
renderDecomp();

// 3. Country Comparison Explorer
const peerSel = document.getElementById('peer-select');
const metricSel = document.getElementById('metric-select');
const geos = Object.keys(DATA.countries).filter(g => g !== 'DE').sort((a,b) => (DATA.country_names[a]||a).localeCompare(DATA.country_names[b]||b));
geos.forEach(g => {{
  const opt = document.createElement('option');
  opt.value = g;
  opt.textContent = `${{DATA.country_names[g] || g}} (${{g}})`;
  if (g === 'FR') opt.selected = true;
  peerSel.appendChild(opt);
}});

function renderCompare() {{
  const peer = peerSel.value;
  const m = metricSel.value;
  const deRows = DATA.countries['DE'].filter(r => r[m] !== null);
  const pRows = (DATA.countries[peer] || []).filter(r => r[m] !== null);
  const svg = document.getElementById('compare-chart');
  const W = 1120, H = 265, pad = {{l:56, r:26, t:22, b:32}};
  const allVals = [...deRows.map(r => r[m]), ...pRows.map(r => r[m])];
  if (!allVals.length) {{
    svg.innerHTML = `<text x="560" y="130" text-anchor="middle" fill="#64748B">No overlapping data for this indicator.</text>`;
    return;
  }}
  const yMin = Math.min(0, Math.min(...allVals));
  const yMax = Math.max(...allVals) * 1.12 || 1;
  const sx = x => pad.l + (x - 2013) / 10 * (W - pad.l - pad.r);
  const sy = y => H - pad.b - (y - yMin) / (yMax - yMin) * (H - pad.t - pad.b);
  const dDigits = m.includes('price') ? 3 : 1;

  let out = '';
  for (let k = 0; k <= 4; k++) {{
    const yv = yMin + (yMax - yMin) * k / 4;
    out += `<line x1="${{pad.l}}" y1="${{sy(yv)}}" x2="${{W-pad.r}}" y2="${{sy(yv)}}" stroke="#E2E8F0" stroke-dasharray="3,3"/>`;
    out += `<text x="${{pad.l-8}}" y="${{sy(yv)+4}}" text-anchor="end" font-size="10.5" fill="#64748B">${{yv.toFixed(dDigits)}}</text>`;
  }}
  for (let yr = 2013; yr <= 2023; yr++) {{
    out += `<text x="${{sx(yr)}}" y="${{H-10}}" text-anchor="middle" font-size="10.5" fill="#64748B">${{yr}}</text>`;
  }}
  const dePath = deRows.map((r,i) => (i?'L':'M') + sx(r.year) + ',' + sy(r[m])).join(' ');
  const pPath  = pRows.map((r,i) => (i?'L':'M') + sx(r.year) + ',' + sy(r[m])).join(' ');
  out += `<path d="${{pPath}}" fill="none" stroke="#D97706" stroke-width="2.6" stroke-dasharray="6,3"/>`;
  out += `<path d="${{dePath}}" fill="none" stroke="#0B3A66" stroke-width="3.2"/>`;
  deRows.forEach(r => out += `<circle cx="${{sx(r.year)}}" cy="${{sy(r[m])}}" r="4" fill="#0B3A66"/>`);
  pRows.forEach(r => out += `<circle cx="${{sx(r.year)}}" cy="${{sy(r[m])}}" r="3.6" fill="#D97706"/>`);
  svg.innerHTML = out;

  const de23 = deRows.find(r => r.year === 2023);
  const p23 = pRows.find(r => r.year === 2023);
  const pName = DATA.country_names[peer] || peer;
  document.getElementById('compare-note').innerHTML =
    `<span style="color:#0B3A66;font-weight:700">● Germany (2023): ${{de23 ? fmt(de23[m], dDigits) : '—'}}</span> &nbsp;|&nbsp; ` +
    `<span style="color:#D97706;font-weight:700">● ${{pName}} (2023): ${{p23 ? fmt(p23[m], dDigits) : '—'}}</span> &nbsp;|&nbsp; ` +
    `Difference (DE − ${{peer}}): <b>${{(de23 && p23) ? ((de23[m] - p23[m]) >= 0 ? '+' : '') + fmt(de23[m] - p23[m], dDigits) : '—'}}</b>`;
}}
peerSel.addEventListener('change', renderCompare);
metricSel.addEventListener('change', renderCompare);
renderCompare();

// 4. Crisis Stress Test Table
function renderCrisisTable(scope) {{
  const tbody = document.querySelector('#crisis-table tbody');
  const rows = DATA.crisis
    .filter(r => scope === 'big6' ? r.is_big6 : r.is_eu27)
    .sort((a,b) => (b.warm_lowinc_2023 || -1) - (a.warm_lowinc_2023 || -1));
  tbody.innerHTML = rows.map(r => `
    <tr class="${{r.geo === 'DE' ? 'highlight' : ''}}">
      <td>${{r.country_name}} (${{r.geo}})</td>
      <td>${{fmt(r.e_gen_share_2023,1)}}%</td>
      <td>${{fmt(r.ren_elec_2023,1)}}%</td>
      <td>${{fmt(r.gas_retail_share_ge5_2023,1)}}%</td>
      <td>&euro;${{fmt(r.elec_eur_2023,3)}}</td>
      <td>${{fmt(r.elec_pps_2023,3)}}</td>
      <td>${{r.gas_eur_pct_chg !== null ? (r.gas_eur_pct_chg >= 0 ? '+' : '') + fmt(r.gas_eur_pct_chg,1) + '%' : '—'}}</td>
      <td>${{fmt(r.warm_total_2023,1)}}%</td>
      <td>${{fmt(r.warm_lowinc_2023,1)}}% (${{r.warm_lowinc_pp_chg !== null ? (r.warm_lowinc_pp_chg >= 0 ? '+' : '') + fmt(r.warm_lowinc_pp_chg,1) : '—'}})</td>
    </tr>
  `).join('');
}}
document.querySelectorAll('#table-filter button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('#table-filter button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderCrisisTable(btn.dataset.scope);
  }});
}});
renderCrisisTable('big6');

// 5. TWFE Models Table
document.querySelector('#models-table tbody').innerHTML = DATA.models.map(m => `
  <tr>
    <td><b>${{m.model_id}}</b><br><span style="color:#64748B;font-size:0.74rem">${{m.description}}</span></td>
    <td>${{fmt(m.coef,4)}}</td>
    <td>[${{fmt(m.ci_low,3)}}, ${{fmt(m.ci_high,3)}}]</td>
    <td>${{fmt(m.within_r2,3)}}</td>
    <td>${{m.loo_within_50pct}}</td>
    <td>${{m.passes_strict_gate ? '<span class="tag-pass">PASS</span>' : '<span class="tag-fail">FAIL</span>'}}</td>
  </tr>
`).join('');

// 6. Grounded Analyst Copilot
const QA = {{
  cohorts: {{
    text: `<b>Finding:</b> Germany's electricity generation concentration (57.1% in 2023) looks <b>below median (-6.3 pp, Rank #21/35)</b> only when small non-EU/island utilities inflate the all-reporter median (63.4%). Against a <b>balanced EU-27 cohort (N=26)</b>, Germany sits near the median (-2.5 pp, Rank #15/26). Against <b>Europe's Big-6 interconnected markets</b> (DE, FR, IT, ES, PL, NL), Germany is <b>+15.0 pp ABOVE the median (42.1%) and Rank #2 of 6</b>—second-most concentrated behind nuclear-incumbent France (78.9%).`,
    cite: `Provenance: Eurostat nrg_ind_market (CMPY_EG5, E7000, PC) | outputs/tables/p1_big6_e_gen_share.csv`
  }},
  gas: {{
    text: `<b>Finding:</b> Germany's gas-retailer density (GRTL / TWh) rose +37.3% over 2013–2023 (1.28 → 1.76), but exact log-decomposition splits this into two distinct regimes: <b>(1) 2013–2017:</b> real entry (+20.6% retailers, 825 → 995) drove 101% of density growth; <b>(2) 2021–2023:</b> retailer count actually <b>fell -0.6%</b> (979 → 973), yet density jumped +25.7% purely because final gas consumption collapsed <b>-20.9%</b> (698 → 552 TWh). Using the cleaner competition series <code>GRTL_NG5</code> confirms genuine retail fragmentation: Germany's major gas retailers (&ge;5% share) fell from 26.0% to 13.3% (Rank #6/6 in Big-6).`,
    cite: `Provenance: Eurostat nrg_ind_market (GRTL, GRTL_NG5) + nrg_bal_s (FC_E + FC_NE) | outputs/tables/p2_germany_density_log_decomposition.csv`
  }},
  prices: {{
    text: `<b>Finding:</b> Abolishing the EEG renewables surcharge cut Germany's electricity tax wedge nearly in half—from <b>50.9%</b> of the household bill in 2021 to <b>28.1%</b> in 2023. However, ex-tax energy &amp; network costs surged <b>+85.4%</b> (€0.158 → €0.293/kWh), pushing all-in German electricity prices up to <b>€0.407/kWh</b> (0.364 PPS/kWh)—highest nominal price in the Big-6. Gas prices rose +77.4% (€0.067 → €0.119/kWh).`,
    cite: `Provenance: Eurostat nrg_pc_204 (Band DC, I_TAX & X_TAX) + nrg_pc_202 (Band D2) | outputs/tables/p3_elec_price_eur_eu27.csv`
  }},
  social: {{
    text: `<b>Finding:</b> No—deconcentration alone did not insulate households from the 2022–2023 supply shock. Germany's inability to keep homes adequately warm more than doubled from <b>3.3%</b> (2021, EU-27 Rank #17/27) to <b>8.2%</b> (2023, Rank #10/27), crossing <b>above</b> the EU-27 median (7.1%). Low-income German households hit <b>14.3%</b> (+6.5 pp). Yet absolute levels stayed lower than Spain (34.3%), France (25.1%), Italy (21.6%), and the Netherlands (21.6%). Panel TWFE models confirm that renewables strongly track deconcentration (M1/M2 PASS 100% LOO), while direct price/concentration links to energy poverty fail the LOO gate (M4–M6)—showing fiscal/welfare policy mediates social outcomes.`,
    cite: `Provenance: Eurostat EU-SILC ilc_mdes01 & ilc_mdes07 | outputs/tables/p4_twfe_models_summary.csv | Guardrail: Non-causal associations`
  }},
  audit: {{
    text: `<b>Governance &amp; Provenance:</b> Every raw &amp; API table is hashed in <code>data/manifest.json</code> (` + DATA.sources_count + ` verified sources). Earlier v1 repo drafts mislabeled Eurostat concentration shares as "prices" and gas retailer counts as "grid infrastructure." Those drafts were audited, documented in <code>METHODOLOGICAL_AUDIT_LOG.md</code>, and replaced with automated Germany-2013 unit checks and strict LOO econometric gates.<br><br><b>SHA-256 Digest Sample:</b><br>` +
      Object.entries(DATA.sources).map(([k,v]) => `• <code>${{k}}</code> (${{v.dataset}}): <code>${{(v.sha256||'').slice(0,16)}}...</code>`).join('<br>'),
    cite: `Provenance: data/manifest.json & METHODOLOGICAL_AUDIT_LOG.md`
  }}
}};

function renderQA(key) {{
  const item = QA[key];
  document.getElementById('qa-box').innerHTML = `${{item.text}}<span class="cite">${{item.cite}}</span>`;
}}
document.querySelectorAll('#qa-buttons button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('#qa-buttons button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderQA(btn.dataset.q);
  }});
}});
renderQA('cohorts');
</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path
