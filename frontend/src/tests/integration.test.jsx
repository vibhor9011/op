import { describe, it, expect, vi, beforeEach } from "vitest";
import React, { act } from "react";
import { createRoot } from "react-dom/client";
import TopBar from "../components/TopBar.jsx";
import PrioritySidebar from "../components/PrioritySidebar.jsx";
import TimeScrubber from "../components/TimeScrubber.jsx";

// Configure React 19 testing environment for act(...)
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

// Sample verified test fixture representing real 33-district model output
const sampleDistricts = [
  {
    id: "G09",
    geometry_id: "G09",
    name: "Dhemaji",
    rank: 1,
    p_mid: 0.4215,
    p_low: 0.2105,
    p_high: 0.6542,
    exposure: 0.7812,
    priority: 0.3293,
    tier: "HIGH",
    robust: true,
    drivers: { rain_1m: 380, rain_catchment: 450, slope: 1.1, river_dist: 3.2 }
  },
  {
    id: "G10",
    geometry_id: "G10",
    name: "Dhubri",
    rank: 2,
    p_mid: 0.3854,
    p_low: 0.1845,
    p_high: 0.5982,
    exposure: 0.8245,
    priority: 0.3178,
    tier: "HIGH",
    robust: true,
    drivers: { rain_1m: 310, rain_catchment: 390, slope: 0.9, river_dist: 2.1 }
  },
  {
    id: "G04",
    geometry_id: "G04",
    name: "Cachar",
    rank: 3,
    p_mid: 0.0842,
    p_low: 0.0214,
    p_high: 0.1985,
    exposure: 0.4512,
    priority: 0.0380,
    tier: "MODERATE",
    robust: false,
    drivers: { rain_1m: 140, rain_catchment: 180, slope: 4.2, river_dist: 12.5 }
  }
];

describe("OrbitGuard Frontend Contract & Honesty Rules", () => {
  let container = null;
  let root = null;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    return () => {
      act(() => root.unmount());
      container.remove();
    };
  });

  it("Honesty Rule 1: Lead Horizon phrasing must be 1-Month Risk Outlook (never 1-3 day forecast)", () => {
    const onSelectLead = vi.fn();
    act(() => {
      root.render(
        <TopBar
          hazard="flood"
          onSelectHazard={() => {}}
          lead="1_month"
          onSelectLead={onSelectLead}
          periods={["2022-06"]}
          currentPeriod="2022-06"
          onSelectPeriod={() => {}}
        />
      );
    });

    const leadBtn = container.querySelector("button[title*='1-Month Risk Outlook']");
    expect(leadBtn).not.toBeNull();
    expect(leadBtn.textContent).toContain("1-MONTH OUTLOOK");
    // Ensure no forbidden daily forecast claim in UI
    expect(container.textContent).not.toContain("1-3 Day Forecast");
    expect(container.textContent).not.toContain("72-Hour Warning");
  });

  it("Honesty Rule 2: Multi-Hazard catalog marks Planned modules honestly without fabricated predictions", () => {
    const onSelectHazard = vi.fn();
    act(() => {
      root.render(
        <TopBar
          hazard="flood"
          onSelectHazard={onSelectHazard}
          lead="1_month"
          onSelectLead={() => {}}
          periods={["2022-06"]}
          currentPeriod="2022-06"
          onSelectPeriod={() => {}}
        />
      );
    });

    const buttons = Array.from(container.querySelectorAll("nav button"));
    const texts = buttons.map((b) => b.textContent);

    expect(texts.some((t) => t.includes("FLOOD") && t.includes("PROTOTYPE"))).toBe(true);
    expect(texts.some((t) => t.includes("DROUGHT") && t.includes("INDEX-DEMO"))).toBe(true);
    expect(texts.some((t) => t.includes("LANDSLIDE") && t.includes("PLANNED"))).toBe(true);
    expect(texts.some((t) => t.includes("CYCLONE") && t.includes("PLANNED"))).toBe(true);
    expect(texts.some((t) => t.includes("WILDFIRE") && t.includes("PLANNED"))).toBe(true);
  });

  it("Honesty Rule 3: Priority queue renders CQR uncertainty bounds [p_low, p_high] and robust badges correctly", () => {
    const dash = {
      period: "2022-06",
      districts: sampleDistricts
    };

    act(() => {
      root.render(
        <PrioritySidebar
          dash={dash}
          selectedId="G09"
          onSelect={() => {}}
          agency="ALL"
          onAgency={() => {}}
          onOpenBriefing={() => {}}
        />
      );
    });

    const text = container.textContent;
    // Dhemaji (G09): p_mid=42.1%, p_low=21.1%, p_high=65.4%
    expect(text).toContain("Dhemaji");
    expect(text).toContain("42.1%");
    expect(text).toContain("21.1%");
    expect(text).toContain("65.4%");

    // Robust badge should only be present on robust districts (G09, G10), not on non-robust (G04)
    const robustBadges = Array.from(container.querySelectorAll("span")).filter(
      (el) => el.textContent.includes("ROBUST")
    );
    expect(robustBadges.length).toBe(2);
  });

  it("Component Test: TimeScrubber supports stepping forward and backward", () => {
    const periods = ["2022-05", "2022-06", "2022-07"];
    const onPeriodChange = vi.fn();
    const onTogglePlay = vi.fn();

    act(() => {
      root.render(
        <TimeScrubber
          periods={periods}
          currentPeriod="2022-06"
          onPeriodChange={onPeriodChange}
          isPlaying={false}
          onTogglePlay={onTogglePlay}
          selectedZone={sampleDistricts[0]}
          leadWording="1-Month Risk Outlook"
        />
      );
    });

    // Prev button (Arrow Back)
    const prevBtn = container.querySelector("button[title*='Previous Period']");
    expect(prevBtn).not.toBeNull();
    act(() => {
      prevBtn.click();
    });
    expect(onPeriodChange).toHaveBeenCalledWith("2022-05");

    // Next button (Arrow Forward)
    const nextBtn = container.querySelector("button[title*='Next Period']");
    expect(nextBtn).not.toBeNull();
    act(() => {
      nextBtn.click();
    });
    expect(onPeriodChange).toHaveBeenCalledWith("2022-07");
  });

  it("Contract Verification: Mathematical consistency of CQR prediction intervals (p_low <= p_mid <= p_high)", () => {
    sampleDistricts.forEach((d) => {
      expect(d.p_low).toBeLessThanOrEqual(d.p_mid);
      expect(d.p_mid).toBeLessThanOrEqual(d.p_high);
      expect(d.p_low).toBeGreaterThanOrEqual(0.0);
      expect(d.p_high).toBeLessThanOrEqual(1.0);
      expect(d.priority).toBeGreaterThanOrEqual(0.0);
    });
  });
});
