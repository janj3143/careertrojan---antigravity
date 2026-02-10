/**
 * Centralized API Configuration — Admin Portal
 * 
 * Single source of truth for all backend API URLs.
 * Vite proxies /api → http://localhost:8500 (FastAPI backend).
 */

export const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export const API = {
  admin: `${API_BASE}/api/admin/v1`,
  auth: `${API_BASE}/api/auth/v1`,
  user: `${API_BASE}/api/user/v1`,
  insights: `${API_BASE}/api/insights/v1`,
  analytics: `${API_BASE}/api/analytics/v1`,
  mapping: `${API_BASE}/api/mapping/v1`,
  aiData: `${API_BASE}/api/ai_data/v1`,
  telemetry: `${API_BASE}/api/telemetry/v1`,
  logs: `${API_BASE}/api/logs/v1`,
  mentor: `${API_BASE}/api/mentor/v1`,
  payment: `${API_BASE}/api/payment/v1`,
  jobs: `${API_BASE}/api/jobs/v1`,
  taxonomy: `${API_BASE}/api/taxonomy/v1`,
} as const;

export const API_CONFIG = { baseUrl: API_BASE };

export default API;
