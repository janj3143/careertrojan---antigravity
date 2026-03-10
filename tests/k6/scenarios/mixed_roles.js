import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8510';

function jsonHeaders(token) {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function roleToken(roleKey) {
  return __ENV[roleKey] || '';
}

export const options = {
  scenarios: {
    user_flow: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '30s', target: 15 },
        { duration: '60s', target: 15 },
        { duration: '20s', target: 0 },
      ],
      exec: 'userFlow',
      tags: { role: 'user' },
    },
    admin_flow: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '30s', target: 4 },
        { duration: '60s', target: 4 },
        { duration: '20s', target: 0 },
      ],
      exec: 'adminFlow',
      tags: { role: 'admin' },
    },
    mentor_flow: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '30s', target: 6 },
        { duration: '60s', target: 6 },
        { duration: '20s', target: 0 },
      ],
      exec: 'mentorFlow',
      tags: { role: 'mentor' },
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<1200'],
  },
};

export function setup() {
  const health = http.get(`${BASE_URL}/health`);
  check(health, {
    'health status 200': (r) => r.status === 200,
  });
  return { baseUrl: BASE_URL };
}

export function userFlow(data) {
  const token = roleToken('USER_TOKEN');

  const me = http.get(`${data.baseUrl}/api/user/v1/me`, {
    headers: jsonHeaders(token),
    tags: { endpoint: 'user_me' },
  });
  check(me, { 'user /me <=499': (r) => r.status < 500 });

  const stats = http.get(`${data.baseUrl}/api/user/v1/stats`, {
    headers: jsonHeaders(token),
    tags: { endpoint: 'user_stats' },
  });
  check(stats, { 'user /stats <=499': (r) => r.status < 500 });

  const lens = http.post(
    `${data.baseUrl}/api/lenses/v1/spider`,
    JSON.stringify({ user_id: 'k6-user', role: 'user' }),
    {
      headers: jsonHeaders(token),
      tags: { endpoint: 'user_lens_spider' },
    },
  );
  check(lens, { 'user lens <=499': (r) => r.status < 500 });

  sleep(1);
}

export function adminFlow(data) {
  const token = roleToken('ADMIN_TOKEN');

  const users = http.get(`${data.baseUrl}/api/admin/v1/users`, {
    headers: jsonHeaders(token),
    tags: { endpoint: 'admin_users' },
  });
  check(users, { 'admin /users <=499': (r) => r.status < 500 });

  const snapshot = http.get(`${data.baseUrl}/api/admin/v1/dashboard/snapshot`, {
    headers: jsonHeaders(token),
    tags: { endpoint: 'admin_dashboard' },
  });
  check(snapshot, { 'admin dashboard <=499': (r) => r.status < 500 });

  const support = http.get(`${data.baseUrl}/api/support/v1/status`, {
    headers: jsonHeaders(token),
    tags: { endpoint: 'admin_support_status' },
  });
  check(support, { 'admin support status <=499': (r) => r.status < 500 });

  sleep(1);
}

export function mentorFlow(data) {
  const token = roleToken('MENTOR_TOKEN');

  const list = http.get(`${data.baseUrl}/api/mentor/v1/list`, {
    headers: jsonHeaders(token),
    tags: { endpoint: 'mentor_list' },
  });
  check(list, { 'mentor /list <=499': (r) => r.status < 500 });

  const summary = http.get(`${data.baseUrl}/api/mentorship/v1/summary`, {
    headers: jsonHeaders(token),
    tags: { endpoint: 'mentor_summary' },
  });
  check(summary, { 'mentor summary <=499': (r) => r.status < 500 });

  sleep(1);
}
