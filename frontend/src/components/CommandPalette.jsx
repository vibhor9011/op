import React, { useState, useEffect, useRef } from "react";
import { Search, MapPin, Calendar, Layers, ShieldCheck, Play, X } from "lucide-react";

export default function CommandPalette({
  isOpen,
  onClose,
  districts = [],
  onSelectDistrict,
  onSelectPeriod,
  onToggleLayer,
  onOpenTrust,
  onOpenDemo
}) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Build searchable items
  const items = [
    // Top actions
    { id: "act-trust", label: "Open Model Trust & Pitch Claims Audit", category: "Actions", icon: ShieldCheck, action: onOpenTrust },
    { id: "act-demo", label: "Launch Guided Backtest Demo (2019–2022)", category: "Actions", icon: Play, action: onOpenDemo },
    { id: "act-layer-extent", label: "Toggle Sentinel-1 SAR Flood Inundation Layer", category: "Layers", icon: Layers, action: () => onToggleLayer("extent") },
    { id: "act-layer-unc", label: "Toggle Conformal Uncertainty Bounds Layer", category: "Layers", icon: Layers, action: () => onToggleLayer("uncertainty") },

    // Key Historical Periods
    { id: "per-2022-06", label: "Jump to June 2022 (Peak Flood Event)", category: "Periods", icon: Calendar, action: () => onSelectPeriod("2022-06") },
    { id: "per-2020-07", label: "Jump to July 2020 (Severe Monsoon Flood)", category: "Periods", icon: Calendar, action: () => onSelectPeriod("2020-07") },
    { id: "per-2019-07", label: "Jump to July 2019 (Sentinel-1 SAR Footprint)", category: "Periods", icon: Calendar, action: () => onSelectPeriod("2019-07") },
    { id: "per-2021-08", label: "Jump to August 2021 (Drought Moisture Deficit)", category: "Periods", icon: Calendar, action: () => onSelectPeriod("2021-08") },

    // Districts (all 33)
    ...districts.map((d) => ({
      id: `dist-${d.id}`,
      label: `${d.name} (${d.id}) — Rank #${d.rank} · ${d.tier}`,
      category: "Districts",
      icon: MapPin,
      action: () => onSelectDistrict(d.id)
    }))
  ];

  const filtered = query.trim()
    ? items.filter((it) => it.label.toLowerCase().includes(query.toLowerCase()) || it.category.toLowerCase().includes(query.toLowerCase()))
    : items.slice(0, 12);

  const handleKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((idx) => (idx + 1) % Math.max(1, filtered.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((idx) => (idx - 1 + filtered.length) % Math.max(1, filtered.length));
    } else if (e.key === "Enter" && filtered[selectedIndex]) {
      e.preventDefault();
      filtered[selectedIndex].action();
      onClose();
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-[9999] flex items-start justify-center pt-24 p-4 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-xl rounded-lg border border-cyan/40 bg-panel shadow-2xl overflow-hidden flex flex-col font-sans">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-line bg-card/80 gap-3">
          <Search className="w-4 h-4 text-cyan shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Type a district name, period (e.g. 2022-06), or command..."
            className="w-full bg-transparent text-ink placeholder:text-dim/60 text-xs focus:outline-none font-mono"
          />
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded border border-line bg-elevated text-[9px] font-mono text-dim">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 divide-y divide-line/30">
          {filtered.length === 0 ? (
            <div className="p-6 text-center text-dim text-xs font-mono">No matching districts or commands found.</div>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    item.action();
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`px-3 py-2.5 rounded flex items-center justify-between cursor-pointer text-xs font-mono transition-colors ${
                    isSelected ? "bg-cyan/15 text-cyan border border-cyan/30" : "text-ink hover:bg-elevated"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-3.5 h-3.5 ${isSelected ? "text-cyan" : "text-dim"}`} />
                    <span>{item.label}</span>
                  </div>
                  <span className="text-[9px] uppercase tracking-wider text-muted font-mono">{item.category}</span>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Hint */}
        <div className="px-4 py-2 border-t border-line bg-canvas/60 flex items-center justify-between text-[10px] font-mono text-dim">
          <span>Navigate with ↑ ↓ · Select with ↵</span>
          <span>Jump to any of 33 Assam districts</span>
        </div>
      </div>
    </div>
  );
}
