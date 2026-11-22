export const TIER_COLOR = { HIGH: "#bd3d34", MODERATE: "#ad6b12", LOW: "#33785e" };
export const TIER_LABEL = { HIGH: "HIGH", MODERATE: "MOD", LOW: "LOW" };

export const pct = (v, d = 0) => (v == null || Number.isNaN(v) ? "n/a" : `${(v * 100).toFixed(d)}%`);
export const half = (d) => (d.p_high - d.p_low) / 2;
export const pm = (d) => `${pct(d.p_mid)} ±${Math.round(half(d) * 100)}`;
export const rank2 = (n) => String(n).padStart(2, "0");

const STOPS = [
  [0.0, [57, 112, 132]],
  [0.35, [197, 144, 58]],
  [1.0, [189, 61, 52]],
];
/** Blue -> amber -> red ramp for p_mid in [0,1]. Values are always also printed as text. */
export function ramp(p) {
  const v = Math.min(1, Math.max(0, p));
  for (let i = 1; i < STOPS.length; i++) {
    if (v <= STOPS[i][0]) {
      const [a, ca] = STOPS[i - 1];
      const [b, cb] = STOPS[i];
      const t = (v - a) / (b - a);
      const c = ca.map((x, k) => Math.round(x + (cb[k] - x) * t));
      return `rgb(${c[0]},${c[1]},${c[2]})`;
    }
  }
  return "rgb(189,61,52)";
}
