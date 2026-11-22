import React from "react";

export function StatTile({ label, value, subtext = null, sparkline = null, accent = "cyan", className = "" }) {
  const accentColor = accent === "red" ? "text-red-400" : accent === "amber" ? "text-amber-400" : accent === "emerald" ? "text-emerald-400" : "text-cyan";

  return (
    <div className={`rounded-md border border-line bg-card p-3 flex flex-col justify-between ${className}`}>
      <span className="text-[9px] font-bold tracking-[0.14em] uppercase text-dim">{label}</span>
      <div className="flex items-baseline justify-between mt-1">
        <span className={`text-xl font-bold font-mono tabular-nums ${accentColor}`}>{value}</span>
        {sparkline && <div className="w-16 h-6">{sparkline}</div>}
      </div>
      {subtext && <span className="text-[10px] text-muted font-mono mt-1">{subtext}</span>}
    </div>
  );
}
