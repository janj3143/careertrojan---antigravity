-- ========================================
-- IntelliCV Application Blockers Schema
-- ========================================
-- Purpose: Track qualification gaps opposite to touch points
-- Features: Gap detection, severity ranking, improvement tracking, objection handling
-- Author: IntelliCV AI System
-- Date: 2025-11-XX
-- ========================================

-- ========================================
-- TABLE 1: Application Blockers
-- ========================================
-- Stores detected gaps/weaknesses for each job application

CREATE TABLE IF NOT EXISTS application_blockers (
    blocker_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    resume_id VARCHAR(255) NOT NULL,
    jd_id VARCHAR(255),  -- Optional: can detect blockers against general career goals
    application_id VARCHAR(255),  -- Link to job applications table

    -- Blocker details
    blocker_type VARCHAR(100) NOT NULL,  -- 'skill_gap', 'experience_gap', 'education_gap', 'certification_gap', 'location_mismatch', 'salary_mismatch', 'culture_fit', 'soft_skill_gap'
    blocker_category VARCHAR(100) NOT NULL,  -- 'technical', 'leadership', 'education', 'experience', 'cultural', 'logistical'
    requirement_text TEXT NOT NULL,  -- The actual JD requirement causing the blocker
    gap_description TEXT NOT NULL,  -- What exactly is missing

    -- Severity scoring
    criticality_score NUMERIC(3, 1) NOT NULL CHECK (criticality_score >= 0 AND criticality_score <= 10),  -- 0-10 scale
    severity_level VARCHAR(20) NOT NULL CHECK (severity_level IN ('CRITICAL', 'MAJOR', 'MODERATE', 'MINOR')),
    impact_on_application NUMERIC(3, 1) NOT NULL,  -- 0-10 how much this hurts application

    -- Detection metadata
    detected_by VARCHAR(50) NOT NULL,  -- 'ai_engine', 'ats_analysis', 'peer_comparison', 'mentor_feedback'
    detection_method VARCHAR(100),  -- 'nlp_keyword_match', 'semantic_analysis', 'experience_calculation', 'certification_check'
    confidence_score NUMERIC(3, 2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),  -- 0-1 confidence in detection

    -- Evidence
    evidence_data JSONB,  -- {
                          --   "required_value": "5+ years Python",
                          --   "candidate_value": "2 years Python",
                          --   "gap_size": "3 years",
                          --   "similar_candidates": ["avg 4.8 years Python"]
                          -- }

    -- Improvement tracking
    is_addressable BOOLEAN DEFAULT TRUE,  -- Can this be fixed?
    improvement_timeline VARCHAR(50),  -- '1-week', '1-month', '3-months', '6-months', '1-year', 'long-term'
    improvement_difficulty VARCHAR(20) CHECK (improvement_difficulty IN ('easy', 'moderate', 'hard', 'very_hard')),

    -- Status tracking
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'in_progress', 'resolved', 'accepted', 'mitigated', 'dismissed')),
    resolution_strategy VARCHAR(100),  -- 'course_completion', 'project_experience', 'certification', 'objection_handling', 'not_required'

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT fk_blocker_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_blockers_user ON application_blockers(user_id);
CREATE INDEX idx_blockers_resume ON application_blockers(resume_id);
CREATE INDEX idx_blockers_jd ON application_blockers(jd_id);
CREATE INDEX idx_blockers_severity ON application_blockers(severity_level);
CREATE INDEX idx_blockers_status ON application_blockers(status);
CREATE INDEX idx_blockers_type ON application_blockers(blocker_type);
CREATE INDEX idx_blockers_created ON application_blockers(created_at DESC);


-- ========================================
-- TABLE 2: Blocker Improvement Plans
-- ========================================
-- AI-generated improvement strategies for each blocker

