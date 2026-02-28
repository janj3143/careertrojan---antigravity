from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, conint, confloat

AxisKey = str
Quadrant = Literal["Q1", "Q2", "Q3", "Q4"]
TrendMethod = Literal["lowess", "poly2", "poly3"]
ScaleType = Literal["linear", "log"]


class SpiderAxis(BaseModel):
    key: AxisKey
    label: str
    score: conint(ge=0, le=100)
    confidence: confloat(ge=0, le=1) = 0.7
    peer_percentile: Optional[confloat(ge=0, le=100)] = None
    top_contributors: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)


class SpiderProfile(BaseModel):
    profile_id: str
    job_family: str
    cohort_id: Optional[str] = None
    axes: List[SpiderAxis]
    overall_fit_score: Optional[conint(ge=0, le=100)] = None
    overall_confidence: Optional[confloat(ge=0, le=1)] = None
    created_at_iso: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ActionBecause(BaseModel):
    gap_axis_keys: List[AxisKey] = Field(default_factory=list)
    gap_peer_percentiles: Dict[AxisKey, confloat(ge=0, le=100)] = Field(default_factory=dict)
    missing_evidence: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class CoveyAction(BaseModel):
    action_id: str
    title: str
    description: str
    effort_friction: confloat(ge=0, le=100)
    impact_potential: confloat(ge=0, le=100)
    quadrant: Quadrant
    axis_effects: Dict[AxisKey, conint(ge=-100, le=100)]
    steps: List[str] = Field(default_factory=list)
    example_prompts: List[str] = Field(default_factory=list)
    confidence: confloat(ge=0, le=1) = 0.7
    because: ActionBecause = Field(default_factory=ActionBecause)
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class CoveyAxisSpec(BaseModel):
    x_label: str = "Effort / Friction"
    y_label: str = "Expected Impact"
    x_unit: str = "0-100"
    y_unit: str = "0-100"


class CoveyActionLens(BaseModel):
    lens_id: str
    title: str
    axis_spec: CoveyAxisSpec = Field(default_factory=CoveyAxisSpec)
    spider_profile_id: str
    cohort_id: Optional[str] = None
    job_family: str
    actions: List[CoveyAction]
    created_at_iso: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AxisSpec(BaseModel):
    key: str
    label: str
    unit: Optional[str] = None
    scale: ScaleType = "linear"
    min: Optional[float] = None
    max: Optional[float] = None


class Density2D(BaseModel):
    algo: Literal["hist2d"] = "hist2d"
    x_edges: List[float]
    y_edges: List[float]
    z: List[List[float]]
    total_n: int
    clipped_n: Optional[int] = None


class Point(BaseModel):
    x: float
    y: float
    id: Optional[str] = None
    label: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class TrendBand(BaseModel):
    x: List[float]
    y: List[float]
    y_lo: Optional[List[float]] = None
    y_hi: Optional[List[float]] = None
    method: TrendMethod = "lowess"


class QuadrantSpec(BaseModel):
    x_split: float
    y_split: float
    labels: Dict[str, str]


class ExplainBlocker(BaseModel):
    key: str
    label: str
    impact_before: int
    impact_after: int


class ExplainSpec(BaseModel):
    x_percentile: Optional[float] = None
    y_percentile: Optional[float] = None
    note: Optional[str] = None
    top_blockers: List[ExplainBlocker] = Field(default_factory=list)


class ChartLens(BaseModel):
    title: str
    x: AxisSpec
    y: AxisSpec
    density: Optional[Density2D] = None
    sample_points: List[Point] = Field(default_factory=list)
    trend: Optional[TrendBand] = None
    exceptions_above: List[Point] = Field(default_factory=list)
    exceptions_below: List[Point] = Field(default_factory=list)
    quadrants: Optional[QuadrantSpec] = None
    explain: Optional[ExplainSpec] = None
    created_at_iso: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
