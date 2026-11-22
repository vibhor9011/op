import React, { useEffect, useRef } from "react";
import { Shield, Radio, ArrowRight, Zap, ExternalLink } from "lucide-react";

export default function HeroLanding({ onLaunch }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animId;
    let angle = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const r = Math.min(cx, cy) * 0.72;

      // Glow behind globe
      const grad = ctx.createRadialGradient(cx, cy, r * 0.4, cx, cy, r * 1.3);
      grad.addColorStop(0, "rgba(0, 240, 255, 0.15)");
      grad.addColorStop(0.7, "rgba(13, 21, 39, 0.6)");
      grad.addColorStop(1, "rgba(7, 12, 24, 0)");
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, r * 1.3, 0, Math.PI * 2);
      ctx.fill();

      // Earth body
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = "#0c172e";
      ctx.fill();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = "rgba(0, 240, 255, 0.4)";
      ctx.stroke();

      // Latitude lines
      for (let lat = -60; lat <= 60; lat += 30) {
        const y = cy + (lat / 90) * (r * 0.9);
        const w = Math.sqrt(Math.max(0, r * r - (y - cy) * (y - cy)));
        ctx.beginPath();
        ctx.ellipse(cx, y, w, w * 0.25, 0, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(0, 240, 255, 0.12)";
        ctx.stroke();
      }

      // Longitude lines rotating
      for (let lon = 0; lon < 180; lon += 45) {
        const curAngle = angle + (lon * Math.PI) / 180;
        ctx.beginPath();
        ctx.ellipse(cx, cy, Math.abs(Math.cos(curAngle)) * r, r, 0, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(0, 240, 255, 0.15)";
        ctx.stroke();
      }

      // Orbit Ring 1 (Sentinel-1 SAR)
      ctx.beginPath();
      ctx.ellipse(cx, cy, r * 1.35, r * 0.45, -0.35, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(0, 229, 255, 0.35)";
      ctx.setLineDash([4, 6]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Orbiting Satellite 1
      const sat1X = cx + Math.cos(angle * 1.5) * (r * 1.35);
      const sat1Y = cy + Math.sin(angle * 1.5) * (r * 0.45);
      ctx.beginPath();
      ctx.arc(sat1X, sat1Y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#00f0ff";
      ctx.shadowColor = "#00f0ff";
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Orbit Ring 2 (Polar Meteorological)
      ctx.beginPath();
      ctx.ellipse(cx, cy, r * 1.25, r * 0.65, 0.55, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(245, 158, 11, 0.3)";
      ctx.setLineDash([3, 7]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Orbiting Satellite 2
      const sat2X = cx + Math.cos(-angle * 1.2) * (r * 1.25);
      const sat2Y = cy + Math.sin(-angle * 1.2) * (r * 0.65);
      ctx.beginPath();
      ctx.arc(sat2X, sat2Y, 3, 0, Math.PI * 2);
      ctx.fillStyle = "#f59e0b";
      ctx.shadowColor = "#f59e0b";
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;

      angle += 0.008;
      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-between bg-canvas text-ink overflow-hidden p-8 sm:p-14 select-none">
      {/* Background Starfield Grid */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: "radial-gradient(#38bdf8 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Top Header */}
      <header className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="brand-mark">O</div>
          <div>
            <h1 className="font-bold tracking-[0.2em] text-sm text-ink font-mono">ORBITGUARD</h1>
            <p className="text-[9px] tracking-widest text-cyan font-mono uppercase">Multi-Hazard Earth Intelligence</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="hidden sm:inline-block px-2.5 py-1 rounded border border-line bg-panel/60 text-dim">
            ASRA HACKATHON 2026 // S75
          </span>
          <button
            onClick={onLaunch}
            className="text-dim hover:text-cyan transition-colors underline-offset-4 hover:underline text-[11px]"
          >
            Skip to Console →
          </button>
        </div>
      </header>

      {/* Hero Body */}
      <main className="relative z-10 my-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center max-w-7xl mx-auto w-full">
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan/30 bg-cyan/10 text-cyan text-xs font-mono w-fit">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Assam Basin Operational Disaster Prototype</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-black tracking-tight leading-[1.1] text-ink">
            Protecting Earth. <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan to-blue-400">
              Securing Orbit.
            </span> <br />
            Ensuring Continuity.
          </h2>

          <p className="text-sm sm:text-base text-dim max-w-xl leading-relaxed">
            Multi-hazard predictive early warning and emergency response prioritisation across all 33 administrative
            districts of Assam. Calibrated conformal uncertainty bounds, Sentinel-1 SAR inundation mapping, and
            deterministic resource allocation for the Assam State Disaster Management Authority (ASDMA).
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={onLaunch}
              className="px-6 py-3 rounded-md bg-cyan text-black font-bold tracking-wider text-xs uppercase hover:bg-cyan/90 transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(0,240,255,0.4)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
            >
              <span>Launch Command Console</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <span className="text-xs text-muted font-mono flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              Precomputed 2014–2025 LOYO Backtest Engine
            </span>
          </div>

          {/* Quick Metrics Strip */}
          <div className="grid grid-cols-3 gap-3 pt-6 border-t border-line/60 max-w-lg font-mono">
            <div>
              <div className="text-lg font-bold text-cyan tabular-nums">0.9360</div>
              <div className="text-[10px] text-dim uppercase tracking-wider">Forecast ROC-AUC</div>
            </div>
            <div>
              <div className="text-lg font-bold text-emerald-400 tabular-nums">80.0%</div>
              <div className="text-[10px] text-dim uppercase tracking-wider">CQR Band Coverage</div>
            </div>
            <div>
              <div className="text-lg font-bold text-ink tabular-nums">33</div>
              <div className="text-[10px] text-dim uppercase tracking-wider">Assam Districts</div>
            </div>
          </div>
        </div>

        {/* Right Canvas Globe */}
        <div className="lg:col-span-5 flex justify-center items-center relative">
          <canvas
            ref={canvasRef}
            width={480}
            height={480}
            className="w-full max-w-[420px] aspect-square object-contain"
            aria-label="Interactive 3D orbital visualization of Earth with Sentinel satellite tracks"
          />
        </div>
      </main>

      {/* Bottom Bar */}
      <footer className="relative z-10 flex flex-wrap items-center justify-between gap-4 text-[10px] font-mono text-dim border-t border-line/40 pt-4">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-ping" />
          <span>OPERATIONAL DECISION SUPPORT SYSTEM // PROTOTYPE v1.0</span>
        </div>
        <div>
          <span>Decision support only; confirm with official ASDMA / IMD bulletins.</span>
        </div>
      </footer>
    </div>
  );
}
