"""Pydantic Models and Schemas for OrbitGuard Early Warning API."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BaseProvenanceResponse(BaseModel):
    """Base model enforcing status, label_source and warning string embedding."""
    status: str = Field("ok", description="Response status ('ok', 'degraded', 'mock')")
    label_source: str = Field(..., description="Label family used: 'synthetic_augmentation' or 'sentinel1_derived'")
    warning: str = Field(..., description="Operational honesty and data caveat warning string")


class HealthResponse(BaseProvenanceResponse):
    """Service health status response."""
    service: str = Field("orbitguard-early-warning-service", description="Service identifier")
    version: str = Field("1.0.0", description="Semantic API version")
    data_mode: str = Field("live", description="Active data mode ('live' or 'mock')")
    validated_files_count: int = Field(0, description="Count of validated precomputed output files")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")


class HazardItem(BaseModel):
    """Hazard domain descriptor with honest validation status."""
    id: str = Field(..., examples=["flood"])
    name: str = Field(..., examples=["Riverine & Flash Inundation"])
    status_badge: str = Field(..., description="Honest badge: 'Operational Prototype', 'Demo: Index-Based', or 'Planned - no data yet'")
    description: str = Field(..., examples=["Multi-hazard early warning and response prioritization for Assam"])
    granularity: str = Field("month", examples=["month"])
    lead_times: List[str] = Field(default_factory=lambda: ["0_month", "1_month"])
    lead_wording: str = Field("1-Month Risk Outlook", description="Approved lead phrasing derived from metrics")
    spatial_units: int = Field(33, description="Number of administrative polygon units")
    has_outputs: bool = Field(True, description="Whether precomputed output predictions exist")


class HazardsResponse(BaseProvenanceResponse):
    """List of supported multi-hazard domains."""
    hazards: List[HazardItem]


class PeriodsResponse(BaseProvenanceResponse):
    """List of precomputed chronological forecast periods."""
    hazard: str = Field("flood", description="Hazard identifier")
    periods: List[str] = Field(..., description="Chronological list of available monthly periods (YYYY-MM)")


class AdvisoryModel(BaseModel):
    """Actionable operational advisory for disaster management authorities."""
    level: str = Field(..., description="Alert level: Severe, Warning, Watch, or Normal")
    headline: str = Field(..., description="Broadcast headline")
    reasons: List[str] = Field(..., description="Deterministic causal factors and rainfall drivers")
    recommended_actions: List[str] = Field(..., description="SDRF and district operational response actions")
    confidence: str = Field(..., description="Confidence categorization based on predictive band width")
    disclaimer: str = Field(
        "Decision support only; confirm with ASDMA/IMD official advisories.",
        description="Mandatory official verification disclaimer"
    )


class ZoneDrivers(BaseModel):
    """Local precipitation and hydrologic drivers."""
    rain_total_mm: Optional[float] = None
    rain_cum3m_mm: Optional[float] = None
    rain_anom_mm: Optional[float] = None


class ZoneItem(BaseModel):
    """District-level forecast and response prioritization entity."""
    id: str = Field(..., examples=["G01"], description="Canonical geometry identifier (G01..G33)")
    name: str = Field(..., examples=["Baksa"], description="Administrative district name")
    p_low: float = Field(..., ge=0.0, le=1.0, description="Lower CQR conformalized uncertainty bound")
    p_mid: float = Field(..., ge=0.0, le=1.0, description="Calibrated flood exceedance probability")
    p_high: float = Field(..., ge=0.0, le=1.0, description="Upper CQR conformalized uncertainty bound")
    exposure: float = Field(..., ge=0.0, le=1.0, description="Normalized multi-factor exposure score")
    priority: float = Field(..., ge=0.0, description="Response prioritization score (p_mid * exposure)")
    rank: int = Field(..., ge=1, le=33, description="Statewide priority rank (1 = highest urgency)")
    robust: bool = Field(..., description="True if zone ranks in top 5 under both p_mid and p_high")
    drivers: Optional[ZoneDrivers] = None
    observed_flood_km2: Optional[float] = Field(None, description="Observed/extracted flooded area in square kilometers")
    observed_flood_frac: Optional[float] = Field(None, description="Observed flood area as fraction of district area")
    advisory: AdvisoryModel = Field(..., description="Operational early warning advisory")


class ZonesResponse(BaseProvenanceResponse):
    """Complete zone-level forecast collection for a period."""
    hazard: str
    granularity: str
    period: str
    lead: str
    lead_wording: str
    zones: List[ZoneItem]


class RankingResponse(BaseProvenanceResponse):
    """Sorted prioritization ranking for humanitarian response resource allocation."""
    hazard: str
    period: str
    lead: str
    lead_wording: str
    ranking: List[ZoneItem]
    top_5_robust: List[str] = Field(..., description="List of district names with robust high-priority ranking")


class ZoneAdvisoryItem(BaseModel):
    """District advisory pairing."""
    zone_id: str
    district_name: str
    priority: float
    rank: int
    advisory: AdvisoryModel


class AdvisoriesResponse(BaseProvenanceResponse):
    """Full operational advisory collection for all districts."""
    hazard: str
    period: str
    lead: str
    advisories: List[ZoneAdvisoryItem]


class DriverExplanation(BaseModel):
    """Attribution item explaining a predictive factor."""
    feature: str = Field(..., examples=["rain_cum3m_mm"])
    importance: float = Field(..., description="Attribution score / absolute SHAP importance")
    value: Optional[float] = Field(None, description="Local feature magnitude")
    plain_language: str = Field(..., description="Human-readable explanation of driver impact")


class ExplainResponse(BaseProvenanceResponse):
    """Top-5 SHAP feature explanations for a specified district zone."""
    zone_id: str
    district: str
    period: str
    top_drivers: List[DriverExplanation]


class TimelineItem(BaseModel):
    """Monthly progression item for risk and precipitation."""
    period: str
    p_low: float
    p_mid: float
    p_high: float
    priority: float
    rank: int
    rain_total_mm: Optional[float] = None
    rain_cum3m_mm: Optional[float] = None
    rain_anom_mm: Optional[float] = None


class TimelineResponse(BaseProvenanceResponse):
    """Multi-period trajectory for a district or statewide aggregate."""
    zone_id: Optional[str] = None
    district_name: Optional[str] = None
    hazard: str
    timeline: List[TimelineItem]


class OverviewResponse(BaseProvenanceResponse):
    """High-level summary of active alerts and statewide exposure."""
    hazard: str
    period: str
    lead: str
    lead_wording: str
    active_alerts_total: int
    severe_alerts_count: int
    warning_alerts_count: int
    watch_alerts_count: int
    normal_count: int
    top_priority_district: str
    statewide_mean_risk: float
    top_5_robust: List[str]


class MetricsResponse(BaseProvenanceResponse):
    """Model validation, backtest, and pitch deck claims verification."""
    results: Dict[str, Any]
    event_backtest: Dict[str, Any]
    claims_table: Dict[str, Any]


class ProvenanceResponse(BaseProvenanceResponse):
    """Audit provenance, synthetic circularity findings, and operational limitations."""
    mode: str
    spatial_units: int
    vintage: str
    data_audit_summary: Dict[str, Any]
    sar_independence_caveat: str
    lead_time_limitation: str
    asdma_disclaimer: str


class ErrorResponse(BaseProvenanceResponse):
    """Standardized error payload embedding mandatory caveats."""
    detail: str
