IntelliCV – Page 12 Web Company Intelligence (All Endpoints) Patch
================================================================

What this provides
- Canonical shared session (admin auth) + cache helper
- Admin API client with Web Company Intelligence endpoints
- Page 12 Streamlit UI that ONLY calls backend endpoints (no demo/fallback/local scraping)

You must implement these backend routes
- GET  /admin/webintel/companies?q=&limit=
- GET  /admin/webintel/industries?q=&limit=
- POST /admin/webintel/research/company
- POST /admin/webintel/analyze/industry
- POST /admin/webintel/analyze/competitive
- POST /admin/webintel/research/bulk
- GET  /admin/webintel/integrations
- GET  /admin/webintel/reports?limit=
- POST /admin/webintel/reports/save

Env
- ADMIN_API_BASE_URL=http://localhost:8000
- ADMIN_API_TIMEOUT_S=30