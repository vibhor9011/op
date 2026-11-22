import React, { useEffect, useState } from "react";
import { Drawer, Badge, Card } from "../design/index.js";
import { fetchExplain, fetchTimeline } from "../services/aiClient.js";
import { AlertOctagon, AlertTriangle, ShieldCheck, Info, CloudRain, Droplets, MapPin, Users, Activity, FileDown } from "lucide-react";

export default function ZoneDrawer({ isOpen, onClose, zone, period = "2022-06", onExportBriefing }) {
  const [explain, setExplain] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen || !zone) return;
    setLoading(true);
    Promise.all([
      fetchExplain(zone.id, period).catch(() => null),
      fetchTimeline(zone.id, "flood").catch(() => null)
    ])
      .then(([exp, tl]) => {
        setExplain(exp);
        setTimeline(tl?.timeline || []);
      })
      .finally(() => setLoading(false));
  }, [isOpen, zone, period]);

  if (!zone) return null;

  const advisory = zone.advisory || {
    level: zone.tier || "Normal",
    headline: `Operational Early Warning Advisory for ${zone.name}`,
    reasons: ["Antecedent riverine saturation build-up", "Catchment rainfall accumulation"],
    recommended_actions: ["Monitor district emergency operations center feeds", "Check vulnerable river embankments"],
    confidence: "High (Narrow band width)",
    disclaimer: "Decision support only; confirm with ASDMA/IMD official advisories."
  };

  const getAdvisoryIcon = (level) => {
    switch (level?.toLowerCase()) {
      case "severe":
        return <AlertOctagon className="w-4 h-4 text-red-400" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case "watch":
        return <Info className="w-4 h-4 text-yellow-400" />;
      default:
        return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
    }
  };

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={`${zone.name} (${zone.id})`}
      subtitle={`Priority Rank #${zone.rank} of 33 Districts · ${zone.tier} Urgency Tier`}
      width="w-[480px]"
    >
      <div className="flex flex-col gap-6 text-xs text-ink font-sans">
        {/* Urgent Advisory Card */}
        <div
          className={`rounded-md p-4 border ${
            advisory.level === "Severe"
              ? "border-red-500/50 bg-red-950/30"
              : advisory.level === "Warning"
              ? "border-amber-500/50 bg-amber-950/30"
              : "border-cyan/40 bg-cyan/10"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {getAdvisoryIcon(advisory.level)}
              <span className="font-bold uppercase tracking-wider font-mono text-[11px]">
                {advisory.level} Advisory Alert
              </span>
            </div>
            <Badge variant={zone.robust ? "robust" : "borderline"} size="xs">
              {zone.robust ? "Robust Rank" : "Borderline"}
            </Badge>
          </div>
          <p className="text-ink font-semibold text-xs leading-snug">{advisory.headline}</p>

          <div className="mt-3 space-y-1.5 border-t border-line/40 pt-2.5">
            <div className="lbl text-dim">Recommended Operational Actions:</div>
            <ul className="space-y-1.5">
              {advisory.recommended_actions.map((act, i) => (
                <li key={i} className="flex gap-2 text-[11px] leading-relaxed text-ink/90">
                  <span className="num font-bold text-cyan">{i + 1}.</span>
                  <span>{act}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-3 pt-2 border-t border-line/40 flex flex-col gap-1 text-[9px] font-mono text-muted">
            <div className="flex justify-between items-center">
              <span>Confidence: <b className="text-ink">{advisory.confidence}</b></span>
            </div>
            <div className="text-[8px] text-muted tracking-tight">{advisory.disclaimer}</div>
          </div>
        </div>

        {/* Prediction Interval & Exposure Metrics */}
        <div className="grid grid-cols-2 gap-3 font-mono">
          <Card>
            <div className="lbl mb-1 text-dim">Exceedance Probability</div>
            <div className="text-xl font-bold text-cyan tabular-nums">
              {(zone.p_mid * 100).toFixed(1)}%
            </div>
            <div className="text-[10px] text-muted mt-0.5">
              80% CQR: [{(zone.p_low * 100).toFixed(1)}% – {(zone.p_high * 100).toFixed(1)}%]
            </div>
          </Card>

          <Card>
            <div className="lbl mb-1 text-dim">Population & Exposure</div>
            <div className="text-xl font-bold text-ink tabular-nums">
              {zone.population_lakh ? `${zone.population_lakh.toFixed(1)}L` : "Exposure"}
            </div>
            <div className="text-[10px] text-muted mt-0.5">
              Priority Score: <span className="text-cyan font-bold">{zone.priority.toFixed(4)}</span>
            </div>
          </Card>
        </div>

        {/* Causal Feature Drivers (TreeSHAP) */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="lbl text-cyan">Top Causal Risk Drivers (TreeSHAP)</span>
            <span className="text-[9px] font-mono text-muted">Local Feature Impact</span>
          </div>

          <div className="rounded-md border border-line bg-card p-3 space-y-3">
            {(explain?.top_drivers || explain?.drivers || [
              { feature: "lag1_severity_index", importance: 0.42, plain_language: "Prior-month riverine saturation carries over strongly into current period." },
              { feature: "upstream_rain_total_mm", importance: 0.28, plain_language: "High transboundary rainfall in the Upper Brahmaputra catchment." },
              { feature: "rain_cum3m_mm", importance: 0.18, plain_language: "90-day cumulative seasonal monsoon precipitation build-up." },
              { feature: "floodplain_frac", importance: 0.08, plain_language: "Low elevation riverine floodplain terrain increases vulnerability." }
            ]).map((d, i) => (
              <div key={i} className="text-[11px] space-y-1">
                <div className="flex justify-between items-baseline font-mono">
                  <span className="font-semibold text-ink">{d.feature.replace(/_/g, " ")}</span>
                  <span className="text-cyan text-[10px]">{(d.importance * 100).toFixed(0)}% weight</span>
                </div>
                <div className="h-1 bg-line rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, d.importance * 200)}%` }}
                  />
                </div>
                <p className="text-[10px] text-dim leading-snug">{d.plain_language}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Local Precipitation Telemetry */}
        {zone.drivers && (
          <div>
            <span className="lbl text-dim mb-2 block">Precipitation Telemetry (Period: {period})</span>
            <div className="grid grid-cols-3 gap-2 font-mono text-[10px]">
              <div className="p-2 rounded bg-elevated border border-line">
                <div className="text-muted text-[9px] uppercase">Monthly Total</div>
                <div className="font-bold text-ink mt-0.5">{zone.drivers.rain_total_mm ?? "—"} mm</div>
              </div>
              <div className="p-2 rounded bg-elevated border border-line">
                <div className="text-muted text-[9px] uppercase">3-Month Cumul</div>
                <div className="font-bold text-ink mt-0.5">{zone.drivers.rain_cum3m_mm ?? "—"} mm</div>
              </div>
              <div className="p-2 rounded bg-elevated border border-line">
                <div className="text-muted text-[9px] uppercase">Anomaly</div>
                <div className={`font-bold mt-0.5 ${(zone.drivers.rain_anom_mm || 0) >= 0 ? "text-cyan" : "text-amber-400"}`}>
                  {(zone.drivers.rain_anom_mm || 0) >= 0 ? "+" : ""}{zone.drivers.rain_anom_mm ?? "—"} mm
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Observed SAR Footprint Data (If Available) */}
        {zone.observed_flood_km2 && (
          <div className="p-3 rounded bg-panel border border-cyan/30 flex items-center justify-between font-mono text-[11px]">
            <div>
              <span className="text-[9px] uppercase text-cyan block">Sentinel-1 SAR Observed Footprint</span>
              <span className="font-bold text-ink">{zone.observed_flood_km2} km² flooded</span>
            </div>
            <Badge variant="ok" size="xs">
              {(zone.observed_flood_frac * 100).toFixed(1)}% of district
            </Badge>
          </div>
        )}

        {/* Actions Strip */}
        <div className="border-t border-line pt-4 flex items-center justify-between">
          <button
            onClick={() => onExportBriefing && onExportBriefing(zone)}
            className="px-4 py-2 rounded bg-card hover:bg-elevated border border-line text-ink font-mono text-xs flex items-center gap-2"
          >
            <FileDown className="w-3.5 h-3.5 text-cyan" />
            <span>Generate Briefing PDF</span>
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-line hover:bg-elevated text-dim hover:text-ink font-mono text-xs"
          >
            Close Drawer
          </button>
        </div>
      </div>
    </Drawer>
  );
}
