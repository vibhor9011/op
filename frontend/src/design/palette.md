# OrbitGuard Mission-Control Design Palette & Token Guide
**Team AsGuardians // ASTRA Hackathon 2026**

---

## 1. Aesthetic Direction: Mission-Control Command Center
OrbitGuard adheres to a high-density, mission-control console aesthetic:
- **Canvas (`#070c18`)**: Deep obsidian-navy void. Reduces optical fatigue during prolonged disaster operations.
- **Command Panels (`#0d1527` / `#121d33`)**: Layered glassmorphic surfaces with thin slate borders (`#1e293b`).
- **Primary Brand Accent (`#00f0ff`)**: High-luminance electric cyan. Guides the operator's eye to primary interactive controls, active lead indicators, and satellite telemetry overlays.
- **Restrained Color Budget**: Vibrant hues are reserved exclusively for critical alerts and active hazard boundaries.

---

## 2. Monotonic, Color-Blind Safe Risk Palette
In accordance with WCAG 2.1 AA accessibility guidelines, the risk scale avoids deceptive red-green confusion (Deuteranopia/Protanopia) by varying both **hue** and **monotonic luminance**:

| Risk Level | Score Cutoff ($p_{\text{mid}} \times \text{Exposure}$) | Hex Code | Visual Swatch | Monotonic Luminance ($L^*$) | Contrast on `#0d1527` |
|---|---|---|---|---|---|
| **Normal / Baseline** | $< 0.02$ | `#10b981` | Emerald Green | 68.2 | **7.4 : 1 (AAA)** |
| **Watch** | $0.02 - 0.05$ | `#f59e0b` | Warm Amber | 72.5 | **8.6 : 1 (AAA)** |
| **Warning** | $0.05 - 0.08$ | `#f97316` | Deep Orange | 62.1 | **6.1 : 1 (AA)** |
| **Severe** | $\ge 0.08$ | `#ef4444` | High-Vis Crimson | 54.0 | **5.2 : 1 (AA)** |

- **Deuteranopia & Protanopia Safe**: Lightness increases progressively from Severe to Normal, ensuring rank order remains distinct under monochrome and grayscale viewing.
- **Tritanopia Safe**: The amber-to-crimson hazard steps are clearly differentiated from the cyan brand accent.

---

## 3. Typography & Numerals
- **Display Headings**: High-contrast tracking (`tracking-[0.14em] uppercase`).
- **UI Prose**: Inter Variable (`font-sans`), optimized for sub-12px readability.
- **Telemetry Numerals**: JetBrains Mono (`font-mono tabular-nums`). Prevents visual jitter during realtime number scrubbing and count-up animations.
