/**
 * Centralized API Configuration — User Portal
 * 
 * Single source of truth for all backend API URLs.
 * All pages/components should import from here instead of defining their own.
 * 
 * In dev mode, Vite proxies /api → http://localhost:8500 (FastAPI backend).
 * In production, nginx handles the proxy.
 */

export const API_BASE = import.meta.env.VITE_API_URL || '';

/** Namespaced API endpoints — all use /api/{domain}/v1 prefix */
export const API = {
  auth: `${API_BASE}/api/auth/v1`,
  user: `${API_BASE}/api/user/v1`,
  resume: `${API_BASE}/api/resume/v1`,
  coaching: `${API_BASE}/api/coaching/v1`,
  jobs: `${API_BASE}/api/jobs/v1`,
  payment: `${API_BASE}/api/payment/v1`,
  rewards: `${API_BASE}/api/rewards/v1`,
  mentorship: `${API_BASE}/api/mentorship/v1`,
  mentor: `${API_BASE}/api/mentor/v1`,
  insights: `${API_BASE}/api/insights/v1`,
  taxonomy: `${API_BASE}/api/taxonomy/v1`,
  credits: `${API_BASE}/api/credits/v1`,
  sessions: `${API_BASE}/api/sessions/v1`,
  aiData: `${API_BASE}/api/ai_data/v1`,
} as const;

/** Legacy alias — prefer named imports above */
export const API_CONFIG = { baseUrl: API_BASE };

export default API;
