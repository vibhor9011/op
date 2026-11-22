import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";

export function Modal({ isOpen, onClose, title, children, maxWidth = "max-w-2xl", className = "" }) {
  const modalRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={modalRef}
        className={`w-full ${maxWidth} rounded-lg border border-line bg-panel p-6 shadow-2xl relative ${className}`}
      >
        <div className="flex items-center justify-between border-b border-line pb-3 mb-4">
          <h2 id="modal-title" className="text-sm font-bold tracking-[0.14em] uppercase text-ink font-mono">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="text-dim hover:text-ink p-1 rounded hover:bg-elevated focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="max-h-[80vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}

export function Drawer({ isOpen, onClose, title, subtitle = null, children, width = "w-[440px]", className = "" }) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <aside
      role="dialog"
      aria-modal="true"
      className={`fixed top-[58px] right-0 bottom-0 z-[8000] ${width} max-w-full border-l border-line bg-panel/95 backdrop-blur-md shadow-2xl flex flex-col transition-transform duration-300 ${className}`}
    >
      <div className="flex items-start justify-between border-b border-line px-5 py-3.5 bg-card/60">
        <div>
          <h2 className="text-sm font-bold tracking-wider uppercase text-ink font-mono">{title}</h2>
          {subtitle && <p className="text-[10px] text-dim font-mono mt-0.5">{subtitle}</p>}
        </div>
        <button
          onClick={onClose}
          aria-label="Close panel"
          className="text-dim hover:text-ink p-1 rounded hover:bg-elevated focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-5">{children}</div>
    </aside>
  );
}
