
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

export type LegacyRadarResponse = {
    axes: string[];
    series: Array<{ label: string; values: number[] }>;
};

export type StructuralDomainResponse = {
    axes: string[];
    user_values: number[];
    peer_median: number[];
    target_role_median: number[];
    domain_score: number;
    percentile: number;
    delta_vs_peer_median: number;
    delta_vs_target_role: number;
};

export type StructuralRadarResponse = {
    model: "structural_v1";
    profile_id?: string;
    axes: string[];
    series: Array<{ label: string; values: number[] }>;
    overview: {
        strategic_score: number;
        leadership_score: number;
        operational_score: number;
        structural_coherence_score: number;
        strategic_operational_gap: number;
        profile_shape: string;
    };
    domains: {
        strategic: StructuralDomainResponse;
        leadership: StructuralDomainResponse;
        operational: StructuralDomainResponse;
    };
    spider_options: string[];
    selected_spider_option: string;
    option_chart: {
        axes: string[];
        user_values: number[];
        peer_median: number[];
        target_role_median: number[];
    };
};

export type SkillsRadarResponse = LegacyRadarResponse | StructuralRadarResponse;
