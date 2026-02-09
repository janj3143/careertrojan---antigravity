
export type CohortFilters = {
    target_role?: string; industry?: string; region?: string; seniority_band?: string;
    time_window?: string; cohort_id?: string;
};

export type InsightSelection = {
    source_visual_id: string;
    selection_type: "point" | "term" | "node";
    ids: string[];
    touchpoint_ids: string[];
    filters?: CohortFilters;
};

export type QuadrantResponse = {
    x_label: string; y_label: string; x_threshold: number; y_threshold: number;
    points: Array<{ id: string; label: string; x: number; y: number; confidence?: number; touchpoint_ids?: string[] }>;
};

export type TermCloudResponse = {
    terms: Array<{ text: string; value: number; touchpoint_ids?: string[] }>;
};

export type CooccurrenceResponse = { edges: Array<{ source: string; target: string; weight: number }> };
