/**
 * LOCAL ENGINE: standalone fallback with the same JSON schema as the FastAPI /api responses.
 *
 * It is NOT the LightGBM model. It evaluates the analytic generator that the synthetic training set
 * was drawn from (backend/data/spec.json), so the median and P10/P90 are the exact quantiles of that
 * generator. Driver contributions are one-at-a-time ablations against a baseline, not SHAP.
 * Same demo inputs as the backend: illustrative rainfall, exposure and boundaries.
 */
import SPEC from "./spec.json" with { type: "json" };

const G = SPEC.generator;
const Z = { p10: -1.2815515655, p90: 1.2815515655 };
const AGENCIES = ["ALL", "SDRF", "SDMA", "DISTRICT", "NGO"];
const sigmoid = (z) => 1 / (1 + Math.exp(-z));
const clip01 = (v) => Math.min(1, Math.max(0, v));
const r4 = (v) => Math.round(v * 1e4) / 1e4;
const r1 = (v) => Math.round(v * 10) / 10;
const r2 = (v) => Math.round(v * 100) / 100;

function latent(f, lead) {
  return (
    G.b0 +
    G.r3 * f.rain_3d +
    G.r1 * f.rain_1d +
    G.tr * lead * f.rain_trend -
    G.el * (f.elevation_m - G.el_ref) -
    G.rd * f.river_dist_km
  );
}

function predict(f, lead) {
  const z = latent(f, lead);
  const sd = G.sd0 + G.sd1 * lead;
  return { low: sigmoid(z + Z.p10 * sd), mid: sigmoid(z), high: sigmoid(z + Z.p90 * sd) };
}

function tierOf(priority) {
  const t = SPEC.tiers;
  return priority >= t.high ? "HIGH" : priority >= t.moderate ? "MODERATE" : "LOW";
}

function features(d, boost) {
  const rain = d.default_rain_mm.map((r) => r + boost / 3);
  return {
    rain,
    f: {
      rain_1d: rain[2],
      rain_3d: rain[0] + rain[1] + rain[2],
      rain_trend: rain[2] - rain[0],
      elevation_m: d.elevation_m,
      river_dist_km: d.river_dist_km,
    },
  };
}

function drivers(f, lead) {
  const base = SPEC.baseline;
  const p0 = predict(f, lead).mid;
  const names = ["rain_1d", "rain_3d", "rain_trend", "elevation_m", "river_dist_km"];
  return names
    .map((n) => {
      const c = p0 - predict({ ...f, [n]: base[n] }, lead).mid;
      return { n, c };
    })
    .sort((a, b) => Math.abs(b.c) - Math.abs(a.c))
    .slice(0, 3)
    .map(({ n, c }) => ({
      feature: n,
      label: SPEC.feature_labels[n],
      value: r1(f[n]),
      unit: SPEC.feature_units[n],
      contribution: r4(c),
      direction: c >= 0 ? "raises" : "lowers",
    }));
}

export function localDashboard(day = 1, rainBoost = 0) {
  const hours = [];
  for (let h = 0; h <= 72; h += 6) hours.push(h);

  const rows = SPEC.districts.map((d) => {
    const { rain, f } = features(d, rainBoost);
    const p = predict(f, day);
    const priority = p.mid * d.exposure;
    const tier = tierOf(priority);
    const borderline = tierOf(p.low * d.exposure) !== tierOf(p.high * d.exposure);
    const advisories = {};
    AGENCIES.forEach((a) => {
      advisories[a] = SPEC.advisories[tier][a].map((t) => t.replace("{district}", d.name));
    });
    return {
      id: d.id,
      name: d.name,
      centroid: d.centroid,
      population_lakh: d.population_lakh,
      exposure: d.exposure,
      rain_daily_mm: rain.map(r1),
      rain_cumulative_mm: r1(rain[0] + rain[1] + rain[2]),
      p_low: r4(clip01(p.low)),
      p_mid: r4(clip01(p.mid)),
      p_high: r4(clip01(p.high)),
      uncertainty: r4(p.high - p.low),
      priority: r4(priority),
      tier,
      borderline,
      at_risk_lakh: r2(d.population_lakh * d.floodplain_frac * p.mid),
      drivers: drivers(f, day),
      advisories,
      forecast: hours.map((h) => {
        const q = predict(f, h / 24);
        return { hour: h, low: r4(q.low), mid: r4(q.mid), high: r4(q.high) };
      }),
    };
  });

  rows.sort((a, b) => b.priority - a.priority);
  rows.forEach((r, i) => (r.rank = i + 1));

  return {
    engine: "local-engine",
    day,
    rain_boost: rainBoost,
    generated_at: new Date().toISOString().slice(0, 19),
    data_note: "DEMO DATA: SYNTHETIC TRAINING SET; illustrative district inputs; schematic boundaries",
    districts: rows,
    geojson: {
      type: "FeatureCollection",
      features: SPEC.districts.map((d) => ({
        type: "Feature",
        properties: { id: d.id, name: d.name },
        geometry: { type: "Polygon", coordinates: [d.polygon] },
      })),
    },
    summary: {
      alerts: rows.filter((r) => r.tier !== "LOW").length,
      high: rows.filter((r) => r.tier === "HIGH").length,
      moderate: rows.filter((r) => r.tier === "MODERATE").length,
      low: rows.filter((r) => r.tier === "LOW").length,
    },
  };
}

/** Schematic Brahmaputra corridor. Same geometry rules as backend/main.py. NOT real SAR. */
export function localExtent(day = 1, rainBoost = 0) {
  const dash = localDashboard(day, rainBoost);
  const cents = dash.districts.map((r) => ({ c: r.centroid, p: r.p_mid }));
  const line = SPEC.river_centerline;
  const left = [];
  const right = [];
  line.forEach(([x, y], i) => {
    const a = line[Math.max(i - 1, 0)];
    const b = line[Math.min(i + 1, line.length - 1)];
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const n = Math.hypot(dx, dy) || 1;
    const nx = -dy / n;
    const ny = dx / n;
    let near = cents[0];
    let best = Infinity;
    cents.forEach((c) => {
      const dd = (c.c[1] - x) ** 2 + (c.c[0] - y) ** 2;
      if (dd < best) {
        best = dd;
        near = c;
      }
    });
    const w = 0.035 * (0.6 + 0.55 * day) * (0.5 + 1.2 * near.p) * (1 + 0.25 * Math.sin(i * 1.7));
    left.push([r4(x + nx * w), r4(y + ny * w)]);
    right.push([r4(x - nx * w), r4(y - ny * w)]);
  });
  const ring = [...left, ...right.reverse(), left[0]];
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { day, kind: "SCHEMATIC_INUNDATION_CORRIDOR", illustrative: true },
        geometry: { type: "Polygon", coordinates: [ring] },
      },
    ],
  };
}

/** Health payload for offline mode: nothing is computed here, so metrics are null. */
export function localHealth() {
  const dash = localDashboard(1, 0);
  return {
    status: "offline",
    engine: "local-engine",
    metrics: null,
    feature_importance: null,
    live_alerts: dash.summary.alerts,
    not_computed: { sar_bhuvan_overlap: null, satellites_operational: null },
    data_note: "DEMO DATA: SYNTHETIC TRAINING SET",
  };
}

export { SPEC, AGENCIES };