CREATE TABLE IF NOT EXISTS blocker_improvement_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,

    -- Plan details
    plan_title VARCHAR(255) NOT NULL,
    plan_description TEXT NOT NULL,
    plan_type VARCHAR(100) NOT NULL,  -- 'course', 'certification', 'project', 'mentorship', 'networking', 'volunteer', 'side_hustle'

    -- Resources
    resource_name VARCHAR(255),  -- "AWS Solutions Architect Course"
    resource_provider VARCHAR(255),  -- "Coursera", "Udemy", "LinkedIn Learning"
    resource_url TEXT,
    resource_cost NUMERIC(10, 2),  -- Cost in user's currency
    currency_code VARCHAR(3) DEFAULT 'USD',

    -- Timeline
    estimated_duration_hours INTEGER,
    estimated_completion_weeks INTEGER,
    start_date DATE,
    target_completion_date DATE,

    -- Progress tracking
    progress_percentage NUMERIC(5, 2) DEFAULT 0.00 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    milestones_completed INTEGER DEFAULT 0,
    milestones_total INTEGER,

    -- Impact
    expected_improvement_score NUMERIC(3, 1),  -- How much this will reduce criticality
    priority_rank INTEGER,  -- 1 = highest priority

    -- AI recommendations
    ai_recommendation_score NUMERIC(3, 2) CHECK (ai_recommendation_score >= 0 AND ai_recommendation_score <= 1),
    success_probability NUMERIC(3, 2) CHECK (success_probability >= 0 AND success_probability <= 1),

    -- Status
    plan_status VARCHAR(50) DEFAULT 'recommended' CHECK (plan_status IN ('recommended', 'accepted', 'in_progress', 'completed', 'abandoned', 'on_hold')),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT fk_plan_blocker FOREIGN KEY (blocker_id) REFERENCES application_blockers(blocker_id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_improvement_plans_blocker ON blocker_improvement_plans(blocker_id);
CREATE INDEX idx_improvement_plans_user ON blocker_improvement_plans(user_id);
CREATE INDEX idx_improvement_plans_status ON blocker_improvement_plans(plan_status);
CREATE INDEX idx_improvement_plans_priority ON blocker_improvement_plans(priority_rank);


-- ========================================
-- TABLE 3: Objection Handling Scripts
-- ========================================
-- AI-generated scripts for proactively addressing blockers in interviews

CREATE TABLE IF NOT EXISTS blocker_objection_scripts (
    script_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,

    -- Script details
    script_title VARCHAR(255) NOT NULL,
    interview_stage VARCHAR(100),  -- 'phone_screen', 'technical', 'behavioral', 'final_round', 'salary_negotiation'

    -- Script content
    opening_statement TEXT NOT NULL,  -- "I recognize I'm building my expertise in Python..."
    gap_acknowledgment TEXT NOT NULL,  -- "While my experience is 2 years rather than the preferred 5..."
    mitigation_statement TEXT NOT NULL,  -- "...I've completed 3 production ML projects in the last year..."
    future_commitment TEXT NOT NULL,  -- "...and I'm enrolled in advanced Python certification completing next month"
    value_proposition TEXT NOT NULL,  -- "This means I bring recent, cutting-edge knowledge plus hunger to grow"

    -- Alternative framings
    confidence_level VARCHAR(20) CHECK (confidence_level IN ('assertive', 'collaborative', 'humble', 'strategic')),
    tone VARCHAR(50),  -- 'proactive', 'defensive', 'transparent', 'solution_oriented'

    -- Context
    when_to_use TEXT,  -- "Use when interviewer asks about years of experience"
    red_flags_to_avoid TEXT[],  -- ["Don't apologize excessively", "Don't say 'I know I'm not qualified'"]

    -- Effectiveness tracking
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    effectiveness_score NUMERIC(3, 2) DEFAULT 0.00,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT fk_script_blocker FOREIGN KEY (blocker_id) REFERENCES application_blockers(blocker_id) ON DELETE CASCADE,
    CONSTRAINT fk_script_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_objection_scripts_blocker ON blocker_objection_scripts(blocker_id);
CREATE INDEX idx_objection_scripts_user ON blocker_objection_scripts(user_id);
CREATE INDEX idx_objection_scripts_stage ON blocker_objection_scripts(interview_stage);


-- ========================================
-- TABLE 4: Blocker Peer Comparisons
-- ========================================
-- Compare candidate's blockers against successful peers

CREATE TABLE IF NOT EXISTS blocker_peer_comparisons (
    comparison_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,

    -- Peer analysis
    peer_pool_size INTEGER NOT NULL,  -- How many similar candidates analyzed
    peer_selection_criteria JSONB,  -- {"job_title": "ML Engineer", "industry": "tech", "years_exp": "3-5"}

    -- Comparison metrics
    candidate_score NUMERIC(3, 1) NOT NULL,  -- Candidate's score on this dimension (0-10)
    peer_avg_score NUMERIC(3, 1) NOT NULL,  -- Average peer score
    peer_median_score NUMERIC(3, 1) NOT NULL,
    peer_top_10_score NUMERIC(3, 1) NOT NULL,  -- Top 10% of peers

    percentile_rank NUMERIC(5, 2),  -- Where candidate falls (0-100%)

    -- Gap analysis
    gap_size NUMERIC(3, 1),  -- How far behind peer average
    gap_severity VARCHAR(20) CHECK (gap_severity IN ('EXTREME', 'SIGNIFICANT', 'MODERATE', 'MINIMAL', 'AHEAD')),

    -- Success insights
    successful_despite_gap BOOLEAN,  -- Did peers succeed without this skill?
    success_rate_with_gap NUMERIC(5, 2),  -- % of peers with similar gap who got hired

    -- Compensation strategies
    compensation_factors JSONB,  -- ["Strong leadership", "Recent project experience"]

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT fk_peer_comp_blocker FOREIGN KEY (blocker_id) REFERENCES application_blockers(blocker_id) ON DELETE CASCADE,
    CONSTRAINT fk_peer_comp_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_peer_comp_blocker ON blocker_peer_comparisons(blocker_id);
CREATE INDEX idx_peer_comp_user ON blocker_peer_comparisons(user_id);
CREATE INDEX idx_peer_comp_severity ON blocker_peer_comparisons(gap_severity);


-- ========================================
-- TABLE 5: Blocker Resolution History
-- ========================================
-- Track how users addressed and resolved blockers over time

CREATE TABLE IF NOT EXISTS blocker_resolution_history (
    resolution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,

    -- Resolution details
    resolution_type VARCHAR(100) NOT NULL,  -- 'skill_acquired', 'experience_gained', 'certification_earned', 'project_completed', 'objection_handled', 'deemed_irrelevant'
    resolution_description TEXT NOT NULL,

    -- Verification
    verification_method VARCHAR(100),  -- 'resume_updated', 'linkedin_verified', 'certificate_uploaded', 'mentor_confirmed'
    verification_url TEXT,
    verification_date DATE,

    -- Impact
    before_score NUMERIC(3, 1),  -- Criticality before resolution
    after_score NUMERIC(3, 1),  -- Criticality after resolution
    improvement_delta NUMERIC(3, 1),  -- How much it improved

    -- Time to resolution
    time_to_resolve_days INTEGER,

    -- Application outcomes
    applications_before_resolution INTEGER,
    applications_after_resolution INTEGER,
    interview_rate_before NUMERIC(5, 2),
    interview_rate_after NUMERIC(5, 2),

    -- Notes
    user_notes TEXT,
    mentor_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT fk_resolution_blocker FOREIGN KEY (blocker_id) REFERENCES application_blockers(blocker_id) ON DELETE CASCADE,
    CONSTRAINT fk_resolution_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_resolution_history_blocker ON blocker_resolution_history(blocker_id);
CREATE INDEX idx_resolution_history_user ON blocker_resolution_history(user_id);
CREATE INDEX idx_resolution_history_date ON blocker_resolution_history(resolved_at DESC);


-- ========================================
-- TRIGGER: Update timestamps automatically
-- ========================================

CREATE OR REPLACE FUNCTION update_blocker_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_blockers_update
    BEFORE UPDATE ON application_blockers
    FOR EACH ROW
    EXECUTE FUNCTION update_blocker_timestamp();

CREATE TRIGGER trg_improvement_plans_update
    BEFORE UPDATE ON blocker_improvement_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_blocker_timestamp();

CREATE TRIGGER trg_objection_scripts_update
    BEFORE UPDATE ON blocker_objection_scripts
    FOR EACH ROW
    EXECUTE FUNCTION update_blocker_timestamp();

CREATE TRIGGER trg_peer_comparisons_update
    BEFORE UPDATE ON blocker_peer_comparisons
    FOR EACH ROW
    EXECUTE FUNCTION update_blocker_timestamp();


-- ========================================
-- VIEWS: Analytics & Reporting
-- ========================================

-- View 1: Active blockers summary by user
CREATE OR REPLACE VIEW v_user_active_blockers AS
SELECT
    user_id,
    COUNT(*) AS total_blockers,
    COUNT(*) FILTER (WHERE severity_level = 'CRITICAL') AS critical_blockers,
    COUNT(*) FILTER (WHERE severity_level = 'MAJOR') AS major_blockers,
    COUNT(*) FILTER (WHERE severity_level = 'MODERATE') AS moderate_blockers,
    COUNT(*) FILTER (WHERE severity_level = 'MINOR') AS minor_blockers,
    AVG(criticality_score) AS avg_criticality,
    COUNT(*) FILTER (WHERE is_addressable = TRUE) AS addressable_count,
    COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress_count,
    COUNT(*) FILTER (WHERE status = 'resolved') AS resolved_count
FROM application_blockers
WHERE status = 'active'
GROUP BY user_id;

-- View 2: Blocker resolution effectiveness
CREATE OR REPLACE VIEW v_blocker_resolution_effectiveness AS
SELECT
    b.blocker_type,
    b.blocker_category,
    COUNT(DISTINCT rh.resolution_id) AS total_resolutions,
    AVG(rh.time_to_resolve_days) AS avg_resolution_days,
    AVG(rh.improvement_delta) AS avg_improvement,
    AVG(rh.interview_rate_after - rh.interview_rate_before) AS avg_interview_rate_improvement
FROM application_blockers b
JOIN blocker_resolution_history rh ON b.blocker_id = rh.blocker_id
GROUP BY b.blocker_type, b.blocker_category;

-- View 3: Most common blockers by job type
CREATE OR REPLACE VIEW v_common_blockers_by_job AS
SELECT
    b.jd_id,
    b.blocker_type,
    b.gap_description,
    COUNT(*) AS occurrence_count,
    AVG(b.criticality_score) AS avg_criticality,
    COUNT(*) FILTER (WHERE b.status = 'resolved') AS resolved_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE b.status = 'resolved') / COUNT(*), 2) AS resolution_rate
FROM application_blockers b
WHERE b.jd_id IS NOT NULL
GROUP BY b.jd_id, b.blocker_type, b.gap_description
HAVING COUNT(*) >= 3
ORDER BY occurrence_count DESC;


-- ========================================
-- SAMPLE DATA: Mock Blockers for Testing
-- ========================================

-- Insert sample blockers for testing (user_id 'demo_user_001')
INSERT INTO application_blockers (
    user_id, resume_id, jd_id, blocker_type, blocker_category,
    requirement_text, gap_description, criticality_score, severity_level,
    impact_on_application, detected_by, detection_method, confidence_score,
    evidence_data, is_addressable, improvement_timeline, improvement_difficulty
) VALUES
(
    'demo_user_001', 'resume_12345', 'jd_ml_engineer_aws',
    'skill_gap', 'technical',
    'Requires 5+ years experience with AWS cloud platforms (EC2, S3, Lambda, SageMaker)',
    'Candidate has only 1 year AWS experience, primarily with S3 and EC2. No SageMaker or advanced ML deployment experience.',
    8.5, 'CRITICAL', 9.0,
    'ai_engine', 'nlp_keyword_match', 0.92,
    '{"required_value": "5+ years AWS", "candidate_value": "1 year AWS (S3, EC2)", "gap_size": "4 years", "missing_services": ["Lambda", "SageMaker"], "similar_candidates": "avg 4.2 years AWS experience"}',
    TRUE, '3-months', 'moderate'
),
(
    'demo_user_001', 'resume_12345', 'jd_ml_engineer_aws',
    'certification_gap', 'education',
    'Preferred: AWS Machine Learning Specialty certification',
    'No AWS certifications on file',
    5.0, 'MODERATE', 6.0,
    'ats_analysis', 'certification_check', 0.95,
    '{"required_cert": "AWS ML Specialty", "candidate_certs": [], "peer_with_cert_rate": 0.67}',
    TRUE, '6-weeks', 'moderate'
),
(
    'demo_user_001', 'resume_12345', 'jd_ml_engineer_aws',
    'experience_gap', 'leadership',
    'Experience leading ML engineering teams (3+ direct reports)',
    'Candidate has led 2 interns but no formal team leadership experience',
    6.5, 'MAJOR', 7.0,
    'ai_engine', 'semantic_analysis', 0.88,
    '{"required_value": "3+ direct reports", "candidate_value": "2 interns (non-direct reports)", "gap_size": "No formal leadership", "industry_avg": "4.5 direct reports"}',
    TRUE, '1-year', 'hard'
),
(
    'demo_user_001', 'resume_12345', 'jd_ml_engineer_aws',
    'skill_gap', 'technical',
    'Deep experience with NLP and transformer models (BERT, GPT, T5)',
    'Resume shows computer vision focus, limited NLP experience (basic sentiment analysis only)',
    4.5, 'MODERATE', 5.5,
    'ai_engine', 'nlp_keyword_match', 0.85,
    '{"required_skills": ["BERT", "GPT", "T5", "transformers"], "candidate_skills": ["sentiment analysis", "text classification"], "domain_gap": "Computer vision specialist, not NLP"}',
    TRUE, '3-months', 'moderate'
);

-- Insert improvement plans for the AWS skill gap blocker
INSERT INTO blocker_improvement_plans (
    blocker_id, user_id, plan_title, plan_description, plan_type,
    resource_name, resource_provider, resource_url, resource_cost, currency_code,
    estimated_duration_hours, estimated_completion_weeks,
    expected_improvement_score, priority_rank, ai_recommendation_score, success_probability,
    plan_status, milestones_total
) VALUES
(
    (SELECT blocker_id FROM application_blockers WHERE gap_description LIKE '%1 year AWS%' LIMIT 1),
    'demo_user_001',
    'AWS Machine Learning Specialty Certification - Fast Track',
    'Complete AWS ML Specialty certification within 6 weeks with hands-on SageMaker projects. Includes 3 capstone projects deploying ML models to production.',
    'certification',
    'AWS Certified Machine Learning - Specialty',
    'AWS Training Portal + Udemy',
    'https://aws.amazon.com/certification/certified-machine-learning-specialty/',
    299.99, 'USD',
    80, 6,
    7.5, 1, 0.94, 0.87,
    'recommended', 5
),
(
    (SELECT blocker_id FROM application_blockers WHERE gap_description LIKE '%1 year AWS%' LIMIT 1),
    'demo_user_001',
    'Build 3 Production ML Deployment Projects',
    'Create portfolio projects demonstrating Lambda, SageMaker, and full ML pipeline deployment on AWS. Each project adds 6-12 months equivalent experience.',
    'project',
    'Self-Directed Portfolio Projects',
    'GitHub + AWS Free Tier',
    NULL,
    0.00, 'USD',
    120, 8,
    6.0, 2, 0.89, 0.82,
    'recommended', 3
);

-- Insert objection handling script for AWS experience gap
INSERT INTO blocker_objection_scripts (
    blocker_id, user_id, script_title, interview_stage,
    opening_statement, gap_acknowledgment, mitigation_statement,
    future_commitment, value_proposition, confidence_level, tone,
    when_to_use, red_flags_to_avoid
) VALUES
(
    (SELECT blocker_id FROM application_blockers WHERE gap_description LIKE '%1 year AWS%' LIMIT 1),
    'demo_user_001',
    'AWS Experience Gap - Proactive Disclosure Strategy',
    'technical',

    'I want to be transparent about my AWS experience level and share how I''m addressing it.',

    'While the JD mentions 5+ years of AWS experience and I currently have 1 year of hands-on production work with S3 and EC2, I recognize this is an area I''m actively strengthening.',

    'In the past 3 months, I''ve: (1) Enrolled in the AWS ML Specialty certification track, completing 60% with target completion in 4 weeks, (2) Built 2 SageMaker projects deploying transformer models to production, and (3) Architected a serverless ML pipeline using Lambda and Step Functions that''s now processing 10M requests/month.',

    'I''m scheduled to complete AWS ML Specialty certification before your target start date, and I''m committed to AWS Solutions Architect certification within my first 6 months on the team.',

    'What this means for your team is you get someone with cutting-edge, recent AWS knowledge, strong ML fundamentals, and proven ability to learn complex cloud platforms quickly. My year of focused AWS work is highly concentrated—I estimate it''s equivalent to 2-3 years of typical exposure because I''ve been running production workloads from day one.',

    'collaborative', 'transparent',

    'Use during technical round when AWS experience is discussed, or proactively at end of intro if AWS is critical requirement',

    ARRAY['Don''t say "I''m not qualified"', 'Avoid defensive tone', 'Don''t promise unrealistic timelines', 'Don''t disparage importance of experience']
);

-- ========================================
-- COMMENTS
-- ========================================

COMMENT ON TABLE application_blockers IS 'Stores qualification gaps and weaknesses identified during resume-JD analysis. Opposite of touch points.';
COMMENT ON TABLE blocker_improvement_plans IS 'AI-generated improvement strategies to address each blocker with courses, certifications, projects';
COMMENT ON TABLE blocker_objection_scripts IS 'Interview scripts for proactively addressing blockers before employer raises them';
COMMENT ON TABLE blocker_peer_comparisons IS 'Compares candidate blockers against successful peers to contextualize gaps';
COMMENT ON TABLE blocker_resolution_history IS 'Tracks how users successfully resolved blockers over time';

COMMENT ON COLUMN application_blockers.criticality_score IS '0-10 scale: How much this blocker hurts the application. 8-10=CRITICAL, 6-7=MAJOR, 4-5=MODERATE, 0-3=MINOR';
COMMENT ON COLUMN application_blockers.evidence_data IS 'JSON evidence: required_value, candidate_value, gap_size, peer_comparison';
COMMENT ON COLUMN blocker_improvement_plans.ai_recommendation_score IS '0-1 confidence that this plan will successfully address the blocker';
COMMENT ON COLUMN blocker_objection_scripts.opening_statement IS 'How to introduce the gap proactively in interview';
COMMENT ON COLUMN blocker_peer_comparisons.successful_despite_gap IS 'Did peer candidates get hired despite having this same gap?';

-- ========================================
-- SCHEMA COMPLETE
-- ========================================
-- Total tables: 5
-- Total indexes: 21
-- Total views: 3
-- Sample data: 4 blockers + 2 improvement plans + 1 objection script
-- ========================================
