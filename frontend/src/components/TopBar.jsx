import React from "react";
import { Badge } from "../design/index.js";
import { ShieldCheck, Play, Search, HelpCircle, Layers, Radio, Globe } from "lucide-react";

export default function TopBar({
  hazard = "flood",
  onSelectHazard,
  lead = "1_month",
  onSelectLead,
  periods = [],
  currentPeriod = "2022-06",
  onSelectPeriod,
  dataMode = "live",
  onOpenTrust,
  onOpenDemo,
  onOpenCommandPalette,
  onOpenHero,
  alertCount = 0
}) {
  const hazardsList = [
    { id: "flood", name: "FLOOD", badge: "PROTOTYPE", active: true },
    { id: "drought", name: "DROUGHT", badge: "INDEX-DEMO", active: true },
    { id: "landslide", name: "LANDSLIDE", badge: "PLANNED", active: false },
    { id: "cyclone", name: "CYCLONE", badge: "PLANNED", active: false },
    { id: "wildfire", name: "WILDFIRE", badge: "PLANNED", active: false }
  ];

  return (
    <header className="h-[58px] shrink-0 border-b border-line bg-panel flex items-center px-4 gap-4 select-none font-mono text-xs">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3 shrink-0 cursor-pointer" onClick={onOpenHero} title="Return to Mission Intro">
        <span className="brand-mark" aria-hidden="true">
          O
        </span>
        <div className="flex flex-col">
          <span className="font-bold tracking-[0.16em] text-[13px] text-ink leading-tight">ORBITGUARD</span>
          <span className="text-[8px] text-cyan tracking-widest uppercase">Earth Intelligence</span>
        </div>
      </div>

      {/* Hazard Domain Tabs with Honest Status Badges */}
      <nav className="flex items-stretch h-full gap-1 ml-2 overflow-x-auto shrink-0 select-none">
        {hazardsList.map((h) => {
          const isSelected = hazard === h.id;
          return (
            <button
              key={h.id}
              onClick={() => onSelectHazard(h.id)}
              className={`px-3 flex items-center gap-1.5 border-b-2 text-[10px] tracking-wider uppercase transition-colors ${
                isSelected
                  ? "border-cyan text-cyan bg-card/60 font-bold"
                  : "border-transparent text-dim hover:text-ink hover:bg-elevated/40"
              }`}
            >
              <span>{h.name}</span>
              <span
                className={`text-[8px] px-1 py-0.2 rounded font-mono ${
                  h.badge === "PROTOTYPE"
                    ? "bg-cyan/15 text-cyan border border-cyan/30"
                    : h.badge === "INDEX-DEMO"
                    ? "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                    : "bg-slate-800 text-slate-500 border border-slate-700"
                }`}
              >
                {h.badge}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Center Controls: Lead Horizon & Period Dropdown */}
      <div className="ml-auto flex items-center gap-3">
        {/* Lead Selector */}
        <div className="flex items-center gap-1 border border-line rounded bg-canvas p-0.5">
          <button
            onClick={() => onSelectLead("1_month")}
            className={`px-2.5 py-1 rounded text-[10px] tracking-wider transition-colors ${
              lead === "1_month" ? "bg-cyan/20 text-cyan border border-cyan/40 font-bold" : "text-dim hover:text-ink"
            }`}
            title="1-Month Risk Outlook (Verified under Leave-One-Year-Out LOYO Cross-Validation)"
          >
            1-MONTH OUTLOOK
          </button>
          <button
            onClick={() => onSelectLead("0_month")}
            className={`px-2.5 py-1 rounded text-[10px] tracking-wider transition-colors ${
              lead === "0_month" ? "bg-cyan/20 text-cyan border border-cyan/40 font-bold" : "text-dim hover:text-ink"
            }`}
            title="Same-Month Risk Assessment (Current Inundation State Nowcast)"
          >
            SAME-MONTH RISK
          </button>
        </div>

        {/* Quick Period Select */}
        <select
          value={currentPeriod}
          onChange={(e) => onSelectPeriod(e.target.value)}
          className="bg-card border border-line rounded px-2.5 py-1 text-[11px] text-ink focus:outline-none focus:border-cyan cursor-pointer"
          aria-label="Select Period"
        >
          {periods.map((p) => (
            <option key={p} value={p}>
              Period: {p}
            </option>
          ))}
        </select>

        {/* Guided Backtest Demo Trigger */}
        <button
          onClick={onOpenDemo}
          className="px-3 py-1.5 rounded border border-cyan/40 bg-cyan/10 hover:bg-cyan/20 text-cyan text-[10px] uppercase tracking-wider font-bold transition-all flex items-center gap-1.5 shadow-[0_0_10px_rgba(0,240,255,0.2)]"
        >
          <Play className="w-3 h-3" />
          <span>Demo Walkthrough</span>
        </button>

        {/* Model Trust Audit Trigger */}
        <button
          onClick={onOpenTrust}
          className="px-3 py-1.5 rounded border border-line hover:border-cyan/40 bg-card hover:bg-elevated text-dim hover:text-ink text-[10px] uppercase tracking-wider transition-colors flex items-center gap-1.5"
          title="Pitch Deck Claims Audit & Empirical Model Trust Verification"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden xl:inline">Model Trust</span>
        </button>

        {/* Quick Search Hotkey Button */}
        <button
          onClick={onOpenCommandPalette}
          className="px-2 py-1.5 rounded border border-line bg-card hover:bg-elevated text-dim hover:text-ink flex items-center gap-1.5 text-[10px]"
          title="Open Command Palette (Ctrl+K)"
        >
          <Search className="w-3.5 h-3.5" />
          <kbd className="hidden sm:inline px-1 py-0.2 rounded bg-elevated text-[9px] text-muted">⌘K</kbd>
        </button>

        {/* Data Mode & Status Pill */}
        <div className="flex items-center gap-2 pl-2 border-l border-line text-[10px]">
          <span className="px-2 py-0.5 rounded border border-line bg-card text-dim font-bold">
            {dataMode === "mock" ? "MOCK DATA" : "LIVE BACKEND"}
          </span>
          <span className="text-dim hidden 2xl:inline">
            Active Alerts: <b className="text-red-400 font-bold tabular-nums">{alertCount}</b>
          </span>
        </div>
      </div>
    </header>
  );
}
