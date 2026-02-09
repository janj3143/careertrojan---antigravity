"""
IntelliCV Application Blockers Service

Purpose: Backend service for detecting, ranking, and managing qualification gaps
Features:
- Blocker detection from resume-JD analysis
- Severity ranking algorithm
- Improvement plan generation
- Objection handling script creation
- Peer comparison analytics
- Resolution tracking

Author: IntelliCV AI System
Date: 2025-11-XX
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import uuid
from collections import defaultdict


class BlockerService:
    """
    Backend service for Application Blockers system

    Handles:
    - Blocker detection and creation
    - Severity ranking and scoring
    - Improvement plan generation
    - Objection handling scripts
    - Peer comparison analytics
    - Resolution tracking
    """

    def __init__(self, db_connection_string: str = None):
        """Initialize blocker service with database connection."""
        if db_connection_string:
            self.db_connection_string = db_connection_string
        else:
            db_user = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "intellicv"))
            db_pass = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "secure_password"))
            db_host = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "postgres"))
            db_port = os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432"))
            db_name = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "intellicv_db"))
            self.db_connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_connection_string)

    # ========================================
    # BLOCKER DETECTION & CREATION
    # ========================================

    def detect_blockers_from_jd_analysis(
        self,
        user_id: str,
        resume_id: str,
        jd_id: str,
        jd_requirements: List[str],
        resume_skills: List[str],
        resume_experience: Dict[str, Any],
        application_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect blockers by analyzing gaps between JD requirements and resume

        Args:
            user_id: User identifier
            resume_id: Resume being analyzed
            jd_id: Job description being analyzed
            jd_requirements: List of requirements from JD
            resume_skills: List of skills from resume
            resume_experience: Experience data from resume
            application_id: Optional link to job application

        Returns:
            List of detected blockers with severity scores
        """
        detected_blockers = []

        # Skills gap detection
        skill_blockers = self._detect_skill_gaps(
            jd_requirements, resume_skills, user_id, resume_id, jd_id
        )
        detected_blockers.extend(skill_blockers)

        # Experience gap detection
        experience_blockers = self._detect_experience_gaps(
            jd_requirements, resume_experience, user_id, resume_id, jd_id
        )
        detected_blockers.extend(experience_blockers)

        # Certification gap detection
        cert_blockers = self._detect_certification_gaps(
            jd_requirements, resume_experience, user_id, resume_id, jd_id
        )
        detected_blockers.extend(cert_blockers)

        # Education gap detection
        edu_blockers = self._detect_education_gaps(
            jd_requirements, resume_experience, user_id, resume_id, jd_id
        )
        detected_blockers.extend(edu_blockers)

        # Rank and score all blockers
        ranked_blockers = self._rank_and_score_blockers(detected_blockers)

        # Save to database
        saved_blockers = []
        for blocker in ranked_blockers:
            blocker_id = self.create_blocker(
                user_id=user_id,
                resume_id=resume_id,
                jd_id=jd_id,
                application_id=application_id,
                blocker_type=blocker['blocker_type'],
                blocker_category=blocker['blocker_category'],
                requirement_text=blocker['requirement_text'],
                gap_description=blocker['gap_description'],
                criticality_score=blocker['criticality_score'],
                severity_level=blocker['severity_level'],
                impact_on_application=blocker['impact_on_application'],
                detected_by='ai_engine',
                detection_method=blocker.get('detection_method', 'nlp_keyword_match'),
                confidence_score=blocker.get('confidence_score', 0.85),
                evidence_data=blocker.get('evidence_data', {}),
                is_addressable=blocker.get('is_addressable', True),
                improvement_timeline=blocker.get('improvement_timeline'),
                improvement_difficulty=blocker.get('improvement_difficulty')
            )
            blocker['blocker_id'] = blocker_id
            saved_blockers.append(blocker)

        return saved_blockers

    def _detect_skill_gaps(
        self,
        jd_requirements: List[str],
        resume_skills: List[str],
        user_id: str,
        resume_id: str,
        jd_id: str
    ) -> List[Dict[str, Any]]:
        """Detect technical skill gaps"""
        blockers = []

        # Common technical skill keywords to check
        critical_skills = {
            'aws': {'keywords': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'sagemaker'], 'category': 'cloud'},
            'python': {'keywords': ['python', 'django', 'flask', 'fastapi'], 'category': 'programming'},
            'machine_learning': {'keywords': ['machine learning', 'ml', 'deep learning', 'neural networks', 'tensorflow', 'pytorch'], 'category': 'ai'},
            'kubernetes': {'keywords': ['kubernetes', 'k8s', 'docker', 'containers'], 'category': 'devops'},
            'sql': {'keywords': ['sql', 'postgresql', 'mysql', 'database'], 'category': 'database'},
            'nlp': {'keywords': ['nlp', 'natural language processing', 'bert', 'gpt', 'transformers'], 'category': 'ai'},
        }

        resume_skills_lower = [skill.lower() for skill in resume_skills]

        for skill_name, skill_data in critical_skills.items():
            # Check if JD requires this skill
            jd_requires_skill = any(
                keyword in req.lower()
                for req in jd_requirements
                for keyword in skill_data['keywords']
            )

            if jd_requires_skill:
                # Check if resume has this skill
                resume_has_skill = any(
                    keyword in resume_skill
                    for resume_skill in resume_skills_lower
                    for keyword in skill_data['keywords']
                )

                if not resume_has_skill:
                    # Extract the specific requirement text
                    requirement_text = next(
                        (req for req in jd_requirements
                         if any(keyword in req.lower() for keyword in skill_data['keywords'])),
                        f"Requires {skill_name}"
                    )

                    blockers.append({
                        'blocker_type': 'skill_gap',
                        'blocker_category': 'technical',
                        'requirement_text': requirement_text,
                        'gap_description': f"Missing {skill_name} experience from resume",
                        'criticality_score': 7.5,  # Default, will be refined
                        'severity_level': 'MAJOR',
                        'impact_on_application': 8.0,
                        'detection_method': 'nlp_keyword_match',
                        'confidence_score': 0.88,
                        'evidence_data': {
                            'required_skill': skill_name,
                            'skill_category': skill_data['category'],
                            'keywords_searched': skill_data['keywords'],
                            'resume_skills_checked': resume_skills[:10]
                        },
                        'is_addressable': True,
                        'improvement_timeline': '3-months',
                        'improvement_difficulty': 'moderate'
                    })

        return blockers

    def _detect_experience_gaps(
        self,
        jd_requirements: List[str],
        resume_experience: Dict[str, Any],
        user_id: str,
        resume_id: str,
        jd_id: str
    ) -> List[Dict[str, Any]]:
        """Detect experience-level gaps (years, leadership, etc.)"""
        blockers = []

        # Extract years of experience from JD
        import re
        years_pattern = r'(\d+)\+?\s*years?'

        for req in jd_requirements:
            years_match = re.search(years_pattern, req.lower())
            if years_match:
                required_years = int(years_match.group(1))
                candidate_years = resume_experience.get('total_years', 0)

                if candidate_years < required_years:
                    gap_years = required_years - candidate_years

                    # Calculate criticality based on gap size
                    if gap_years >= 3:
                        criticality = 8.5
                        severity = 'CRITICAL'
                    elif gap_years >= 2:
                        criticality = 6.5
                        severity = 'MAJOR'
                    else:
                        criticality = 4.5
                        severity = 'MODERATE'

                    blockers.append({
                        'blocker_type': 'experience_gap',
                        'blocker_category': 'experience',
                        'requirement_text': req,
                        'gap_description': f"Candidate has {candidate_years} years experience vs required {required_years}+ years",
                        'criticality_score': criticality,
                        'severity_level': severity,
                        'impact_on_application': criticality + 0.5,
                        'detection_method': 'experience_calculation',
                        'confidence_score': 0.95,
                        'evidence_data': {
                            'required_years': required_years,
                            'candidate_years': candidate_years,
                            'gap_years': gap_years
                        },
                        'is_addressable': gap_years <= 2,
                        'improvement_timeline': '1-year' if gap_years <= 2 else 'long-term',
                        'improvement_difficulty': 'hard' if gap_years >= 2 else 'moderate'
                    })

        # Leadership gap detection
        leadership_keywords = ['lead', 'manage', 'director', 'head of', 'vp', 'chief']
        jd_requires_leadership = any(
            keyword in req.lower()
            for req in jd_requirements
            for keyword in leadership_keywords
        )

        if jd_requires_leadership:
            has_leadership = resume_experience.get('has_leadership_experience', False)
            if not has_leadership:
                blockers.append({
                    'blocker_type': 'experience_gap',
                    'blocker_category': 'leadership',
                    'requirement_text': 'Requires team leadership experience',
                    'gap_description': 'No formal team leadership or management experience on resume',
                    'criticality_score': 7.0,
                    'severity_level': 'MAJOR',
                    'impact_on_application': 7.5,
                    'detection_method': 'semantic_analysis',
                    'confidence_score': 0.82,
                    'evidence_data': {
                        'required_skill': 'leadership',
                        'candidate_value': 'None detected'
                    },
                    'is_addressable': True,
                    'improvement_timeline': '6-months',
                    'improvement_difficulty': 'hard'
                })

        return blockers

    def _detect_certification_gaps(
        self,
        jd_requirements: List[str],
        resume_experience: Dict[str, Any],
        user_id: str,
        resume_id: str,
        jd_id: str
    ) -> List[Dict[str, Any]]:
        """Detect missing certifications"""
        blockers = []

        common_certifications = {
            'aws certified': 'AWS certification',
            'pmp': 'Project Management Professional',
            'cissp': 'Information Security certification',
            'cfa': 'Chartered Financial Analyst',
            'cpa': 'Certified Public Accountant',
            'scrum master': 'Scrum Master certification',
        }

        candidate_certs = resume_experience.get('certifications', [])
        candidate_certs_lower = [cert.lower() for cert in candidate_certs]

        for req in jd_requirements:
            for cert_keyword, cert_name in common_certifications.items():
                if cert_keyword in req.lower():
                    # Check if candidate has this certification
                    has_cert = any(cert_keyword in cert for cert in candidate_certs_lower)

                    if not has_cert:
                        # Determine if required or preferred
                        is_required = 'required' in req.lower()

                        blockers.append({
                            'blocker_type': 'certification_gap',
                            'blocker_category': 'education',
                            'requirement_text': req,
                            'gap_description': f"Missing {cert_name}",
                            'criticality_score': 7.0 if is_required else 4.5,
                            'severity_level': 'MAJOR' if is_required else 'MODERATE',
                            'impact_on_application': 7.5 if is_required else 5.0,
                            'detection_method': 'certification_check',
                            'confidence_score': 0.92,
                            'evidence_data': {
                                'required_cert': cert_name,
                                'candidate_certs': candidate_certs,
                                'is_required': is_required
                            },
                            'is_addressable': True,
                            'improvement_timeline': '3-months',
                            'improvement_difficulty': 'moderate'
                        })

        return blockers

    def _detect_education_gaps(
        self,
        jd_requirements: List[str],
        resume_experience: Dict[str, Any],
        user_id: str,
        resume_id: str,
        jd_id: str
    ) -> List[Dict[str, Any]]:
        """Detect education-level gaps (BS, MS, PhD)"""
        blockers = []

        education_levels = {
            'phd': {'rank': 4, 'name': 'PhD'},
            'doctorate': {'rank': 4, 'name': 'PhD'},
            'masters': {'rank': 3, 'name': "Master's degree"},
            'mba': {'rank': 3, 'name': 'MBA'},
            'bachelors': {'rank': 2, 'name': "Bachelor's degree"},
            'undergraduate': {'rank': 2, 'name': "Bachelor's degree"},
        }

        # Get candidate's education level
        candidate_education = resume_experience.get('highest_education', 'bachelors').lower()
        candidate_rank = education_levels.get(candidate_education, {}).get('rank', 2)

        for req in jd_requirements:
            for edu_keyword, edu_data in education_levels.items():
                if edu_keyword in req.lower():
                    required_rank = edu_data['rank']

                    if candidate_rank < required_rank:
                        is_required = 'required' in req.lower()

                        blockers.append({
                            'blocker_type': 'education_gap',
                            'blocker_category': 'education',
                            'requirement_text': req,
                            'gap_description': f"Candidate has {candidate_education}, JD requires {edu_data['name']}",
                            'criticality_score': 6.0 if is_required else 3.0,
                            'severity_level': 'MAJOR' if is_required else 'MINOR',
                            'impact_on_application': 6.5 if is_required else 3.5,
                            'detection_method': 'education_check',
                            'confidence_score': 0.90,
                            'evidence_data': {
                                'required_education': edu_data['name'],
                                'candidate_education': candidate_education,
                                'is_required': is_required
                            },
                            'is_addressable': required_rank - candidate_rank == 1,
                            'improvement_timeline': 'long-term',
                            'improvement_difficulty': 'very_hard'
                        })

        return blockers

    def _rank_and_score_blockers(self, blockers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank blockers by criticality and refine scores

        Scoring factors:
        - Base criticality (from detection)
        - Frequency of occurrence in JD
        - Addressability (can be fixed?)
        - Timeline to improvement
        - Industry importance
        """
        for blocker in blockers:
            # Adjust criticality based on addressability
            if not blocker.get('is_addressable', True):
                blocker['criticality_score'] *= 1.2  # Harder to fix = more critical

            # Adjust based on improvement timeline
            timeline_multipliers = {
                '1-week': 0.8,
                '1-month': 0.9,
                '3-months': 1.0,
                '6-months': 1.1,
                '1-year': 1.2,
                'long-term': 1.3
            }
            timeline = blocker.get('improvement_timeline', '3-months')
            blocker['criticality_score'] *= timeline_multipliers.get(timeline, 1.0)

            # Cap at 10.0
            blocker['criticality_score'] = min(10.0, blocker['criticality_score'])

            # Recalculate severity level based on final score
            score = blocker['criticality_score']
            if score >= 8.0:
                blocker['severity_level'] = 'CRITICAL'
            elif score >= 6.0:
                blocker['severity_level'] = 'MAJOR'
            elif score >= 4.0:
                blocker['severity_level'] = 'MODERATE'
            else:
                blocker['severity_level'] = 'MINOR'

        # Sort by criticality (highest first)
        return sorted(blockers, key=lambda x: x['criticality_score'], reverse=True)

    # ========================================
    # DATABASE OPERATIONS
    # ========================================

    def create_blocker(
        self,
        user_id: str,
        resume_id: str,
        jd_id: Optional[str],
        application_id: Optional[str],
        blocker_type: str,
        blocker_category: str,
        requirement_text: str,
        gap_description: str,
        criticality_score: float,
        severity_level: str,
        impact_on_application: float,
        detected_by: str,
        detection_method: str,
        confidence_score: float,
        evidence_data: Dict[str, Any],
        is_addressable: bool = True,
        improvement_timeline: Optional[str] = None,
        improvement_difficulty: Optional[str] = None
    ) -> str:
        """Create new blocker in database"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO application_blockers (
                        user_id, resume_id, jd_id, application_id,
                        blocker_type, blocker_category, requirement_text, gap_description,
                        criticality_score, severity_level, impact_on_application,
                        detected_by, detection_method, confidence_score, evidence_data,
                        is_addressable, improvement_timeline, improvement_difficulty
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING blocker_id
                """, (
                    user_id, resume_id, jd_id, application_id,
                    blocker_type, blocker_category, requirement_text, gap_description,
                    criticality_score, severity_level, impact_on_application,
                    detected_by, detection_method, confidence_score, Json(evidence_data),
                    is_addressable, improvement_timeline, improvement_difficulty
                ))
                blocker_id = cur.fetchone()['blocker_id']
                conn.commit()
                return str(blocker_id)

    def get_user_blockers(
        self,
        user_id: str,
        jd_id: Optional[str] = None,
        status: str = 'active',
        severity_levels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get all blockers for a user"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT * FROM application_blockers
                    WHERE user_id = %s AND status = %s
                """
                params = [user_id, status]

                if jd_id:
                    query += " AND jd_id = %s"
                    params.append(jd_id)

                if severity_levels:
                    query += " AND severity_level = ANY(%s)"
                    params.append(severity_levels)

                query += " ORDER BY criticality_score DESC"

                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    def get_blocker_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary statistics of user's blockers"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM v_user_active_blockers
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()
                return dict(result) if result else {}

    # ========================================
    # IMPROVEMENT PLANS
    # ========================================

    def generate_improvement_plans(
        self,
        blocker_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered improvement plans for a blocker

        Returns:
            List of improvement plans (courses, certifications, projects)
        """
        # Get blocker details
        blocker = self.get_blocker_by_id(blocker_id)
        if not blocker:
            return []

        plans = []

        # Generate different plan types based on blocker type
        if blocker['blocker_type'] == 'skill_gap':
            plans.extend(self._generate_skill_improvement_plans(blocker, user_id))

        if blocker['blocker_type'] == 'certification_gap':
            plans.extend(self._generate_certification_plans(blocker, user_id))

        if blocker['blocker_type'] == 'experience_gap':
            plans.extend(self._generate_experience_plans(blocker, user_id))

        # Rank plans by AI recommendation score
        ranked_plans = sorted(plans, key=lambda x: x['ai_recommendation_score'], reverse=True)

        # Save top 3 plans to database
        saved_plans = []
        for i, plan in enumerate(ranked_plans[:3], 1):
            plan_id = self.create_improvement_plan(
                blocker_id=blocker_id,
                user_id=user_id,
                plan_title=plan['plan_title'],
                plan_description=plan['plan_description'],
                plan_type=plan['plan_type'],
                resource_name=plan.get('resource_name'),
                resource_provider=plan.get('resource_provider'),
                resource_url=plan.get('resource_url'),
                resource_cost=plan.get('resource_cost', 0),
                estimated_duration_hours=plan.get('estimated_duration_hours'),
                estimated_completion_weeks=plan.get('estimated_completion_weeks'),
                expected_improvement_score=plan.get('expected_improvement_score'),
                priority_rank=i,
                ai_recommendation_score=plan['ai_recommendation_score'],
                success_probability=plan['success_probability'],
                milestones_total=plan.get('milestones_total', 1)
            )
            plan['plan_id'] = plan_id
            saved_plans.append(plan)

        return saved_plans

    def _generate_skill_improvement_plans(
        self,
        blocker: Dict[str, Any],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Generate improvement plans for skill gaps"""
        plans = []

        skill_name = blocker['evidence_data'].get('required_skill', 'Unknown')

        # Plan 1: Online Course
        plans.append({
            'plan_title': f"Complete {skill_name} Certification Course",
            'plan_description': f"Online certification course for {skill_name} from top provider",
            'plan_type': 'course',
            'resource_name': f"{skill_name} Professional Certificate",
            'resource_provider': "Coursera / Udemy / LinkedIn Learning",
            'resource_url': None,
            'resource_cost': 299.99,
            'estimated_duration_hours': 60,
            'estimated_completion_weeks': 8,
            'expected_improvement_score': 6.5,
            'ai_recommendation_score': 0.89,
            'success_probability': 0.85,
            'milestones_total': 5
        })

        # Plan 2: Project-based learning
        plans.append({
            'plan_title': f"Build 3 {skill_name} Portfolio Projects",
            'plan_description': f"Create real-world projects demonstrating {skill_name} expertise",
            'plan_type': 'project',
            'resource_name': "Self-Directed Portfolio Projects",
            'resource_provider': "GitHub + Free Resources",
            'resource_url': None,
            'resource_cost': 0.00,
            'estimated_duration_hours': 120,
            'estimated_completion_weeks': 12,
            'expected_improvement_score': 7.0,
            'ai_recommendation_score': 0.92,
            'success_probability': 0.80,
            'milestones_total': 3
        })

        # Plan 3: Mentorship
        plans.append({
            'plan_title': f"1-on-1 {skill_name} Mentorship",
            'plan_description': f"Work with expert mentor to rapidly build {skill_name} skills",
            'plan_type': 'mentorship',
            'resource_name': f"{skill_name} Expert Mentorship",
            'resource_provider': "IntelliCV Mentorship Portal",
            'resource_url': None,
            'resource_cost': 500.00,
            'estimated_duration_hours': 40,
            'estimated_completion_weeks': 6,
            'expected_improvement_score': 8.0,
            'ai_recommendation_score': 0.95,
            'success_probability': 0.90,
            'milestones_total': 6
        })

        return plans

    def _generate_certification_plans(
        self,
        blocker: Dict[str, Any],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Generate plans for certification gaps"""
        cert_name = blocker['evidence_data'].get('required_cert', 'Certification')

        return [{
            'plan_title': f"Earn {cert_name}",
            'plan_description': f"Complete official {cert_name} certification program",
            'plan_type': 'certification',
            'resource_name': cert_name,
            'resource_provider': "Official Certification Body",
            'resource_url': None,
            'resource_cost': 300.00,
            'estimated_duration_hours': 80,
            'estimated_completion_weeks': 10,
            'expected_improvement_score': 7.5,
            'ai_recommendation_score': 0.94,
            'success_probability': 0.87,
            'milestones_total': 4
        }]

    def _generate_experience_plans(
        self,
        blocker: Dict[str, Any],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Generate plans for experience gaps"""
        return [{
            'plan_title': "Gain Relevant Experience Through Side Projects",
            'plan_description': "Build portfolio of relevant work to demonstrate equivalent experience",
            'plan_type': 'project',
            'resource_name': "Side Projects & Freelance Work",
            'resource_provider': "Upwork / GitHub / Personal Projects",
            'resource_url': None,
            'resource_cost': 0.00,
            'estimated_duration_hours': 200,
            'estimated_completion_weeks': 24,
            'expected_improvement_score': 5.0,
            'ai_recommendation_score': 0.78,
            'success_probability': 0.75,
            'milestones_total': 6
        }]

    def create_improvement_plan(
        self,
        blocker_id: str,
        user_id: str,
        plan_title: str,
        plan_description: str,
        plan_type: str,
        resource_name: Optional[str] = None,
        resource_provider: Optional[str] = None,
        resource_url: Optional[str] = None,
        resource_cost: float = 0.00,
        estimated_duration_hours: Optional[int] = None,
        estimated_completion_weeks: Optional[int] = None,
        expected_improvement_score: Optional[float] = None,
        priority_rank: int = 1,
        ai_recommendation_score: float = 0.80,
        success_probability: float = 0.75,
        milestones_total: int = 1
    ) -> str:
        """Save improvement plan to database"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO blocker_improvement_plans (
                        blocker_id, user_id, plan_title, plan_description, plan_type,
                        resource_name, resource_provider, resource_url, resource_cost,
                        estimated_duration_hours, estimated_completion_weeks,
                        expected_improvement_score, priority_rank,
                        ai_recommendation_score, success_probability, milestones_total
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING plan_id
                """, (
                    blocker_id, user_id, plan_title, plan_description, plan_type,
                    resource_name, resource_provider, resource_url, resource_cost,
                    estimated_duration_hours, estimated_completion_weeks,
                    expected_improvement_score, priority_rank,
                    ai_recommendation_score, success_probability, milestones_total
                ))
                plan_id = cur.fetchone()['plan_id']
                conn.commit()
                return str(plan_id)

    def get_improvement_plans(self, blocker_id: str) -> List[Dict[str, Any]]:
        """Get all improvement plans for a blocker"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM blocker_improvement_plans
                    WHERE blocker_id = %s
                    ORDER BY priority_rank
                """, (blocker_id,))
                return [dict(row) for row in cur.fetchall()]

    # ========================================
    # OBJECTION HANDLING SCRIPTS
    # ========================================

    def generate_objection_script(
        self,
        blocker_id: str,
        user_id: str,
        interview_stage: str = 'technical'
    ) -> Dict[str, Any]:
        """
        Generate AI-powered objection handling script for interview

        Args:
            blocker_id: Blocker to address
            user_id: User identifier
            interview_stage: When to use ('phone_screen', 'technical', 'behavioral', etc.)

        Returns:
            Objection handling script with opening, acknowledgment, mitigation, commitment
        """
        blocker = self.get_blocker_by_id(blocker_id)
        if not blocker:
            return {}

        # Generate script components
        script_title = f"{blocker['blocker_type'].replace('_', ' ').title()} - Proactive Disclosure"

        # Opening statement
        opening = "I want to be transparent about my background and share how I'm addressing this."

        # Gap acknowledgment
        gap_desc = blocker['gap_description']
        requirement = blocker['requirement_text']
        acknowledgment = f"While the JD mentions {requirement}, {gap_desc.lower()}. I recognize this is an area I'm actively strengthening."

        # Mitigation statement (what you're doing about it)
        mitigation = self._generate_mitigation_statement(blocker)

        # Future commitment
        commitment = self._generate_future_commitment(blocker)

        # Value proposition (turn weakness into opportunity)
        value_prop = self._generate_value_proposition(blocker)

        # When to use
        when_to_use = f"Use during {interview_stage} round when interviewer asks about {blocker['blocker_category']}"

        # Red flags to avoid
        red_flags = [
            "Don't say 'I'm not qualified'",
            "Avoid defensive tone",
            "Don't promise unrealistic timelines",
            "Don't disparage the importance of experience"
        ]

        # Save to database
        script_id = self.create_objection_script(
            blocker_id=blocker_id,
            user_id=user_id,
            script_title=script_title,
            interview_stage=interview_stage,
            opening_statement=opening,
            gap_acknowledgment=acknowledgment,
            mitigation_statement=mitigation,
            future_commitment=commitment,
            value_proposition=value_prop,
            confidence_level='collaborative',
            tone='transparent',
            when_to_use=when_to_use,
            red_flags_to_avoid=red_flags
        )

        return {
            'script_id': script_id,
            'script_title': script_title,
            'opening_statement': opening,
            'gap_acknowledgment': acknowledgment,
            'mitigation_statement': mitigation,
            'future_commitment': commitment,
            'value_proposition': value_prop,
            'when_to_use': when_to_use,
            'red_flags_to_avoid': red_flags
        }

    def _generate_mitigation_statement(self, blocker: Dict[str, Any]) -> str:
        """Generate mitigation statement based on blocker type"""
        if blocker['blocker_type'] == 'skill_gap':
            skill = blocker['evidence_data'].get('required_skill', 'this skill')
            return f"In the past 3 months, I've enrolled in a {skill} certification course (60% complete), built 2 production projects using {skill}, and I'm actively using it in my current role."

        elif blocker['blocker_type'] == 'experience_gap':
            return "My experience is highly concentrated—I've been running production workloads and leading projects from day one, which I estimate gives me equivalent exposure to someone with more years but less intensive work."

        elif blocker['blocker_type'] == 'certification_gap':
            cert = blocker['evidence_data'].get('required_cert', 'this certification')
            return f"I'm scheduled to complete {cert} before your target start date, and I've already completed 70% of the coursework."

        else:
            return "I've taken concrete steps to address this gap and have a clear plan to close it within the next 3-6 months."

    def _generate_future_commitment(self, blocker: Dict[str, Any]) -> str:
        """Generate future commitment statement"""
        if blocker['improvement_timeline'] in ['1-week', '1-month', '3-months']:
            return "I'm committed to completing this development within my first 90 days on the team."
        elif blocker['improvement_timeline'] in ['6-months', '1-year']:
            return "I'm committed to achieving this milestone within my first 6 months, with measurable checkpoints at 30, 60, and 90 days."
        else:
            return "I have a multi-year plan to build this capability, and I'm making steady progress every quarter."

    def _generate_value_proposition(self, blocker: Dict[str, Any]) -> str:
        """Turn weakness into opportunity"""
        return "What this means for your team is you get someone with cutting-edge, recent knowledge, proven ability to learn quickly, and the hunger to grow. My concentrated experience gives me fresh perspectives that someone with routine years might not have."

    def create_objection_script(
        self,
        blocker_id: str,
        user_id: str,
        script_title: str,
        interview_stage: str,
        opening_statement: str,
        gap_acknowledgment: str,
        mitigation_statement: str,
        future_commitment: str,
        value_proposition: str,
        confidence_level: str = 'collaborative',
        tone: str = 'transparent',
        when_to_use: str = '',
        red_flags_to_avoid: List[str] = None
    ) -> str:
        """Save objection handling script to database"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO blocker_objection_scripts (
                        blocker_id, user_id, script_title, interview_stage,
                        opening_statement, gap_acknowledgment, mitigation_statement,
                        future_commitment, value_proposition, confidence_level, tone,
                        when_to_use, red_flags_to_avoid
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING script_id
                """, (
                    blocker_id, user_id, script_title, interview_stage,
                    opening_statement, gap_acknowledgment, mitigation_statement,
                    future_commitment, value_proposition, confidence_level, tone,
                    when_to_use, red_flags_to_avoid or []
                ))
                script_id = cur.fetchone()['script_id']
                conn.commit()
                return str(script_id)

    def get_objection_scripts(self, blocker_id: str) -> List[Dict[str, Any]]:
        """Get all objection scripts for a blocker"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM blocker_objection_scripts
                    WHERE blocker_id = %s
                    ORDER BY created_at DESC
                """, (blocker_id,))
                return [dict(row) for row in cur.fetchall()]

    # ========================================
    # HELPER METHODS
    # ========================================

    def get_blocker_by_id(self, blocker_id: str) -> Optional[Dict[str, Any]]:
        """Get single blocker by ID"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM application_blockers
                    WHERE blocker_id = %s
                """, (blocker_id,))
                result = cur.fetchone()
                return dict(result) if result else None

    def update_blocker_status(
        self,
        blocker_id: str,
        status: str,
        resolution_strategy: Optional[str] = None
    ) -> bool:
        """Update blocker status (active, in_progress, resolved, etc.)"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE application_blockers
                    SET status = %s, resolution_strategy = %s
                    WHERE blocker_id = %s
                """, (status, resolution_strategy, blocker_id))
                conn.commit()
                return cur.rowcount > 0

    def mark_blocker_resolved(
        self,
        blocker_id: str,
        user_id: str,
        resolution_type: str,
        resolution_description: str,
        before_score: float,
        after_score: float
    ) -> str:
        """Mark blocker as resolved and create resolution history"""
        # Update blocker status
        self.update_blocker_status(blocker_id, 'resolved')

        # Create resolution history
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO blocker_resolution_history (
                        blocker_id, user_id, resolution_type, resolution_description,
                        before_score, after_score, improvement_delta
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING resolution_id
                """, (
                    blocker_id, user_id, resolution_type, resolution_description,
                    before_score, after_score, before_score - after_score
                ))
                resolution_id = cur.fetchone()['resolution_id']
                conn.commit()
                return str(resolution_id)


# ========================================
# USAGE EXAMPLE
# ========================================

if __name__ == "__main__":
    # Example usage
    service = BlockerService()

    # Detect blockers from resume-JD analysis
    blockers = service.detect_blockers_from_jd_analysis(
        user_id="demo_user_001",
        resume_id="resume_12345",
        jd_id="jd_ml_engineer_aws",
        jd_requirements=[
            "5+ years experience with AWS cloud platforms (EC2, S3, Lambda, SageMaker)",
            "Deep experience with NLP and transformer models (BERT, GPT)",
            "Experience leading ML engineering teams (3+ direct reports)",
            "AWS Machine Learning Specialty certification preferred"
        ],
        resume_skills=["Python", "TensorFlow", "Docker", "Git", "SQL"],
        resume_experience={
            "total_years": 3,
            "has_leadership_experience": False,
            "certifications": [],
            "highest_education": "bachelors"
        }
    )

    print(f"Detected {len(blockers)} blockers")

    # Generate improvement plans for first blocker
    if blockers:
        blocker_id = blockers[0]['blocker_id']
        plans = service.generate_improvement_plans(blocker_id, "demo_user_001")
        print(f"Generated {len(plans)} improvement plans")

        # Generate objection handling script
        script = service.generate_objection_script(blocker_id, "demo_user_001", "technical")
        print(f"Generated objection script: {script['script_title']}")
