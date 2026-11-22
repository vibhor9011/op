import React, { useState } from "react";

export function Tooltip({ text, children, position = "top", className = "" }) {
  const [visible, setVisible] = useState(false);

  const posClasses =
    position === "bottom"
      ? "top-full mt-2 left-1/2 -translate-x-1/2"
      : position === "right"
      ? "left-full ml-2 top-1/2 -translate-y-1/2"
      : position === "left"
      ? "right-full mr-2 top-1/2 -translate-y-1/2"
      : "bottom-full mb-2 left-1/2 -translate-x-1/2";

  return (
    <div
      className={`relative inline-block ${className}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && text && (
        <div
          role="tooltip"
          className={`absolute z-50 whitespace-nowrap rounded border border-line bg-panel px-2.5 py-1 text-[10px] font-mono text-ink shadow-xl pointer-events-none ${posClasses}`}
        >
          {text}
        </div>
      )}
    </div>
  );
}
