/**
 * Centralized API Configuration — Mentor Portal
 * 
 * Single source of truth for all backend API URLs.
 * Vite proxies /api → http://localhost:8500 (FastAPI backend).
 */

export const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export const API = {
  auth: `${API_BASE}/api/auth/v1`,
  mentor: `${API_BASE}/api/mentor/v1`,
  mentorship: `${API_BASE}/api/mentorship/v1`,
  sessions: `${API_BASE}/api/sessions/v1`,
  user: `${API_BASE}/api/user/v1`,
  payment: `${API_BASE}/api/payment/v1`,
} as const;

export const API_CONFIG = { baseUrl: API_BASE };

export default API;
