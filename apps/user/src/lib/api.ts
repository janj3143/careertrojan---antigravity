
import type { CohortFilters, QuadrantResponse, TermCloudResponse, CooccurrenceResponse, SkillsRadarResponse } from "./types";
export type ApiConfig = { baseUrl: string }; // "/api"
const JSON_HEADERS = { "Content-Type": "application/json" };

async function http<T>(url: string, init?: RequestInit): Promise<T> {
    const headers = new Headers(init?.headers);
    const token = localStorage.getItem("token");
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");

    const res = await fetch(url, { ...init, headers });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text().catch(() => "")}`);
    return (await res.json()) as T;
}

function qs(filters: CohortFilters) {
    const p = new URLSearchParams();
    Object.entries(filters ?? {}).forEach(([k, v]) => v && p.set(k, String(v)));
    return p.toString();
}

export async function resolveCohort(cfg: ApiConfig, filters: CohortFilters) {
    return http<{ cohort_id: string; count: number }>(`${cfg.baseUrl}/insights/cohort/resolve`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(filters ?? {}),
    });
}

export async function getQuadrant(cfg: ApiConfig, filters: CohortFilters): Promise<QuadrantResponse> {
    return http<QuadrantResponse>(`${cfg.baseUrl}/insights/quadrant?${qs(filters)}`);
}
export async function getTermCloud(cfg: ApiConfig, filters: CohortFilters): Promise<TermCloudResponse> {
    return http<TermCloudResponse>(`${cfg.baseUrl}/insights/terms/cloud?${qs(filters)}`);
}
export async function getCooccurrence(cfg: ApiConfig, filters: CohortFilters, term?: string): Promise<CooccurrenceResponse> {
    const p = new URLSearchParams(qs(filters));
    if (term) p.set("term", term);
    return http<CooccurrenceResponse>(`${cfg.baseUrl}/insights/terms/cooccurrence?${p.toString()}`);
}

export async function getSkillsRadar(
    cfg: ApiConfig,
    options?: {
        profile_id?: string;
        model?: "legacy" | "structural_v1";
        spider_option?: "three_domain" | "leadership_strategy_vision_management" | "operational_execution";
        target_role?: string;
    }
): Promise<SkillsRadarResponse> {
    const p = new URLSearchParams();
    if (options?.profile_id) p.set("profile_id", options.profile_id);
    if (options?.model) p.set("model", options.model);
    if (options?.spider_option) p.set("spider_option", options.spider_option);
    if (options?.target_role) p.set("target_role", options.target_role);

    const suffix = p.toString() ? `?${p.toString()}` : "";
    return http<SkillsRadarResponse>(`${cfg.baseUrl}/insights/skills/radar${suffix}`);
}

export async function getUserStats(cfg: ApiConfig) {
    return http<any>(`${cfg.baseUrl}/api/user/v1/stats`);
}

export async function getUserActivity(cfg: ApiConfig) {
    return http<any[]>(`${cfg.baseUrl}/api/user/v1/activity`);
}


// --- Coaching Service ---
export type QuestionType =
    | "General competency"
    | "Role-specific"
    | "Role-specific & Performance Questions"
    | "Marketing"
    | "Technical"
    | "Development"
    | "Finance"
    | "Sales"
    | "Engineering"
    | "Management"
    | "Culture & values"
    | "Leadership"
    | "Problem-solving";

export async function generateQuestions(cfg: ApiConfig, payload: { question_type: string; count: number; resume?: any; job?: any }) {
    return http<string[]>(`${cfg.baseUrl}/api/coaching/v1/questions/generate`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

export async function reviewAnswer(cfg: ApiConfig, payload: { question: string; answer: string; resume?: any; job?: any }) {
    return http<any>(`${cfg.baseUrl}/api/coaching/v1/answers/review`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

export async function generateStarStories(cfg: ApiConfig, payload: { focus_areas: string[]; resume?: any; job?: any }) {
    return http<any[]>(`${cfg.baseUrl}/api/coaching/v1/stories/generate`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

export async function submitInterviewLearningFeedback(
    cfg: ApiConfig,
    payload: {
        question_type: string;
        question: string;
        helpful?: boolean;
        answer_score?: number;
        session_outcome?: string;
        resume?: any;
        job?: any;
    }
) {
    return http<any>(`${cfg.baseUrl}/api/coaching/v1/learning/feedback`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

export type CompanyBriefingResponse = {
    company_name: string;
    company_overview: {
        what_they_do?: string;
        website?: string;
        industry?: string;
        location?: string;
        confidence_score?: number;
    };
    similar_hiring_history: {
        employed_similar_profiles: boolean;
        count: number;
        years: number[];
        sample_roles: string[];
        overlap_skills: string[];
        profiles_scanned: number;
    };
    highlights: {
        recent_news: Array<{
            title?: string;
            snippet?: string;
            source?: string;
            url?: string;
            date?: string;
        }>;
        new_appointments: string[];
        new_products_or_developments: string[];
        detected_technologies: string[];
    };
};

export async function getCompanyBriefing(
    cfg: ApiConfig,
    payload: { company_name: string; resume?: any; job?: any; max_profile_files?: number }
): Promise<CompanyBriefingResponse> {
    return http<CompanyBriefingResponse>(`${cfg.baseUrl}/api/intelligence/v1/company/briefing`, {
        method: "POST",
        headers: JSON_HEADERS,
        body: JSON.stringify(payload),
    });
}

// --- Blocker Service ---
export async function detectBlockers(cfg: ApiConfig, payload: { jd_text: string; resume_data: any }) {
    return http<any>(`${cfg.baseUrl}/api/blockers/detect`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

export async function getUserBlockers(cfg: ApiConfig, userId: number) {
    return http<any[]>(`${cfg.baseUrl}/api/blockers/user/${userId}`);
}

export async function generateImprovementPlans(cfg: ApiConfig, payload: { blocker_id: string; user_id: number }) {
    return http<any>(`${cfg.baseUrl}/api/blockers/improvement-plans/generate`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

