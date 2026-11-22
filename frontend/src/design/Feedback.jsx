import React from "react";
import { AlertCircle, XCircle } from "lucide-react";

export function Skeleton({ className = "", width, height }) {
  return (
    <div
      style={{ width, height }}
      className={`animate-pulse rounded bg-line/60 ${className}`}
      aria-hidden="true"
    />
  );
}

export function ErrorBanner({ title = "Operational Notice", message, onDismiss = null, className = "" }) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className={`rounded-md border border-red-500/40 bg-red-950/40 p-3 text-red-200 flex items-start gap-3 shadow-lg ${className}`}
    >
      <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
      <div className="flex-1 text-[11px]">
        <div className="font-bold tracking-wide uppercase font-mono text-red-300">{title}</div>
        <div className="mt-0.5 leading-relaxed text-red-200/90">{message}</div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-400 hover:text-red-200 p-0.5 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red-400"
          aria-label="Dismiss error"
        >
          <XCircle className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon: Icon = null, title, message, action = null, className = "" }) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center text-dim rounded-md border border-line/40 bg-card/40 ${className}`}>
      {Icon && <Icon className="w-8 h-8 mb-3 text-dim/60" />}
      <div className="text-xs font-bold uppercase tracking-wider text-ink font-mono">{title}</div>
      <div className="text-[11px] text-dim/80 max-w-xs mt-1 leading-relaxed">{message}</div>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Toast({ message, type = "info", onClose = null }) {
  if (!message) return null;
  const borderCol = type === "error" ? "border-red-500/60" : type === "success" ? "border-emerald-500/60" : "border-cyan/60";

  return (
    <div
      role="status"
      className={`fixed bottom-5 right-5 z-50 rounded-md border ${borderCol} bg-panel/95 backdrop-blur px-4 py-2.5 text-xs text-ink shadow-2xl flex items-center gap-3 animate-fade-in`}
    >
      <span>{message}</span>
      {onClose && (
        <button onClick={onClose} className="text-dim hover:text-ink text-[10px] ml-2">
          ✕
        </button>
      )}
    </div>
  );
}
