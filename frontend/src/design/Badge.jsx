import React from "react";
import { ShieldCheck, AlertTriangle, Info, AlertOctagon } from "lucide-react";

export function Badge({ variant = "default", children, size = "sm", className = "", ...props }) {
  const sizeClasses = size === "xs" ? "text-[9px] px-1.5 py-0.5" : "text-[10px] px-2 py-0.5 font-semibold";

  let colorClasses = "bg-line/40 text-dim border border-line";
  let icon = null;

  switch (variant.toLowerCase()) {
    case "severe":
    case "crit":
      colorClasses = "bg-red-500/15 text-red-400 border border-red-500/40";
      icon = <AlertOctagon className="w-3 h-3 inline mr-1" />;
      break;
    case "warning":
    case "mod":
      colorClasses = "bg-amber-500/15 text-amber-400 border border-amber-500/40";
      icon = <AlertTriangle className="w-3 h-3 inline mr-1" />;
      break;
    case "watch":
      colorClasses = "bg-yellow-500/10 text-yellow-300 border border-yellow-500/30";
      icon = <Info className="w-3 h-3 inline mr-1" />;
      break;
    case "normal":
    case "nom":
    case "ok":
    case "validated":
      colorClasses = "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30";
      icon = <ShieldCheck className="w-3 h-3 inline mr-1" />;
      break;
    case "robust":
      colorClasses = "bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-[0_0_8px_rgba(0,240,255,0.25)]";
      break;
    case "borderline":
      colorClasses = "bg-slate-700/30 text-slate-400 border border-slate-600/40";
      break;
    case "mock":
      colorClasses = "bg-amber-600/20 text-amber-300 border border-amber-500/50";
      break;
    case "planned":
      colorClasses = "bg-slate-800/60 text-slate-400 border border-slate-700";
      break;
    default:
      break;
  }

  return (
    <span
      className={`inline-flex items-center rounded tracking-wider uppercase font-mono ${sizeClasses} ${colorClasses} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </span>
  );
}
