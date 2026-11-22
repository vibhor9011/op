import React, { Suspense, lazy, useCallback, useEffect, useMemo, useRef, useState } from "react";
import TopBar from "./components/TopBar.jsx";
import PrioritySidebar from "./components/PrioritySidebar.jsx";
import AssamMap from "./components/AssamMap.jsx";
import TimeScrubber from "./components/TimeScrubber.jsx";

// Performance code-split heavy modal and canvas components
const ZoneDrawer = lazy(() => import("./components/ZoneDrawer.jsx"));
const ModelTrustModal = lazy(() => import("./components/ModelTrustModal.jsx"));
const BacktestDemoModal = lazy(() => import("./components/BacktestDemoModal.jsx"));
const BriefingModal = lazy(() => import("./components/BriefingModal.jsx"));
const CommandPalette = lazy(() => import("./components/CommandPalette.jsx"));
const HeroLanding = lazy(() => import("./components/HeroLanding.jsx"));

import {
  fetchDashboard,
  fetchExtent,
  fetchGeometry,
  fetchHealth,
  fetchPeriods,
  fetchRanking
} from "./services/aiClient.js";
import { localDashboard, localExtent } from "./data/orbitguardEngine.js";
import { AlertCircle, AlertTriangle, Info, Layers, Shield, Sliders } from "lucide-react";

const MONSOON_PERIODS = [
  "2014-05", "2014-06", "2014-07", "2014-08", "2014-09", "2014-10",
  "2015-05", "2015-06", "2015-07", "2015-08", "2015-09", "2015-10",
  "2016-05", "2016-06", "2016-07", "2016-08", "2016-09", "2016-10",
  "2017-05", "2017-06", "2017-07", "2017-08", "2017-09", "2017-10",
  "2018-05", "2018-06", "2018-07", "2018-08", "2018-09", "2018-10",
  "2019-05", "2019-06", "2019-07", "2019-08", "2019-09", "2019-10",
  "2020-05", "2020-06", "2020-07", "2020-08", "2020-09", "2020-10",
  "2021-05", "2021-06", "2021-07", "2021-08", "2021-09", "2021-10",
  "2022-05", "2022-06", "2022-07", "2022-08", "2022-09", "2022-10",
  "2023-05", "2023-06", "2023-07", "2023-08", "2023-09", "2023-10",
  "2024-05", "2024-06", "2024-07", "2024-08", "2024-09", "2024-10",
  "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10"
];

