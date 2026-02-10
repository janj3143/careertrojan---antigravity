
import type { CohortFilters, QuadrantResponse, TermCloudResponse, CooccurrenceResponse } from "./types";
import { API } from "./apiConfig";

export type ApiConfig = { baseUrl: string }; // kept for backward compat — prefer API import

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

// ── Insights API ──────────────────────────────────────────────

export async function resolveCohort(filters: CohortFilters) {
    return http<{ cohort_id: string; count: number; profile_ids: string[]; summary: any }>(
        `${API.insights}/cohort/resolve`,
        { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(filters ?? {}) },
    );
}

export async function getQuadrant(filters: CohortFilters): Promise<QuadrantResponse> {
    return http<QuadrantResponse>(`${API.insights}/quadrant?${qs(filters)}`);
}

export async function getSkillsRadar(profileId?: string) {
    const p = profileId ? `?profile_id=${encodeURIComponent(profileId)}` : "";
    return http<{ axes: string[]; series: Array<{ label: string; values: number[] }> }>(
        `${API.insights}/skills/radar${p}`,
    );
}

export async function getTermCloud(filters: CohortFilters): Promise<TermCloudResponse> {
    return http<TermCloudResponse>(`${API.insights}/terms/cloud?${qs(filters)}`);
}

export async function getCooccurrence(filters: CohortFilters, term?: string): Promise<CooccurrenceResponse> {
    const p = new URLSearchParams(qs(filters));
    if (term) p.set("term", term);
    return http<CooccurrenceResponse>(`${API.insights}/terms/cooccurrence?${p.toString()}`);
}

export async function getNetworkGraph() {
    return http<{ nodes: any[]; edges: any[] }>(`${API.insights}/graph`);
}

export async function getVisualCatalogue() {
    return http<{ visuals: any[] }>(`${API.insights}/visuals`);
}

// ── Touchpoints API ──────────────────────────────────────────

export async function getEvidence(touchpointIds: string[]) {
    const p = new URLSearchParams();
    touchpointIds.forEach(id => p.append("touchpoint_id", id));
    return http<{ items: any[]; count: number }>(`${API.touchpoints}/evidence?${p.toString()}`);
}

export async function getTouchnots(touchpointIds: string[]) {
    const p = new URLSearchParams();
    touchpointIds.forEach(id => p.append("touchpoint_id", id));
    return http<{ items: any[]; count: number }>(`${API.touchpoints}/touchnots?${p.toString()}`);
}

export async function getUserStats() {
    return http<any>(`${API.user}/stats`);
}

export async function getUserActivity() {
    return http<any[]>(`${API.user}/activity`);
}


// --- Coaching Service ---
export type QuestionType = "General competency" | "Role-specific" | "Culture & values" | "Leadership" | "Problem-solving";

export async function generateQuestions(payload: { question_type: string; count: number; resume?: any; job?: any }) {
    return http<string[]>(`${API.coaching}/questions/generate`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

export async function reviewAnswer(payload: { question: string; answer: string; resume?: any; job?: any }) {
    return http<any>(`${API.coaching}/answers/review`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

export async function generateStarStories(payload: { focus_areas: string[]; resume?: any; job?: any }) {
    return http<any[]>(`${API.coaching}/stories/generate`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

// --- Blocker Service ---
export async function detectBlockers(payload: { jd_text: string; resume_data: any }) {
    return http<any>(`${API.coaching}/blockers/detect`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

export async function getUserBlockers(userId: number) {
    return http<any[]>(`${API.coaching}/blockers/user/${userId}`);
}

export async function generateImprovementPlans(payload: { blocker_id: string; user_id: number }) {
    return http<any>(`${API.coaching}/blockers/improvement-plans/generate`, {
        method: "POST", headers: JSON_HEADERS, body: JSON.stringify(payload)
    });
}

