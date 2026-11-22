/**
 * OrbitGuard API TypeScript Contract (frontend/src/services/apiTypes.ts).
 * =======================================================================
 * Auto-generated from OpenAPI 3.1.0 schema (service/app.py & service/models.py).
 * Enforces typed contracts, non-null guarantees, and honesty metadata embedding.
 */

export interface ProvenanceMeta {
  status: "ok" | "degraded" | "mock" | "error";
  label_source: string;
  warning: string;
}

export interface HealthResponse extends ProvenanceMeta {
  service: string;
  version: string;
  data_mode: "live" | "mock";
  validated_files_count: number;
  timestamp: string;
}

export interface HazardItem {
  id: string;
  name: string;
  status_badge: string;
  description: string;
  granularity: string;
  lead_times: string[];
  lead_wording: string;
  spatial_units: number;
  has_outputs: boolean;
}

export interface HazardsResponse extends ProvenanceMeta {
  hazards: HazardItem[];
}

export interface PeriodsResponse extends ProvenanceMeta {
  hazard: string;
  periods: string[];
}

export interface AdvisoryModel {
  level: "Severe" | "Warning" | "Watch" | "Normal";
  headline: string;
  reasons: string[];
  recommended_actions: string[];
  confidence: string;
  disclaimer: string;
}

export interface ZoneDrivers {
  rain_total_mm?: number | null;
  rain_cum3m_mm?: number | null;
  rain_anom_mm?: number | null;
}

export interface ZoneItem {
  id: string;
  name: string;
  p_low: number;
  p_mid: number;
  p_high: number;
  exposure: number;
  priority: number;
  rank: number;
  robust: boolean;
  drivers?: ZoneDrivers | null;
  observed_flood_km2?: number | null;
  observed_flood_frac?: number | null;
  advisory: AdvisoryModel;
}

export interface ZonesResponse extends ProvenanceMeta {
  hazard: string;
  granularity: string;
  period: string;
  lead: string;
  lead_wording: string;
  zones: ZoneItem[];
}

export interface RankingResponse extends ProvenanceMeta {
  hazard: string;
  period: string;
  lead: string;
  lead_wording: string;
  ranking: ZoneItem[];
  top_5_robust: string[];
}

export interface ZoneAdvisoryItem {
  zone_id: string;
  district_name: string;
  priority: number;
  rank: number;
  advisory: AdvisoryModel;
}

export interface AdvisoriesResponse extends ProvenanceMeta {
  hazard: string;
  period: string;
  lead: string;
  advisories: ZoneAdvisoryItem[];
}

export interface DriverExplanation {
  feature: string;
  importance: number;
  value?: number | null;
  plain_language: string;
}

export interface ExplainResponse extends ProvenanceMeta {
  zone_id: string;
  district: string;
  period: string;
  top_drivers: DriverExplanation[];
}

export interface TimelineItem {
  period: string;
  p_low: number;
  p_mid: number;
  p_high: number;
  priority: number;
  rank: number;
  rain_total_mm?: number | null;
  rain_cum3m_mm?: number | null;
  rain_anom_mm?: number | null;
}

export interface TimelineResponse extends ProvenanceMeta {
  zone_id?: string | null;
  district_name?: string | null;
  hazard: string;
  timeline: TimelineItem[];
}

export interface OverviewResponse extends ProvenanceMeta {
  hazard: string;
  period: string;
  lead: string;
  lead_wording: string;
  active_alerts_total: number;
  severe_alerts_count: number;
  warning_alerts_count: number;
  watch_alerts_count: number;
  normal_count: number;
  top_priority_district: string;
  statewide_mean_risk: number;
  top_5_robust: string[];
}

export interface DeckClaimItem {
  claim: string;
  status: "validated" | "partly" | "not_validated" | "planned";
  evidence_file: string;
  number?: string | null;
  notes?: string;
}

export interface MetricsResponse extends ProvenanceMeta {
  results: Record<string, any>;
  event_backtest: Record<string, any>;
  claims_table: Record<string, DeckClaimItem>;
}

export interface ProvenanceResponse extends ProvenanceMeta {
  mode: string;
  spatial_units: number;
  vintage: string;
  data_audit_summary: Record<string, any>;
  sar_independence_caveat: string;
  lead_time_limitation: string;
  asdma_disclaimer: string;
}
