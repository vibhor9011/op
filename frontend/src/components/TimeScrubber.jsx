import React from "react";
import { Play, Pause, SkipBack, SkipForward, Calendar, CloudRain } from "lucide-react";

export default function TimeScrubber({
  periods = [],
  currentPeriod,
  onPeriodChange,
  isPlaying,
  onTogglePlay,
  selectedZone,
  leadWording = "1-Month Risk Outlook"
}) {
  const currentIndex = Math.max(0, periods.indexOf(currentPeriod));

  const handlePrev = () => {
    if (currentIndex > 0) onPeriodChange(periods[currentIndex - 1]);
  };

  const handleNext = () => {
    if (currentIndex < periods.length - 1) onPeriodChange(periods[currentIndex + 1]);
  };

  const handleSlider = (e) => {
    const idx = Number(e.target.value);
    if (periods[idx]) onPeriodChange(periods[idx]);
  };

  const drivers = selectedZone?.drivers;

  return (
    <div className="h-[64px] border-t border-line bg-panel px-4 flex items-center justify-between gap-6 select-none font-mono">
      {/* Play Controls & Current Period Badge */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="flex items-center gap-1">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className="p-1.5 rounded hover:bg-elevated disabled:opacity-30 text-dim hover:text-ink transition-colors"
            title="Previous Period (←)"
          >
            <SkipBack className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onTogglePlay}
            className="p-2 rounded bg-cyan/15 hover:bg-cyan/25 border border-cyan/40 text-cyan transition-colors"
            title={isPlaying ? "Pause Timeline (Space)" : "Auto-Play Monsoon Timeline (Space)"}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <button
            onClick={handleNext}
            disabled={currentIndex >= periods.length - 1}
            className="p-1.5 rounded hover:bg-elevated disabled:opacity-30 text-dim hover:text-ink transition-colors"
            title="Next Period (→)"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Period Pill */}
        <div className="flex flex-col">
          <div className="text-[12px] font-bold text-cyan tracking-wider flex items-center gap-1.5">
            <Calendar className="w-3 h-3 text-cyan" />
            <span>{currentPeriod}</span>
          </div>
          <span className="text-[9px] text-muted tracking-wide">{leadWording}</span>
        </div>
      </div>

      {/* Main Timeline Slider */}
      <div className="flex-1 max-w-2xl flex flex-col justify-center gap-1">
        <div className="flex justify-between text-[9px] text-muted">
          <span>{periods[0] || "2014-05"}</span>
          <span className="text-dim font-bold">
            Period {currentIndex + 1} of {periods.length} (Monsoon Seasons 2014–2025)
          </span>
          <span>{periods[periods.length - 1] || "2025-10"}</span>
        </div>
        <input
          type="range"
          min={0}
          max={Math.max(0, periods.length - 1)}
          value={currentIndex}
          onChange={handleSlider}
          className="w-full h-1.5 bg-line rounded cursor-pointer accent-cyan focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan"
          aria-label="Monsoon Timeline Scrubber"
        />
      </div>

      {/* District Rainfall Telemetry Strip */}
      <div className="hidden lg:flex items-center gap-4 text-[10px] shrink-0 border-l border-line/60 pl-5">
        <div className="flex items-center gap-2">
          <CloudRain className="w-4 h-4 text-cyan" />
          <div>
            <div className="text-[9px] text-muted uppercase">Selected: {selectedZone?.name || "Statewide"}</div>
            <div className="font-bold text-ink">
              {drivers?.rain_total_mm != null ? `${drivers.rain_total_mm.toFixed(0)} mm` : "—"}{" "}
              <span className="text-dim font-normal">
                (90d: {drivers?.rain_cum3m_mm != null ? `${drivers.rain_cum3m_mm.toFixed(0)} mm` : "—"})
              </span>
            </div>
          </div>
        </div>

        {drivers?.rain_anom_mm != null && (
          <div className="flex flex-col text-right">
            <span className="text-[9px] text-muted uppercase">Anomaly</span>
            <span className={`font-bold ${drivers.rain_anom_mm >= 0 ? "text-cyan" : "text-amber-400"}`}>
              {drivers.rain_anom_mm >= 0 ? "+" : ""}
              {drivers.rain_anom_mm.toFixed(0)} mm
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
