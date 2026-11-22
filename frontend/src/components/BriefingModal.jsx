import React from "react";
import { Modal, Badge } from "../design/index.js";
import { Printer, Shield, FileText, CheckSquare, AlertTriangle } from "lucide-react";

export default function BriefingModal({ isOpen, onClose, zone, period = "2022-06" }) {
  if (!zone) return null;

  const advisory = zone.advisory || {
    level: zone.tier || "Normal",
    headline: `Operational Early Warning Advisory for ${zone.name}`,
    reasons: ["Antecedent riverine saturation build-up", "Catchment rainfall accumulation"],
    recommended_actions: ["Pre-position boats and SDRF teams", "Activate 24/7 District Emergency Operations Center"],
    confidence: "High",
    disclaimer: "Decision support only; confirm with ASDMA/IMD official advisories."
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Emergency Response Briefing Document" maxWidth="max-w-3xl">
      <div className="flex flex-col gap-5 text-xs text-ink font-sans">
        {/* Print Action Bar */}
        <div className="flex items-center justify-between border-b border-line pb-3">
          <div className="text-[11px] text-dim font-mono">
            District Emergency Officer Briefing Card · Period: <b className="text-cyan">{period}</b>
          </div>
          <button
            onClick={handlePrint}
            className="px-4 py-2 rounded bg-cyan text-black font-bold uppercase tracking-wider text-xs hover:bg-cyan/90 transition-all flex items-center gap-1.5 font-mono shadow-[0_0_12px_rgba(0,240,255,0.3)]"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print / Save as PDF</span>
          </button>
        </div>

        {/* Printable Document Area */}
        <div id="briefing-document" className="rounded border border-line bg-card p-6 space-y-6 text-ink">
          {/* Document Header */}
          <div className="flex justify-between items-start border-b border-line/80 pb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="brand-mark w-5 h-5 text-[10px]">O</span>
                <span className="font-bold tracking-[0.16em] uppercase text-xs font-mono">ORBITGUARD EARLY WARNING</span>
              </div>
              <h1 className="text-xl font-black uppercase text-ink font-mono">{zone.name} District Flood Briefing</h1>
              <p className="text-[10px] text-dim font-mono mt-0.5">
                Assam State Disaster Management Authority (ASDMA) · Decision Support Unit
              </p>
            </div>
            <div className="text-right font-mono">
              <Badge variant={advisory.level} size="md">
                {advisory.level} PRIORITY
              </Badge>
              <div className="text-[10px] text-dim mt-1">Statewide Rank: #{zone.rank} of 33</div>
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-4 gap-3 font-mono text-[11px] p-3 rounded bg-panel border border-line/60">
            <div>
              <div className="text-[9px] text-muted uppercase">Exceedance Probability</div>
              <div className="text-base font-bold text-cyan mt-0.5">{(zone.p_mid * 100).toFixed(1)}%</div>
            </div>
            <div>
              <div className="text-[9px] text-muted uppercase">80% CQR Uncertainty</div>
              <div className="text-base font-bold text-ink mt-0.5">
                {(zone.p_low * 100).toFixed(0)}%–{(zone.p_high * 100).toFixed(0)}%
              </div>
            </div>
            <div>
              <div className="text-[9px] text-muted uppercase">Population Exposure</div>
              <div className="text-base font-bold text-ink mt-0.5">
                {zone.population_lakh ? `${zone.population_lakh.toFixed(1)} Lakh` : "High"}
              </div>
            </div>
            <div>
              <div className="text-[9px] text-muted uppercase">Robustness Flag</div>
              <div className={`text-base font-bold mt-0.5 ${zone.robust ? "text-cyan" : "text-dim"}`}>
                {zone.robust ? "ROBUST" : "BORDERLINE"}
              </div>
            </div>
          </div>

          {/* Operational Advisory Directive */}
          <div className="space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-cyan font-mono flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5" />
              Operational Response Directive
            </h2>
            <div className="p-3.5 rounded bg-panel border border-line space-y-2">
              <div className="font-semibold text-ink text-[11px]">{advisory.headline}</div>
              <div className="text-[10px] text-dim">
                <b>Confidence:</b> {advisory.confidence} · Calibrated via Conformalized Quantile Regression.
              </div>
            </div>
          </div>

          {/* Action Checklist */}
          <div className="space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-dim font-mono flex items-center gap-2">
              <CheckSquare className="w-3.5 h-3.5 text-emerald-400" />
              Mandatory Action Checklist for District Incident Commander
            </h2>
            <ul className="space-y-2 text-[11px]">
              {advisory.recommended_actions.map((act, i) => (
                <li key={i} className="flex items-start gap-2.5 p-2 rounded bg-panel/60 border border-line/40">
                  <input type="checkbox" className="mt-0.5 rounded border-line text-cyan" />
                  <span className="leading-snug text-ink/90">{act}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Mandatory Official Disclaimer */}
          <div className="border-t border-line/80 pt-3 flex items-center justify-between text-[9px] font-mono text-muted">
            <span>Issue Date: {period} | Generated by OrbitGuard v1.0 ML Backend</span>
            <span className="font-bold text-dim">
              DECISION SUPPORT ONLY; CONFIRM WITH ASDMA/IMD OFFICIAL BULLETINS.
            </span>
          </div>
        </div>
      </div>
    </Modal>
  );
}
