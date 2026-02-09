
import type { CohortFilters, QuadrantResponse, TermCloudResponse, CooccurrenceResponse } from "./types";
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

export async function getUserStats(cfg: ApiConfig) {
    return http<any>(`${cfg.baseUrl}/api/user/v1/stats`);
}

export async function getUserActivity(cfg: ApiConfig) {
    return http<any[]>(`${cfg.baseUrl}/api/user/v1/activity`);
}


// --- Coaching Service ---
export type QuestionType = "General competency" | "Role-specific" | "Culture & values" | "Leadership" | "Problem-solving";

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

