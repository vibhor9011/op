import React, { useState } from "react";
import { Badge } from "../design/index.js";
import { getRiskColor } from "../design/tokens.js";
import { Search, Download, FileText, ChevronDown, ChevronUp, ShieldCheck, AlertTriangle, AlertOctagon, Info } from "lucide-react";

const AGENCIES = ["ALL", "SDRF", "SDMA", "DISTRICT", "NGO"];

export default function PrioritySidebar({
  dash,
  selectedId,
  onSelect,
  agency = "ALL",
  onAgency,
  onOpenBriefing
}) {
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  const rows = dash?.districts || [];
  const filteredRows = rows.filter((d) => {
    if (!search.trim()) return true;
    return d.name.toLowerCase().includes(search.toLowerCase()) || d.id.toLowerCase().includes(search.toLowerCase());
  });

  const handleToggleExpand = (id, e) => {
    e.stopPropagation();
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const handleExportCSV = () => {
    const headers = ["Rank", "Geometry_ID", "District", "Priority_Score", "Exceedance_Prob", "CQR_P_Low", "CQR_P_High", "Exposure", "Tier", "Robust"];
    const csvRows = [headers.join(",")];

    rows.forEach((d) => {
      csvRows.push([
        d.rank,
        d.id,
        `"${d.name}"`,
        d.priority.toFixed(4),
        d.p_mid.toFixed(4),
        d.p_low.toFixed(4),
        d.p_high.toFixed(4),
        d.exposure.toFixed(4),
        d.tier,
        d.robust ? "YES" : "NO"
      ].join(","));
    });

    const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `orbitguard_prioritization_${dash?.period || "current"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <aside className="w-[360px] max-lg:w-[300px] shrink-0 border-r border-line bg-panel flex flex-col min-h-0 select-none">
      {/* Header & Controls */}
      <div className="p-3 border-b border-line space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="lbl text-ink font-mono">Priority Queue (Risk × Exposure)</span>
          <span className="text-[10px] font-mono text-cyan font-bold">{rows.length} Districts</span>
        </div>

        {/* Agency Filter Tabs */}
        <div className="flex gap-px bg-canvas border border-line rounded p-0.5" role="tablist">
          {AGENCIES.map((a) => (
            <button
              key={a}
              role="tab"
              aria-selected={agency === a}
              onClick={() => onAgency(a)}
              className={`flex-1 py-1 text-[10px] font-mono tracking-wider transition-colors rounded ${
                agency === a ? "bg-cyan/15 text-cyan border border-cyan/40 font-bold" : "text-dim hover:text-ink"
              }`}
            >
              {a}
            </button>
          ))}
        </div>

        {/* Search & Export Strip */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-dim absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search 33 districts..."
              className="w-full pl-8 pr-2.5 py-1 text-[11px] font-mono rounded border border-line bg-card text-ink placeholder:text-muted focus:outline-none focus:border-cyan"
            />
          </div>

          <button
            onClick={handleExportCSV}
            className="p-1.5 rounded border border-line hover:border-cyan/40 bg-card hover:bg-elevated text-dim hover:text-cyan transition-colors"
            title="Export Prioritisation Queue as CSV"
            aria-label="Export CSV"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* District List */}
      <ul className="flex-1 overflow-y-auto divide-y divide-line/60">
        {filteredRows.map((d) => {
          const isSelected = d.id === selectedId;
          const isExpanded = expandedId === d.id;
          const riskColor = getRiskColor(d.priority);

          return (
            <li key={d.id} className={isSelected ? "bg-cyan/5" : ""}>
              <div
                onClick={() => onSelect(d.id)}
                className={`w-full text-left flex items-stretch hover:bg-elevated/70 cursor-pointer transition-colors p-2.5 gap-2.5 ${
                  isSelected ? "border-l-2 border-cyan" : ""
                }`}
              >
                {/* Rank Badge */}
                <span className="font-mono w-7 shrink-0 text-center py-1 text-dim text-xs font-bold tabular-nums">
                  #{d.rank}
                </span>

                {/* District Name & Meta */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-xs text-ink truncate">{d.name}</span>
                    <Badge variant={d.tier} size="xs">
                      {d.tier}
                    </Badge>
                    {d.robust ? (
                      <span
                        className="text-[8px] font-mono px-1 py-0.2 rounded bg-cyan/15 text-cyan border border-cyan/40 font-bold"
                        title="Robust: Ranks top-5 under both median and upper 80% bound"
                      >
                        ROBUST
                      </span>
                    ) : (
                      <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-slate-800 text-slate-400">
                        BORDERLINE
                      </span>
                    )}
                  </div>

                  <div className="text-[10px] text-muted font-mono mt-0.5">
                    Exposure: <span className="text-dim font-bold">{d.exposure.toFixed(2)}</span> · P-Mid:{" "}
                    <span className="text-cyan font-bold">{(d.p_mid * 100).toFixed(1)}%</span>{" "}
                    <span className="text-[9px] text-dim font-normal" title="80% Conformal Prediction Interval">
                      [{(d.p_low * 100).toFixed(1)}%–{(d.p_high * 100).toFixed(1)}%]
                    </span>
                  </div>
                </div>

                {/* Priority Score & Expand Arrow */}
                <div className="flex items-center gap-2 shrink-0">
                  <div className="text-right font-mono">
                    <div className="text-xs font-bold text-ink tabular-nums">{d.priority.toFixed(3)}</div>
                    <div className="text-[9px] text-muted">score</div>
                  </div>

                  <button
                    onClick={(e) => handleToggleExpand(d.id, e)}
                    className="p-1 text-dim hover:text-ink rounded hover:bg-line/40"
                    aria-label="Toggle actions"
                  >
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Expandable Accordion Body */}
              {isExpanded && (
                <div className="border-t border-line/40 bg-card/60 p-3 space-y-3 font-mono text-[11px] animate-fade-in">
                  {/* Advisory Actions */}
                  <div>
                    <div className="text-[9px] uppercase tracking-wider text-cyan font-bold mb-1.5 flex items-center justify-between">
                      <span>Action Directives ({agency})</span>
                      <button
                        onClick={() => onOpenBriefing && onOpenBriefing(d)}
                        className="text-[9px] text-dim hover:text-cyan flex items-center gap-1 font-mono"
                      >
                        <FileText className="w-3 h-3" />
                        <span>Briefing Card</span>
                      </button>
                    </div>
                    <ul className="space-y-1">
                      {(d.advisories?.[agency] || d.advisory?.recommended_actions || []).slice(0, 3).map((act, i) => (
                        <li key={i} className="flex gap-2 text-[10px] text-dim leading-snug">
                          <span className="text-cyan font-bold">{i + 1}.</span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Telemetry Strip */}
                  <div className="pt-2 border-t border-line/40 flex justify-between text-[10px] text-muted">
                    <span>
                      80% Band: [{(d.p_low * 100).toFixed(0)}%–{(d.p_high * 100).toFixed(0)}%]
                    </span>
                    <span>{d.population_lakh ? `${d.population_lakh.toFixed(1)}L Pop` : ""}</span>
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
