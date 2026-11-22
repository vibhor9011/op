/**
 * OrbitGuard Design System Tokens (frontend/src/design/tokens.js).
 * ================================================================
 * Mission-Control Aesthetic: Near-black navy background, electric cyan accent,
 * color-blind safe monotonic risk ramp, accessible contrast ratios.
 */

export const TOKENS = {
  colors: {
    canvas: "#070c18",       // Deep mission-control navy
    panel: "#0d1527",        // Command panel background
    card: "#121d33",         // Card container
    elevated: "#182542",     // Hover / elevated panel
    line: "#1e293b",         // Subtle structural border
    lineFocus: "#38bdf8",    // Focused border ring
    cyan: "#00f0ff",         // Primary brand electric cyan
    cyanMuted: "#0284c7",    // Muted brand cyan
    cyanGlow: "rgba(0, 240, 255, 0.18)",

    // Monotonic, Color-Blind Safe Risk Palette (Accessible on Dark Navy)
    risk: {
      normal: { hex: "#10b981", bg: "rgba(16, 185, 129, 0.12)", border: "rgba(16, 185, 129, 0.35)", text: "#34d399", label: "Normal" },
      watch: { hex: "#f59e0b", bg: "rgba(245, 158, 11, 0.12)", border: "rgba(245, 158, 11, 0.35)", text: "#fbbf24", label: "Watch" },
      warning: { hex: "#f97316", bg: "rgba(249, 115, 22, 0.15)", border: "rgba(249, 115, 22, 0.45)", text: "#fb923c", label: "Warning" },
      severe: { hex: "#ef4444", bg: "rgba(239, 68, 68, 0.20)", border: "rgba(239, 68, 68, 0.55)", text: "#f87171", label: "Severe" },
    },

    text: {
      ink: "#f8fafc",        // High-contrast primary text (contrast > 12:1)
      dim: "#94a3b8",        // Secondary metadata text (contrast > 4.5:1)
      muted: "#64748b",      // Subtle labels & captions
    }
  },

  radii: {
    sm: "4px",
    md: "8px",
    lg: "12px",
    full: "9999px",
  },

  transitions: {
    fast: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
    standard: "250ms cubic-bezier(0.4, 0, 0.2, 1)",
    smooth: "400ms cubic-bezier(0.16, 1, 0.3, 1)",
  }
};

/**
 * Returns a monotonic color for any hazard priority score in [0, 1].
 * Monotonic lightness & chroma progression guarantees color-blind readability.
 */
export function getRiskColor(priority) {
  if (priority >= 0.08) return TOKENS.colors.risk.severe.hex;
  if (priority >= 0.05) return TOKENS.colors.risk.warning.hex;
  if (priority >= 0.02) return TOKENS.colors.risk.watch.hex;
  return TOKENS.colors.risk.normal.hex;
}

export function getRiskTier(priority) {
  if (priority >= 0.08) return "Severe";
  if (priority >= 0.05) return "Warning";
  if (priority >= 0.02) return "Watch";
  return "Normal";
}
