-- Sample test data for IntelliCV-AI Admin Portal
-- This script inserts test data for development and testing purposes

-- Insert additional test admin users
INSERT INTO admin_users (username, email, password_hash, full_name, role, is_active) VALUES
    ('test_admin', 'test.admin@intellicv.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewDBxLg5RuKvOT5S', 'Test Administrator', 'admin', true),
    ('test_viewer', 'test.viewer@intellicv.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewDBxLg5RuKvOT5S', 'Test Viewer', 'viewer', true),
    ('inactive_user', 'inactive@intellicv.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewDBxLg5RuKvOT5S', 'Inactive User', 'admin', false)
ON CONFLICT (username) DO NOTHING;

-- Insert test data sources
INSERT INTO data_sources (name, type, connection_string, configuration, is_active, created_by) VALUES
    ('PostgreSQL Main', 'database', 'postgresql://user:pass@localhost:5432/maindb', '{"driver": "postgresql", "pool_size": 10}', true, (SELECT id FROM admin_users WHERE username = 'admin')),
    ('Redis Cache', 'cache', 'redis://localhost:6379/0', '{"max_connections": 20}', true, (SELECT id FROM admin_users WHERE username = 'admin')),
    ('External API', 'api', 'https://api.example.com/v1', '{"auth_type": "bearer", "timeout": 30}', true, (SELECT id FROM admin_users WHERE username = 'admin')),
    ('CSV Import', 'file', '/data/imports/', '{"file_types": ["csv", "xlsx"], "max_size": "100MB"}', true, (SELECT id FROM admin_users WHERE username = 'admin'))
ON CONFLICT DO NOTHING;

-- Insert test jobs
INSERT INTO admin_jobs (name, type, status, progress, configuration, created_by) VALUES
    ('Database Backup', 'backup', 'completed', 100, '{"backup_type": "full", "compression": true}', (SELECT id FROM admin_users WHERE username = 'admin')),
    ('Data Import Job', 'data_import', 'running', 65, '{"source": "csv", "batch_size": 1000}', (SELECT id FROM admin_users WHERE username = 'test_admin')),
    ('System Maintenance', 'maintenance', 'pending', 0, '{"tasks": ["cleanup_logs", "optimize_db"]}', (SELECT id FROM admin_users WHERE username = 'admin')),
    ('Failed Export', 'data_export', 'failed', 25, '{"format": "json", "destination": "s3"}', (SELECT id FROM admin_users WHERE username = 'test_admin'))
ON CONFLICT DO NOTHING;

-- Insert test audit logs
INSERT INTO audit_logs (user_id, action, resource_type, resource_id, old_values, new_values, ip_address) VALUES
    ((SELECT id FROM admin_users WHERE username = 'admin'), 'CREATE', 'admin_users', (SELECT id FROM admin_users WHERE username = 'test_admin')::text, NULL, '{"username": "test_admin", "role": "admin"}', '127.0.0.1'),
    ((SELECT id FROM admin_users WHERE username = 'test_admin'), 'UPDATE', 'data_sources', (SELECT id FROM data_sources WHERE name = 'PostgreSQL Main')::text, '{"is_active": false}', '{"is_active": true}', '192.168.1.100'),
    ((SELECT id FROM admin_users WHERE username = 'admin'), 'DELETE', 'admin_jobs', gen_random_uuid()::text, '{"name": "Old Backup Job"}', NULL, '127.0.0.1'),
    ((SELECT id FROM admin_users WHERE username = 'test_viewer'), 'VIEW', 'system_metrics', NULL, NULL, NULL, '192.168.1.101')
ON CONFLICT DO NOTHING;

-- Insert test system metrics
INSERT INTO system_metrics (metric_name, metric_value, metric_unit, tags, recorded_at) VALUES
    ('cpu_usage', 75.5, 'percent', '{"host": "admin-portal", "component": "app"}', NOW() - INTERVAL '1 hour'),
    ('memory_usage', 1024, 'mb', '{"host": "admin-portal", "component": "app"}', NOW() - INTERVAL '1 hour'),
    ('active_sessions', 5, 'count', '{"component": "session_manager"}', NOW() - INTERVAL '30 minutes'),
    ('database_connections', 12, 'count', '{"database": "postgresql", "pool": "main"}', NOW() - INTERVAL '15 minutes'),
    ('api_requests_per_minute', 150, 'count', '{"endpoint": "/api/admin", "method": "GET"}', NOW() - INTERVAL '5 minutes'),
    ('response_time_avg', 250, 'ms', '{"endpoint": "/api/admin", "percentile": "95"}', NOW() - INTERVAL '5 minutes'),
    ('disk_usage', 45.2, 'percent', '{"mount": "/app/data"}', NOW()),
    ('error_rate', 0.02, 'percent', '{"component": "api", "severity": "error"}', NOW())
ON CONFLICT DO NOTHING;

-- Insert test user activity
INSERT INTO user_activity (user_id, page_path, action, duration_seconds, metadata) VALUES
    ((SELECT id FROM admin_users WHERE username = 'admin'), '/admin/dashboard', 'page_view', 120, '{"browser": "Chrome", "screen_resolution": "1920x1080"}'),
    ((SELECT id FROM admin_users WHERE username = 'admin'), '/admin/users', 'page_view', 45, '{"browser": "Chrome"}'),
    ((SELECT id FROM admin_users WHERE username = 'test_admin'), '/admin/jobs', 'page_view', 180, '{"browser": "Firefox"}'),
    ((SELECT id FROM admin_users WHERE username = 'test_admin'), '/admin/data-sources', 'action_click', 5, '{"button": "refresh", "element_id": "refresh-btn"}'),
    ((SELECT id FROM admin_users WHERE username = 'test_viewer'), '/admin/reports', 'page_view', 300, '{"browser": "Safari"})
ON CONFLICT DO NOTHING;

-- Update job completion times and status
UPDATE admin_jobs 
SET 
    started_at = NOW() - INTERVAL '2 hours',
    completed_at = NOW() - INTERVAL '1 hour'
WHERE status = 'completed';

UPDATE admin_jobs 
SET started_at = NOW() - INTERVAL '30 minutes'
WHERE status = 'running';

UPDATE admin_jobs 
SET 
    started_at = NOW() - INTERVAL '1 hour',
    completed_at = NOW() - INTERVAL '45 minutes',
    error_message = 'Connection timeout to external service'
WHERE status = 'failed';

-- Create some test sessions
INSERT INTO admin_sessions (user_id, session_token, ip_address, user_agent, expires_at) VALUES
    ((SELECT id FROM admin_users WHERE username = 'admin'), 'admin_session_token_123', '127.0.0.1', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', NOW() + INTERVAL '1 hour'),
    ((SELECT id FROM admin_users WHERE username = 'test_admin'), 'test_session_token_456', '192.168.1.100', 'Mozilla/5.0 (macOS; Intel Mac OS X 10_15_7) AppleWebKit/537.36', NOW() + INTERVAL '2 hours')
ON CONFLICT DO NOTHING;

COMMIT;