export default function App() {
  // Operational parameters
  const [hazard, setHazard] = useState("flood");
  const [lead, setLead] = useState("1_month");
  const [periods, setPeriods] = useState(MONSOON_PERIODS);
  const [currentPeriod, setCurrentPeriod] = useState("2022-06");
  const [selectedId, setSelectedId] = useState("G09"); // Dhemaji as default focus
  const [agency, setAgency] = useState("ALL");
  const [sarOpacity, setSarOpacity] = useState(0.75);

  // Layer toggles
  const [layers, setLayers] = useState({
    risk: true,
    uncertainty: false,
    extent: true
  });

  // Timeline auto-play
  const [isPlaying, setIsPlaying] = useState(false);

  // Data state
  const [dash, setDash] = useState(null);
  const [extent, setExtent] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorNotice, setErrorNotice] = useState(null);

  // Modals & Drawers
  const [showHero, setShowHero] = useState(false);
  const [showTrust, setShowTrust] = useState(false);
  const [showDemo, setShowDemo] = useState(false);
  const [showBriefing, setShowBriefing] = useState(false);
  const [briefingZone, setBriefingZone] = useState(null);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const reqId = useRef(0);

  // Initial Health & Periods Discovery
  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => null);
    fetchPeriods("flood")
      .then((res) => {
        if (res?.periods?.length > 0) setPeriods(res.periods);
      })
      .catch(() => null);
  }, []);

  // Main Data Fetch for Hazard, Period, and Lead
  useEffect(() => {
    const id = ++reqId.current;
    setLoading(true);

    if (["landslide", "cyclone", "wildfire"].includes(hazard)) {
      // Planned hazards show honest placeholder state (no synthetic predictions fabricated)
      setDash({
        engine: "planned-placeholder",
        hazard,
        period: currentPeriod,
        lead_wording: "Planned Module",
        label_source: "none",
        warning: `The ${hazard.toUpperCase()} hazard module is PLANNED for future development. No synthetic data or unverified predictions are generated in compliance with hackathon rules.`,
        districts: [],
        geojson: null,
        summary: { alerts: 0, high: 0, moderate: 0, low: 0 }
      });
      setExtent(null);
      setLoading(false);
      return;
    }

    // Active hazards: flood or drought
    const loadData = async () => {
      try {
        let dashboardData = null;
        let extentData = null;

        if (hazard === "flood") {
          dashboardData = await fetchDashboard(currentPeriod, lead);
          if (layers.extent) {
            extentData = await fetchExtent(currentPeriod).catch(() => null);
          }
        } else if (hazard === "drought") {
          const [rankingRes, geomRes] = await Promise.all([
            fetchRanking("drought", currentPeriod, lead),
            fetchGeometry("drought")
          ]);
          dashboardData = {
            engine: "fastapi-spi-vci",
            hazard: "drought",
            period: currentPeriod,
            lead_wording: rankingRes.lead_wording,
            label_source: rankingRes.label_source,
            warning: rankingRes.warning,
            districts: rankingRes.ranking,
            geojson: geomRes,
            summary: {
              alerts: rankingRes.ranking.filter((r) => r.priority >= 0.02).length,
              high: rankingRes.ranking.filter((r) => r.priority >= 0.05).length,
              moderate: rankingRes.ranking.filter((r) => r.priority >= 0.02 && r.priority < 0.05).length,
              low: rankingRes.ranking.filter((r) => r.priority < 0.02).length
            }
          };
        }

        if (id === reqId.current && dashboardData) {
          setDash(dashboardData);
          setExtent(extentData);
          setErrorNotice(null);
        }
      } catch (err) {
        if (id === reqId.current) {
          console.warn("[OrbitGuard Data Load] Falling back to offline local engine:", err);
          // Fallback to local engine representation
          const fallback = localDashboard(1, 0);
          fallback.engine = "local-offline-engine";
          fallback.period = currentPeriod;
          fallback.warning = `Operating in Offline Mode (${err.message}). Live model results precomputed in outputs/ directory.`;
          setDash(fallback);
          setExtent(localExtent(1, 0));
          setErrorNotice(fallback.warning);
        }
      } finally {
        if (id === reqId.current) setLoading(false);
      }
    };

    loadData();
  }, [hazard, currentPeriod, lead, layers.extent]);

  // Auto-play timeline loop
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setCurrentPeriod((prev) => {
        const idx = periods.indexOf(prev);
        if (idx === -1 || idx >= periods.length - 1) return periods[0];
        return periods[idx + 1];
      });
    }, 2800);
    return () => clearInterval(interval);
  }, [isPlaying, periods]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;

      // Ctrl+K or Cmd+K: Command Palette
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setShowCommandPalette((prev) => !prev);
      }

      // Space: Play / Pause timeline
      if (e.key === " " && !showHero && !showTrust && !showDemo && !showBriefing) {
        e.preventDefault();
        setIsPlaying((p) => !p);
      }

      // ArrowLeft / ArrowRight: Step timeline
      if (e.key === "ArrowLeft") {
        setCurrentPeriod((prev) => {
          const idx = periods.indexOf(prev);
          return idx > 0 ? periods[idx - 1] : prev;
        });
      }
      if (e.key === "ArrowRight") {
        setCurrentPeriod((prev) => {
          const idx = periods.indexOf(prev);
          return idx < periods.length - 1 ? periods[idx + 1] : prev;
        });
      }

      // Escape: Close overlays
      if (e.key === "Escape") {
        setIsDrawerOpen(false);
        setShowTrust(false);
        setShowDemo(false);
        setShowBriefing(false);
        setShowCommandPalette(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [periods, showHero, showTrust, showDemo, showBriefing]);

  // Current selected district object
  const selectedDistrict = useMemo(() => {
    if (!dash || !dash.districts || dash.districts.length === 0) return null;
    return dash.districts.find((d) => d.id === selectedId) || dash.districts[0];
  }, [dash, selectedId]);

  // Handle District Selection from Map or Sidebar
  const handleSelectDistrict = useCallback((id) => {
    setSelectedId(id);
    setIsDrawerOpen(true);
  }, []);

  // Handle Briefing Modal Open
  const handleOpenBriefing = useCallback((district) => {
    setBriefingZone(district);
    setShowBriefing(true);
  }, []);

  const handleToggleLayer = useCallback((layerKey) => {
    setLayers((prev) => ({ ...prev, [layerKey]: !prev[layerKey] }));
  }, []);

  const alertCount = dash?.summary?.alerts || 0;
  const leadWording = dash?.lead_wording || (lead === "1_month" ? "1-Month Risk Outlook" : "Same-Month Risk Assessment");

  if (showHero) {
    return (
      <Suspense fallback={<div className="h-screen w-screen bg-[#070c18] flex items-center justify-center text-cyan font-mono text-sm">INITIALIZING ORBITAL SENSORS...</div>}>
        <HeroLanding onLaunch={() => setShowHero(false)} />
      </Suspense>
    );
  }

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-canvas text-ink font-sans select-none antialiased">
      {/* 1. TOP MISSION COMMAND BAR */}
      <TopBar
        hazard={hazard}
        onSelectHazard={setHazard}
        lead={lead}
        onSelectLead={setLead}
        periods={periods}
        currentPeriod={currentPeriod}
        onSelectPeriod={setCurrentPeriod}
        dataMode={dash?.engine?.includes("offline") ? "mock" : "live"}
        onOpenTrust={() => setShowTrust(true)}
        onOpenDemo={() => setShowDemo(true)}
        onOpenCommandPalette={() => setShowCommandPalette(true)}
        onOpenHero={() => setShowHero(true)}
        alertCount={alertCount}
      />

      {/* Offline or Notice Banner if applicable */}
      {errorNotice && (
        <div className="bg-amber-950/80 border-b border-amber-600/50 px-4 py-1.5 flex items-center justify-between text-xs text-amber-200">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{errorNotice}</span>
          </div>
          <span className="font-mono text-[10px] text-amber-400 font-bold uppercase tracking-wider">
            OFFLINE FALLBACK
          </span>
        </div>
      )}

      {/* 2. MAIN WORKSPACE (Priority Sidebar + Map Center + Inset Panels) */}
      <div className="flex-1 flex min-h-0 relative">
        {/* Left: 33-District Priority Queue Sidebar */}
        <PrioritySidebar
          dash={dash}
          selectedId={selectedId}
          onSelect={handleSelectDistrict}
          agency={agency}
          onAgency={setAgency}
          onOpenBriefing={handleOpenBriefing}
        />

        {/* Center: Mission Map & Spatial Overlays */}
        <main className="flex-1 min-w-0 flex flex-col min-h-0 relative">
          <div className="flex-1 relative min-h-0 bg-[#070c18]">
            {/* Planned Hazard Informational Screen */}
            {["landslide", "cyclone", "wildfire"].includes(hazard) ? (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-8 text-center bg-canvas/95 backdrop-blur-sm">
                <div className="w-16 h-16 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center mb-4 text-slate-400">
                  <Shield className="w-8 h-8" />
                </div>
                <h2 className="text-xl font-bold tracking-widest text-ink uppercase mb-2">
                  {hazard.toUpperCase()} HAZARD MODULE · PLANNED
                </h2>
                <p className="max-w-md text-xs text-dim leading-relaxed mb-6 font-mono">
                  This hazard module is scheduled for operational deployment in Phase 2 for Assam State Disaster Management Authority (ASDMA).
                  In accordance with strict hackathon integrity guidelines, no unverified predictions or synthetic data are displayed.
                </p>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setHazard("flood")}
                    className="px-4 py-2 rounded bg-cyan/20 border border-cyan/50 text-cyan text-xs font-mono font-bold hover:bg-cyan/30 transition-colors uppercase tracking-wider"
                  >
                    Return to Operational Flood Monitor
                  </button>
                  <button
                    onClick={() => setHazard("drought")}
                    className="px-4 py-2 rounded bg-amber-500/20 border border-amber-500/50 text-amber-300 text-xs font-mono font-bold hover:bg-amber-500/30 transition-colors uppercase tracking-wider"
                  >
                    View Drought SPI/VCI Index Demo
                  </button>
                </div>
              </div>
            ) : (
              <AssamMap
                dash={dash}
                extent={extent}
                selectedId={selectedId}
                onSelect={handleSelectDistrict}
                layers={layers}
                sarOpacity={sarOpacity}
                onSarOpacityChange={setSarOpacity}
              />
            )}

            {/* Inset HUD: Layer Toggles & SAR Opacity Slider (Bottom Right) */}
            {!["landslide", "cyclone", "wildfire"].includes(hazard) && (
              <div className="absolute bottom-4 right-4 z-20 bg-panel/95 backdrop-blur border border-line p-3 w-[230px] rounded shadow-2xl font-mono text-xs select-none">
                <div className="flex items-center justify-between border-b border-line pb-1.5 mb-2">
                  <span className="lbl text-ink font-bold flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-cyan" />
                    <span>Map Layers</span>
                  </span>
                  <span className="text-[9px] text-cyan font-bold">33 POLYS</span>
                </div>

                <div className="space-y-1.5">
                  <label className="flex items-center justify-between text-[11px] text-ink cursor-pointer hover:text-cyan transition-colors">
                    <span className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={layers.risk}
                        onChange={() => handleToggleLayer("risk")}
                        className="rounded border-line bg-card text-cyan focus:ring-0"
                      />
                      <span>Risk Exceedance</span>
                    </span>
                    <span className="text-[9px] text-dim">p_mid</span>
                  </label>

                  <label className="flex items-center justify-between text-[11px] text-ink cursor-pointer hover:text-cyan transition-colors">
                    <span className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={layers.uncertainty}
                        onChange={() => handleToggleLayer("uncertainty")}
                        className="rounded border-line bg-card text-cyan focus:ring-0"
                      />
                      <span>CQR Uncertainty</span>
                    </span>
                    <span className="text-[9px] text-amber-400">80% band</span>
                  </label>

                  <label className="flex items-center justify-between text-[11px] text-ink cursor-pointer hover:text-cyan transition-colors">
                    <span className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={layers.extent}
                        onChange={() => handleToggleLayer("extent")}
                        className="rounded border-line bg-card text-cyan focus:ring-0"
                      />
                      <span>Sentinel-1 SAR</span>
                    </span>
                    <span className="text-[9px] text-cyan">30m VV</span>
                  </label>
                </div>

                {/* SAR Opacity Slider */}
                {layers.extent && (
                  <div className="mt-2.5 pt-2 border-t border-line/60">
                    <div className="flex items-center justify-between text-[9px] text-dim mb-1">
                      <span>SAR Footprint Opacity</span>
                      <span className="text-cyan font-bold">{Math.round(sarOpacity * 100)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0.1"
                      max="1.0"
                      step="0.05"
                      value={sarOpacity}
                      onChange={(e) => setSarOpacity(parseFloat(e.target.value))}
                      className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan"
                    />
                  </div>
                )}

                {/* Color Ramp Bar */}
                <div className="mt-3 pt-2 border-t border-line/60">
                  <div className="flex items-center justify-between text-[8px] text-dim mb-1 uppercase tracking-wider">
                    <span>Low Risk</span>
                    <span>Moderate</span>
                    <span>Severe</span>
                  </div>
                  <div className="h-1.5 w-full rounded-sm overflow-hidden bg-gradient-to-r from-emerald-500 via-amber-500 via-orange-500 to-red-500" />
                  <div className="flex items-center justify-between text-[8px] text-dim mt-0.5">
                    <span>&lt;2%</span>
                    <span>2%–5%</span>
                    <span>&gt;5%</span>
                  </div>
                </div>
              </div>
            )}

            {/* Quick Status Pill (Bottom Left) */}
            <div className="absolute bottom-4 left-4 z-20 text-[10px] font-mono tracking-wider text-dim bg-panel/90 backdrop-blur border border-line px-2.5 py-1 rounded flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>ASSAM STATE DISASTER MANAGEMENT AUTHORITY (ASDMA) · 33 DISTRICTS</span>
            </div>
          </div>

          {/* 3. MONSOON TIMELINE SCRUBBER (Bottom) */}
          <TimeScrubber
            periods={periods}
            currentPeriod={currentPeriod}
            onPeriodChange={setCurrentPeriod}
            isPlaying={isPlaying}
            onTogglePlay={() => setIsPlaying((p) => !p)}
            selectedZone={selectedDistrict}
            leadWording={leadWording}
          />
        </main>
      </div>

      {/* 4. MANDATORY OPERATIONAL FOOTER */}
      <footer className="h-7 shrink-0 border-t border-line bg-panel flex items-center justify-between px-4 font-mono text-[9px] text-dim select-none">
        <div className="flex items-center gap-3 truncate">
          <span className="text-cyan font-bold">ORBITGUARD v2.4</span>
          <span>·</span>
          <span className="truncate">
            DECISION SUPPORT ONLY; CONFIRM WITH ASDMA/IMD OFFICIAL ADVISORIES.
          </span>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <span>
            LEAD HORIZON: <b className="text-ink">{leadWording.toUpperCase()}</b>
          </span>
          <span>·</span>
          <span>
            HOLDOUT LOYO CV: F1 <b className="text-ink">0.704</b> · AUC <b className="text-ink">0.793</b> · CONFORMAL 80% COVERAGE <b className="text-ink">80.0%</b>
          </span>
        </div>
      </footer>

      {/* 5. OVERLAYS, MODALS & DRAWERS (Lazy Loaded with Suspense) */}
      <Suspense fallback={null}>
        {/* Zone Detail Drawer */}
        {isDrawerOpen && (
          <ZoneDrawer
            isOpen={isDrawerOpen}
            onClose={() => setIsDrawerOpen(false)}
            zone={selectedDistrict}
            period={currentPeriod}
            onExportBriefing={handleOpenBriefing}
          />
        )}

        {/* Model Trust & Pitch Deck Claims Audit Modal */}
        {showTrust && (
          <ModelTrustModal
            isOpen={showTrust}
            onClose={() => setShowTrust(false)}
          />
        )}

        {/* Guided Backtest Story Demo Modal */}
        {showDemo && (
          <BacktestDemoModal
            isOpen={showDemo}
            onClose={() => setShowDemo(false)}
            onSelectPeriod={(p) => setCurrentPeriod(p)}
            onSelectDistrict={(id) => {
              setSelectedId(id);
              setIsDrawerOpen(true);
            }}
          />
        )}

        {/* Printable Emergency Briefing Modal */}
        {showBriefing && (
          <BriefingModal
            isOpen={showBriefing}
            onClose={() => setShowBriefing(false)}
            zone={briefingZone || selectedDistrict}
            period={currentPeriod}
          />
        )}

        {/* Command Palette (Ctrl+K) */}
        {showCommandPalette && (
          <CommandPalette
            isOpen={showCommandPalette}
            onClose={() => setShowCommandPalette(false)}
            districts={dash?.districts || []}
            onSelectDistrict={handleSelectDistrict}
            onSelectPeriod={(p) => setCurrentPeriod(p)}
            onToggleLayer={handleToggleLayer}
            onOpenTrust={() => setShowTrust(true)}
            onOpenDemo={() => setShowDemo(true)}
          />
        )}
      </Suspense>
    </div>
  );
}
