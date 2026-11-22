import React from "react";

export function Slider({ min = 0, max = 100, step = 1, value, onChange, label, className = "", unit = "" }) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <div className="flex justify-between text-[10px] font-mono text-dim">
          <span className="uppercase tracking-wider">{label}</span>
          <span className="text-cyan font-bold tabular-nums">
            {value}
            {unit}
          </span>
        </div>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={label || "Slider"}
        aria-valuenow={value}
        aria-valuemin={min}
        aria-valuemax={max}
        className="w-full h-1.5 bg-line rounded-lg appearance-none cursor-pointer accent-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan"
      />
    </div>
  );
}
