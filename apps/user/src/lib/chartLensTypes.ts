export type ScaleType = "linear" | "log";
export type TrendMethod = "lowess" | "poly2" | "poly3";
export type Quadrant = "Q1" | "Q2" | "Q3" | "Q4";

export interface AxisSpec {
  key: string;
  label: string;
  unit?: string | null;
  scale: ScaleType;
  min?: number | null;
  max?: number | null;
}

export interface Density2D {
  algo: "hist2d";
  x_edges: number[];
  y_edges: number[];
  z: number[][];
  total_n: number;
  clipped_n?: number | null;
}

export interface Point {
  x: number;
  y: number;
  id?: string | null;
  label?: string | null;
  meta: Record<string, any>;
}

export interface TrendBand {
  x: number[];
  y: number[];
  y_lo?: number[] | null;
  y_hi?: number[] | null;
  method: TrendMethod;
}

export interface QuadrantSpec {
  x_split: number;
  y_split: number;
  labels: Record<string, string>;
}

export interface ExplainBlocker {
  key: string;
  label: string;
  impact_before: number;
  impact_after: number;
}

export interface ExplainSpec {
  x_percentile?: number | null;
  y_percentile?: number | null;
  note?: string | null;
  top_blockers: ExplainBlocker[];
}

export interface ChartLens {
  title: string;
  x: AxisSpec;
  y: AxisSpec;
  density?: Density2D | null;
  sample_points: Point[];
  trend?: TrendBand | null;
  exceptions_above: Point[];
  exceptions_below: Point[];
  quadrants?: QuadrantSpec | null;
  explain?: ExplainSpec | null;
  created_at_iso: string;
}

export interface SpiderAxis {
  key: string;
  label: string;
  score: number;
  confidence: number;
  peer_percentile?: number | null;
  top_contributors: string[];
  missing_evidence: string[];
}

export interface SpiderProfile {
  profile_id: string;
  job_family: string;
  cohort_id?: string | null;
  axes: SpiderAxis[];
  overall_fit_score?: number | null;
  overall_confidence?: number | null;
  created_at_iso: string;
}

export interface ActionBecause {
  gap_axis_keys: string[];
  gap_peer_percentiles: Record<string, number>;
  missing_evidence: string[];
  notes: string[];
}

export interface CoveyAction {
  action_id: string;
  title: string;
  description: string;
  effort_friction: number;
  impact_potential: number;
  quadrant: Quadrant;
  axis_effects: Record<string, number>;
  steps: string[];
  example_prompts: string[];
  confidence: number;
  because: ActionBecause;
  tags: string[];
  meta: Record<string, any>;
}

export interface CoveyAxisSpec {
  x_label: string;
  y_label: string;
  x_unit: string;
  y_unit: string;
}

export interface CoveyActionLens {
  lens_id: string;
  title: string;
  axis_spec: CoveyAxisSpec;
  spider_profile_id: string;
  cohort_id?: string | null;
  job_family: string;
  actions: CoveyAction[];
  created_at_iso: string;
}
