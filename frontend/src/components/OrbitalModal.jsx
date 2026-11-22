import { X } from "lucide-react";

const CELLS = Array.from({ length: 14 }, (_, i) => ({ id: `EO-${String(i + 1).padStart(2, "0")}`, watch: i === 4 || i === 11 }));

export default function OrbitalModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-[2000] bg-[#102435]/45 flex items-center justify-center p-4" onClick={onClose} role="dialog" aria-modal="true" aria-label="Orbital continuity preview">
      <div className="w-full max-w-[620px] bg-panel border border-line rounded-sm" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 h-10 border-b border-line">
          <div className="flex items-center gap-3">
            <span className="font-semibold tracking-wider text-[12px]">ORBITAL: CONTINUITY</span>
            <span className="text-[9px] tracking-wider px-1.5 py-0.5 border border-mod text-mod rounded-sm">PLANNED MODULE</span>
            <span className="text-[9px] tracking-wider px-1.5 py-0.5 border border-dim text-dim rounded-sm">ILLUSTRATIVE</span>
          </div>
          <button onClick={onClose} aria-label="Close" className="text-dim hover:text-ink">
            <X size={16} strokeWidth={1.5} />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div>
            <div className="lbl mb-2">EO satellite availability · layout preview</div>
            <div className="num text-[22px] leading-none">
              12<span className="text-dim"> / 14</span> <span className="text-[11px] text-dim">operational (sample)</span>
            </div>
            <div className="grid grid-cols-7 gap-px bg-line border border-line mt-3">
              {CELLS.map((c) => (
                <div key={c.id} className="bg-canvas px-2 py-2">
                  <div className="num text-[10px] text-dim">{c.id}</div>
                  <div className="text-[10px] tracking-wider mt-0.5" style={{ color: c.watch ? "#e5a00d" : "#30a46c" }}>
                    {c.watch ? "WATCH" : "NOMINAL"}
                  </div>
                </div>
              ))}
            </div>
            <div className="text-[10px] text-dim mt-1.5">Generic placeholders. No live satellite data is connected; counts are sample values.</div>
          </div>

          <div>
            <div className="lbl mb-2">Planned pipeline</div>
            <ol className="grid grid-cols-4 gap-px bg-line border border-line text-[11px]">
              {[
                ["01", "Ingest orbital elements", "CelesTrak"],
                ["02", "Propagate orbits", "SGP4"],
                ["03", "Screen conjunctions", "miss distance + uncertainty"],
                ["04", "Flag EO assets", "disaster-monitoring continuity"],
              ].map(([n, t, s]) => (
                <li key={n} className="bg-canvas p-2">
                  <div className="num text-dim text-[10px]">{n}</div>
                  <div className="font-semibold leading-tight">{t}</div>
                  <div className="text-dim text-[10px] leading-tight mt-0.5">{s}</div>
                </li>
              ))}
            </ol>
          </div>

          <p className="text-[11px] text-dim leading-snug">
            Why it belongs: flood monitoring depends on Earth-observation satellites staying available. Orbital risk monitoring protects that data supply. This module is on the roadmap and is not implemented in the MVP.
          </p>
        </div>
      </div>
    </div>
  );
}
