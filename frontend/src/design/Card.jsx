import React from "react";

export function Card({ children, className = "", hover = false, onClick = null, ...props }) {
  return (
    <div
      onClick={onClick}
      className={`rounded-md border border-line bg-card p-4 transition-all duration-200 ${
        hover ? "hover:border-cyan/40 hover:bg-elevated cursor-pointer" : ""
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function GlassPanel({ children, className = "", ...props }) {
  return (
    <div
      className={`rounded-md border border-line/80 bg-panel/85 backdrop-blur-md shadow-2xl ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
