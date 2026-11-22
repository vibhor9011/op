import React, { useState, useEffect } from "react";
import { Modal, Badge } from "../design/index.js";
import { Play, Pause, ChevronRight, ChevronLeft, RotateCcw, AlertTriangle, ShieldCheck, MapPin } from "lucide-react";

export default function BacktestDemoModal({ isOpen, onClose, onSelectPeriod, onSelectDistrict }) {
  const [step, setStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const steps = [
    {
      title: "Step 1: Antecedent Catchment Saturation (May 2022)",
      period: "2022-05",
      lead: "1-Month Risk Outlook",
      caption:
        "Pre-monsoon rainfall build-up in the Upper Brahmaputra basin. Catchment saturation index begins climbing, but district flood exceedance probabilities remain within the 10%–25% baseline band.",
      highlightDistrict: "G09", // Dhemaji
      stats: { meanRisk: "14.2%", peakDistrict: "Dhemaji (#1)", activeAlerts: "8" }
    },
    {
      title: "Step 2: Rapid Cloudburst & Risk Surge (June 2022)",
      period: "2022-06",
      lead: "1-Month Risk Outlook",
      caption:
        "Catastrophic monsoon rainfall build-up across Upper Assam and Meghalaya hills. OrbitGuard's 1-month forecast flags Dhemaji, Dhubri, and Barpeta as Severe priority. Conformal uncertainty bands widen by +34%, signaling elevated forecast volatility.",
      highlightDistrict: "G10", // Dhubri
      stats: { meanRisk: "38.6%", peakDistrict: "Dhubri (#1)", activeAlerts: "22" }
    },
    {
      title: "Step 3: Peak Inundation & Sentinel-1 SAR Footprint",
      period: "2019-07",
      lead: "Same-Month Risk Assessment",
      caption:
        "Severe flood inundation event. OrbitGuard maps the Sentinel-1 SAR microwave radar footprint across the Brahmaputra corridor (233.05 km² flooded in Dhemaji; 142.6 km² in Dhubri).",
      highlightDistrict: "G09",
      stats: { sarFloodedKm2: "233.05 km²", peakDistrict: "Dhemaji", activeAlerts: "29" }
    },
    {
      title: "Step 4: Response Prioritization & Robust Allocations",
      period: "2022-06",
      lead: "1-Month Risk Outlook",
      caption:
        "Prioritization engine ranks all 33 districts by urgency score (Risk × Population Exposure × Vulnerability). Top-tier districts are verified under Monte Carlo perturbations as 'ROBUST', triggering SDRF boat pre-positioning.",
      highlightDistrict: "G02", // Barpeta
      stats: { robustDistricts: "5 Districts", topPriority: "Barpeta (0.052)", activeAlerts: "22" }
    },
    {
      title: "Step 5: Unified Multi-Hazard Contract (Drought Module)",
      period: "2021-08",
      lead: "Same-Month Risk Assessment",
      caption:
        "Demonstrating multi-hazard extensibility: OrbitGuard evaluates 30-year CHIRPS SPI-3 and MODIS NDVI Vegetation Condition Index (VCI) through the identical polymorphic Hazard interface without changing ranking code.",
      highlightDistrict: "G20", // Karbi Anglong
      stats: { spi3Index: "-1.82 (Severe Deficit)", vciMoisture: "31.4%", activeAlerts: "14" }
    }
  ];

  const current = steps[step];

  useEffect(() => {
    if (!isPlaying) return;
    const timer = setInterval(() => {
      setStep((s) => {
        if (s >= steps.length - 1) {
          setIsPlaying(false);
          return s;
        }
        return s + 1;
      });
    }, 4500);
    return () => clearInterval(timer);
  }, [isPlaying, steps.length]);

  const handleApplyStep = () => {
    if (onSelectPeriod) onSelectPeriod(current.period);
    if (onSelectDistrict) onSelectDistrict(current.highlightDistrict);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Guided Backtest Demo: 2019–2022 Flood Walkthrough" maxWidth="max-w-2xl">
      <div className="flex flex-col gap-5 text-xs text-ink font-sans">
        {/* Progress indicator */}
        <div className="flex items-center gap-2">
          {steps.map((st, i) => (
            <div
              key={i}
              onClick={() => setStep(i)}
              className={`flex-1 h-1.5 rounded-full cursor-pointer transition-all ${
                i === step ? "bg-cyan shadow-[0_0_8px_rgba(0,240,255,0.6)]" : i < step ? "bg-cyan/40" : "bg-line"
              }`}
            />
          ))}
        </div>

        {/* Story Card */}
        <div className="rounded-md border border-line bg-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <div>
              <span className="text-[10px] font-bold tracking-widest text-cyan font-mono uppercase">
                {current.lead}
              </span>
              <h3 className="text-sm font-bold text-ink mt-0.5 font-mono">{current.title}</h3>
            </div>
            <Badge variant="robust" size="xs">
              Period: {current.period}
            </Badge>
          </div>

          <p className="text-dim text-[11px] leading-relaxed">{current.caption}</p>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-3 p-3 rounded bg-panel border border-line/60 font-mono text-[11px]">
            {Object.entries(current.stats).map(([k, v]) => (
              <div key={k}>
                <div className="text-[9px] text-muted uppercase tracking-wider">{k.replace(/([A-Z])/g, " $1")}</div>
                <div className="font-bold text-cyan mt-0.5">{v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between pt-2 border-t border-line">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-2 rounded bg-card hover:bg-elevated border border-line text-cyan font-mono flex items-center gap-1.5"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span>{isPlaying ? "Pause" : "Play Story"}</span>
            </button>
            <button
              onClick={() => setStep(0)}
              className="p-2 rounded hover:bg-elevated text-dim hover:text-ink font-mono text-xs"
              title="Reset to Step 1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              disabled={step === 0}
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              className="p-2 rounded border border-line disabled:opacity-30 hover:bg-elevated text-dim hover:text-ink"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-[11px] font-mono text-dim">
              {step + 1} / {steps.length}
            </span>
            <button
              disabled={step === steps.length - 1}
              onClick={() => setStep((s) => Math.min(steps.length - 1, s + 1))}
              className="p-2 rounded border border-line disabled:opacity-30 hover:bg-elevated text-dim hover:text-ink"
            >
              <ChevronRight className="w-4 h-4" />
            </button>

            <button
              onClick={handleApplyStep}
              className="ml-3 px-4 py-2 rounded bg-cyan text-black font-bold uppercase tracking-wider text-xs hover:bg-cyan/90 transition-all flex items-center gap-1.5"
            >
              <MapPin className="w-3.5 h-3.5" />
              <span>Jump to Map</span>
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
