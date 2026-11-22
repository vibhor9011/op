import React, { useRef } from "react";

export function Tabs({ tabs = [], activeId, onChange, className = "" }) {
  const tabRefs = useRef([]);

  const handleKeyDown = (e, index) => {
    let nextIndex = index;
    if (e.key === "ArrowRight") {
      nextIndex = (index + 1) % tabs.length;
    } else if (e.key === "ArrowLeft") {
      nextIndex = (index - 1 + tabs.length) % tabs.length;
    } else if (e.key === "Home") {
      nextIndex = 0;
    } else if (e.key === "End") {
      nextIndex = tabs.length - 1;
    }

    if (nextIndex !== index) {
      e.preventDefault();
      onChange(tabs[nextIndex].id);
      tabRefs.current[nextIndex]?.focus();
    }
  };

  return (
    <div role="tablist" className={`flex border-b border-line gap-2 ${className}`}>
      {tabs.map((tab, idx) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            ref={(el) => (tabRefs.current[idx] = el)}
            role="tab"
            aria-selected={isActive}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onChange(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, idx)}
            className={`px-3 py-2 text-[11px] font-semibold tracking-wider uppercase transition-colors relative ${
              isActive
                ? "text-cyan border-b-2 border-cyan"
                : "text-dim hover:text-ink border-b-2 border-transparent"
            } focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan`}
          >
            {tab.label}
            {tab.badge && <span className="ml-2">{tab.badge}</span>}
          </button>
        );
      })}
    </div>
  );
}
