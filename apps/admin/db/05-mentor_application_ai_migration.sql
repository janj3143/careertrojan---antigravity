-- ---------------------------------------------------------------------------
-- Mentor Application AI Upgrade Migration
-- Adds AI metadata columns, snapshot storage, and backfills existing rows
-- ---------------------------------------------------------------------------

BEGIN;

-- 1. Extend mentor_applications with AI metadata + snapshot fields
ALTER TABLE mentor_applications
    ADD COLUMN IF NOT EXISTS ai_focus_tags JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS ai_chat_history JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS application_snapshot JSONB,
    ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'user_portal';

-- 2. Normalize defaults for legacy rows
UPDATE mentor_applications
SET
    ai_focus_tags = COALESCE(ai_focus_tags, '[]'::jsonb),
    ai_chat_history = COALESCE(ai_chat_history, '[]'::jsonb)
WHERE ai_focus_tags IS NULL OR ai_chat_history IS NULL;

UPDATE mentor_applications
SET source = 'user_portal'
WHERE source IS NULL OR TRIM(source) = '';

ALTER TABLE mentor_applications
    ALTER COLUMN ai_focus_tags SET DEFAULT '[]'::jsonb,
    ALTER COLUMN ai_chat_history SET DEFAULT '[]'::jsonb,
    ALTER COLUMN source SET DEFAULT 'user_portal',
    ALTER COLUMN source SET NOT NULL;

-- 3. Backfill application_snapshot for existing applications
WITH snapshot_source AS (
    SELECT
        application_id,
        jsonb_build_object(
            'application_id', application_id::text,
            'status', status,
            'submitted_date', COALESCE(
                to_char(submitted_date AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
            ),
            'professional', jsonb_build_object(
                'full_name', full_name,
                'email', email,
                'phone', phone,
                'linkedin', linkedin_url,
                'current_role', current_role,
                'company', current_company,
                'years_experience', CASE
                    WHEN years_experience IS NULL THEN 'Not provided'
                    ELSE years_experience::text || ' years'
                END,
                'industry', CASE
                    WHEN industry IS NULL OR TRIM(industry) = '' THEN '[]'::jsonb
                    ELSE jsonb_build_array(industry)
                END,
                'professional_summary', COALESCE(specialization, ''),
                'achievements', NULL
            ),
            'expertise', jsonb_build_object(
                'technical_expertise', '[]'::jsonb,
                'leadership_expertise', '[]'::jsonb,
                'career_expertise', COALESCE(expertise_areas, '[]'::jsonb),
                'business_expertise', '[]'::jsonb,
                'target_audience', COALESCE(target_audience, '[]'::jsonb),
                'session_formats', COALESCE(session_formats, '[]'::jsonb),
                'availability', CASE
                    WHEN hours_per_week IS NULL THEN 'Not provided'
                    ELSE hours_per_week::text || ' hours/week'
                END,
                'ai_recommendations', COALESCE(ai_focus_tags, '[]'::jsonb)
            ),
            'packages', COALESCE(initial_packages, '[]'::jsonb),
            'ai_chat_history', COALESCE(ai_chat_history, '[]'::jsonb),
            'guardian_notes', '[]'::jsonb,
            'source', COALESCE(source, 'user_portal')
        ) AS snapshot_payload
    FROM mentor_applications
)
UPDATE mentor_applications m
SET application_snapshot = s.snapshot_payload
FROM snapshot_source s
WHERE m.application_id = s.application_id
  AND m.application_snapshot IS NULL;

COMMIT;
