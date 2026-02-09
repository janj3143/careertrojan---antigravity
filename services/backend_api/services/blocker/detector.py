"""
Application Blocker Detector Utility

Purpose: Lightweight blocker detection for resume upload integration
Can be called from resume upload pages, job matching, and career assistant

Author: IntelliCV AI System
Date: 2025-11-XX
"""

from typing import Dict, List, Any, Tuple
import re
from collections import defaultdict


class BlockerDetector:
    """
    Lightweight blocker detection utility

    Integrates with:
    - Resume upload pages
    - Job matching engine
    - Career assistant (UMarketU)
    - Interview preparation
    """

    def __init__(self):
        """Initialize blocker detection patterns"""
        self.skill_patterns = self._load_skill_patterns()
        self.experience_patterns = self._load_experience_patterns()
        self.certification_patterns = self._load_certification_patterns()
        self.education_patterns = self._load_education_patterns()

    # ========================================
    # MAIN DETECTION METHOD
    # ========================================

    def detect_blockers(
        self,
        jd_text: str,
        resume_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect all blockers between JD and resume

        Args:
            jd_text: Full job description text
            resume_data: Parsed resume data with skills, experience_years,
                certifications, education_level, has_leadership

        Returns:
            Dictionary with total_blockers, severity counts, blocker list,
            overall_impact, and addressable_count
        """
        blockers = []

        # Detect different blocker types
        skill_blockers = self._detect_skill_blockers(jd_text, resume_data.get('skills', []))
        experience_blockers = self._detect_experience_blockers(jd_text, resume_data)
        cert_blockers = self._detect_certification_blockers(jd_text, resume_data.get('certifications', []))
        edu_blockers = self._detect_education_blockers(jd_text, resume_data.get('education_level', 'bachelor'))

        # Combine all blockers
        all_blockers = skill_blockers + experience_blockers + cert_blockers + edu_blockers

        # Rank and score
        ranked_blockers = self._rank_blockers(all_blockers)

        # Calculate summary statistics
        severity_counts = self._calculate_severity_counts(ranked_blockers)

        return {
            'total_blockers': len(ranked_blockers),
            'critical_count': severity_counts['CRITICAL'],
            'major_count': severity_counts['MAJOR'],
            'moderate_count': severity_counts['MODERATE'],
            'minor_count': severity_counts['MINOR'],
            'blockers': ranked_blockers,
            'overall_impact': self._calculate_overall_impact(ranked_blockers),
            'addressable_count': sum(1 for b in ranked_blockers if b['is_addressable'])
        }

    # ========================================
    # SKILL BLOCKER DETECTION
    # ========================================

    def _detect_skill_blockers(
        self,
        jd_text: str,
        resume_skills: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect missing technical skills"""
        blockers = []
        jd_lower = jd_text.lower()
        resume_skills_lower = [s.lower() for s in resume_skills]

        for skill_category, patterns in self.skill_patterns.items():
            # Check if JD requires this skill category
            jd_requires = any(pattern in jd_lower for pattern in patterns['keywords'])

            if jd_requires:
                # Check if resume has this skill
                resume_has = any(
                    pattern in resume_skill
                    for resume_skill in resume_skills_lower
                    for pattern in patterns['keywords']
                )

                if not resume_has:
                    blockers.append({
                        'type': 'skill_gap',
                        'category': 'technical',
                        'severity': patterns['default_severity'],
                        'criticality_score': patterns['default_criticality'],
                        'requirement': f"{patterns['display_name']} experience required",
                        'gap': f"No {patterns['display_name']} skills found on resume",
                        'improvement_timeline': '3-months',
                        'improvement_difficulty': 'moderate',
                        'is_addressable': True,
                        'evidence': {
                            'required': patterns['display_name'],
                            'candidate_has': None,
                            'gap_type': 'complete_absence'
                        }
                    })

        return blockers

    def _detect_experience_blockers(
        self,
        jd_text: str,
        resume_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect years of experience gaps"""
        blockers = []

        # Extract required years from JD
        years_pattern = r'(\d+)\+?\s*years?\s+(?:of\s+)?experience'
        matches = re.findall(years_pattern, jd_text.lower())

        if matches:
            required_years = max([int(y) for y in matches])
            candidate_years = resume_data.get('experience_years', 0)

            if candidate_years < required_years:
                gap_years = required_years - candidate_years

                # Calculate severity based on gap
                if gap_years >= 3:
                    severity = 'CRITICAL'
                    criticality = 8.5
                elif gap_years >= 2:
                    severity = 'MAJOR'
                    criticality = 6.5
                else:
                    severity = 'MODERATE'
                    criticality = 4.5

                blockers.append({
                    'type': 'experience_gap',
                    'category': 'experience',
                    'severity': severity,
                    'criticality_score': criticality,
                    'requirement': f"{required_years}+ years of experience required",
                    'gap': f"Candidate has {candidate_years} years vs {required_years}+ required ({gap_years} year gap)",
                    'improvement_timeline': '1-year' if gap_years <= 2 else 'long-term',
                    'improvement_difficulty': 'hard',
                    'is_addressable': gap_years <= 2,
                    'evidence': {
                        'required': f"{required_years}+ years",
                        'candidate_has': f"{candidate_years} years",
                        'gap_size': gap_years
                    }
                })

        # Leadership experience check
        if any(keyword in jd_text.lower() for keyword in ['lead team', 'manage', 'director', 'head of']):
            has_leadership = resume_data.get('has_leadership', False)
            if not has_leadership:
                blockers.append({
                    'type': 'experience_gap',
                    'category': 'leadership',
                    'severity': 'MAJOR',
                    'criticality_score': 7.0,
                    'requirement': 'Team leadership/management experience required',
                    'gap': 'No formal leadership experience on resume',
                    'improvement_timeline': '6-months',
                    'improvement_difficulty': 'hard',
                    'is_addressable': True,
                    'evidence': {
                        'required': 'Leadership experience',
                        'candidate_has': 'None detected',
                        'gap_type': 'complete_absence'
                    }
                })

        return blockers

    def _detect_certification_blockers(
        self,
        jd_text: str,
        resume_certifications: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect missing certifications"""
        blockers = []
        jd_lower = jd_text.lower()
        resume_certs_lower = [c.lower() for c in resume_certifications]

        for cert_name, patterns in self.certification_patterns.items():
            # Check if JD requires this certification
            jd_requires = any(pattern in jd_lower for pattern in patterns['keywords'])

            if jd_requires:
                # Check if resume has this certification
                resume_has = any(
                    pattern in cert
                    for cert in resume_certs_lower
                    for pattern in patterns['keywords']
                )

                if not resume_has:
                    # Check if it's required or preferred
                    is_required = 'required' in jd_lower and any(p in jd_lower for p in patterns['keywords'])

                    blockers.append({
                        'type': 'certification_gap',
                        'category': 'education',
                        'severity': 'MAJOR' if is_required else 'MODERATE',
                        'criticality_score': 7.0 if is_required else 4.5,
                        'requirement': f"{patterns['display_name']} {'required' if is_required else 'preferred'}",
                        'gap': f"Missing {patterns['display_name']}",
                        'improvement_timeline': '3-months',
                        'improvement_difficulty': 'moderate',
                        'is_addressable': True,
                        'evidence': {
                            'required': patterns['display_name'],
                            'candidate_has': None,
                            'is_required': is_required
                        }
                    })

        return blockers

    def _detect_education_blockers(
        self,
        jd_text: str,
        candidate_education: str
    ) -> List[Dict[str, Any]]:
        """Detect education-level gaps"""
        blockers = []
        jd_lower = jd_text.lower()

        # Education hierarchy
        edu_hierarchy = {
            'phd': 4,
            'masters': 3,
            'bachelor': 2,
            'associate': 1
        }

        candidate_level = edu_hierarchy.get(candidate_education.lower(), 2)

        for edu_name, patterns in self.education_patterns.items():
            # Check if JD requires this education level
            jd_requires = any(pattern in jd_lower for pattern in patterns['keywords'])

            if jd_requires:
                required_level = patterns['level']

                if candidate_level < required_level:
                    is_required = 'required' in jd_lower

                    blockers.append({
                        'type': 'education_gap',
                        'category': 'education',
                        'severity': 'MAJOR' if is_required else 'MINOR',
                        'criticality_score': 6.0 if is_required else 3.0,
                        'requirement': f"{patterns['display_name']} {'required' if is_required else 'preferred'}",
                        'gap': f"Candidate has {candidate_education}, requires {patterns['display_name']}",
                        'improvement_timeline': 'long-term',
                        'improvement_difficulty': 'very_hard',
                        'is_addressable': required_level - candidate_level == 1,
                        'evidence': {
                            'required': patterns['display_name'],
                            'candidate_has': candidate_education,
                            'level_gap': required_level - candidate_level
                        }
                    })

        return blockers

    # ========================================
    # RANKING & SCORING
    # ========================================

    def _rank_blockers(self, blockers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank blockers by criticality and refine scores"""
        for blocker in blockers:
            # Adjust score based on addressability
            if not blocker['is_addressable']:
                blocker['criticality_score'] *= 1.2

            # Adjust based on timeline
            timeline_multipliers = {
                '1-week': 0.8,
                '1-month': 0.9,
                '3-months': 1.0,
                '6-months': 1.1,
                '1-year': 1.2,
                'long-term': 1.3
            }
            blocker['criticality_score'] *= timeline_multipliers.get(blocker['improvement_timeline'], 1.0)

            # Cap at 10.0
            blocker['criticality_score'] = min(10.0, blocker['criticality_score'])

            # Recalculate severity
            score = blocker['criticality_score']
            if score >= 8.0:
                blocker['severity'] = 'CRITICAL'
            elif score >= 6.0:
                blocker['severity'] = 'MAJOR'
            elif score >= 4.0:
                blocker['severity'] = 'MODERATE'
            else:
                blocker['severity'] = 'MINOR'

        # Sort by criticality (highest first)
        return sorted(blockers, key=lambda x: x['criticality_score'], reverse=True)

    def _calculate_severity_counts(self, blockers: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate count of each severity level"""
        counts = defaultdict(int)
        for blocker in blockers:
            counts[blocker['severity']] += 1
        return dict(counts)

    def _calculate_overall_impact(self, blockers: List[Dict[str, Any]]) -> float:
        """Calculate overall impact score (0-10)"""
        if not blockers:
            return 0.0

        # Weighted average by severity
        severity_weights = {
            'CRITICAL': 1.0,
            'MAJOR': 0.7,
            'MODERATE': 0.4,
            'MINOR': 0.2
        }

        total_impact = sum(
            blocker['criticality_score'] * severity_weights.get(blocker['severity'], 0.5)
            for blocker in blockers
        )

        return min(10.0, total_impact / len(blockers))

    # ========================================
    # PATTERN DEFINITIONS
    # ========================================

    def _load_skill_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load technical skill detection patterns"""
        return {
            'aws': {
                'keywords': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'sagemaker'],
                'display_name': 'AWS',
                'default_severity': 'MAJOR',
                'default_criticality': 7.5
            },
            'python': {
                'keywords': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
                'display_name': 'Python',
                'default_severity': 'CRITICAL',
                'default_criticality': 8.5
            },
            'machine_learning': {
                'keywords': ['machine learning', 'ml', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn'],
                'display_name': 'Machine Learning',
                'default_severity': 'CRITICAL',
                'default_criticality': 8.0
            },
            'kubernetes': {
                'keywords': ['kubernetes', 'k8s', 'docker', 'containers', 'orchestration'],
                'display_name': 'Kubernetes/Docker',
                'default_severity': 'MAJOR',
                'default_criticality': 7.0
            },
            'sql': {
                'keywords': ['sql', 'postgresql', 'mysql', 'database', 'rdbms'],
                'display_name': 'SQL/Databases',
                'default_severity': 'MAJOR',
                'default_criticality': 6.5
            },
            'nlp': {
                'keywords': ['nlp', 'natural language processing', 'bert', 'gpt', 'transformers'],
                'display_name': 'NLP',
                'default_severity': 'MAJOR',
                'default_criticality': 7.0
            },
            'react': {
                'keywords': ['react', 'react.js', 'reactjs', 'jsx', 'hooks'],
                'display_name': 'React',
                'default_severity': 'MAJOR',
                'default_criticality': 7.0
            },
            'java': {
                'keywords': ['java', 'spring', 'spring boot', 'hibernate', 'maven'],
                'display_name': 'Java',
                'default_severity': 'CRITICAL',
                'default_criticality': 8.0
            }
        }

    def _load_experience_patterns(self) -> Dict[str, Any]:
        """Load experience detection patterns"""
        return {
            'years': r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            'leadership': ['lead', 'manage', 'director', 'head of', 'vp', 'chief', 'team lead']
        }

    def _load_certification_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load certification detection patterns"""
        return {
            'aws_certified': {
                'keywords': ['aws certified', 'aws certification', 'solutions architect', 'ml specialty'],
                'display_name': 'AWS Certification'
            },
            'pmp': {
                'keywords': ['pmp', 'project management professional'],
                'display_name': 'PMP'
            },
            'cissp': {
                'keywords': ['cissp', 'certified information systems security'],
                'display_name': 'CISSP'
            },
            'scrum_master': {
                'keywords': ['scrum master', 'csm', 'certified scrummaster'],
                'display_name': 'Scrum Master'
            }
        }

    def _load_education_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load education level detection patterns"""
        return {
            'phd': {
                'keywords': ['phd', 'ph.d', 'doctorate', 'doctoral'],
                'display_name': 'PhD',
                'level': 4
            },
            'masters': {
                'keywords': ['masters', 'master\'s', 'mba', 'ms', 'm.s'],
                'display_name': "Master's degree",
                'level': 3
            },
            'bachelors': {
                'keywords': ['bachelors', 'bachelor\'s', 'bs', 'b.s', 'ba', 'b.a', 'undergraduate'],
                'display_name': "Bachelor's degree",
                'level': 2
            }
        }

    # ========================================
    # IMPROVEMENT SUGGESTIONS
    # ========================================

    def suggest_improvements(self, blocker: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest improvement strategies for a blocker

        Returns:
            List of improvement strategies with timeline, cost, difficulty
        """
        strategies = []

        if blocker['type'] == 'skill_gap':
            skill = blocker['requirement'].split(' ')[0]
            strategies = [
                {
                    'strategy': f"Complete {skill} certification course",
                    'type': 'course',
                    'timeline': '8 weeks',
                    'cost': '$299',
                    'difficulty': 'moderate',
                    'expected_improvement': 6.5,
                    'recommended': True
                },
                {
                    'strategy': f"Build 3 portfolio projects using {skill}",
                    'type': 'project',
                    'timeline': '12 weeks',
                    'cost': '$0',
                    'difficulty': 'moderate',
                    'expected_improvement': 7.0,
                    'recommended': True
                },
                {
                    'strategy': f"1-on-1 mentorship with {skill} expert",
                    'type': 'mentorship',
                    'timeline': '6 weeks',
                    'cost': '$500',
                    'difficulty': 'easy',
                    'expected_improvement': 8.0,
                    'recommended': True
                }
            ]

        elif blocker['type'] == 'certification_gap':
            cert = blocker['requirement'].split(' ')[0]
            strategies = [
                {
                    'strategy': f"Enroll in {cert} certification program",
                    'type': 'certification',
                    'timeline': '10 weeks',
                    'cost': '$300',
                    'difficulty': 'moderate',
                    'expected_improvement': 7.5,
                    'recommended': True
                }
            ]

        elif blocker['type'] == 'experience_gap':
            strategies = [
                {
                    'strategy': "Gain experience through side projects and freelance",
                    'type': 'project',
                    'timeline': '24 weeks',
                    'cost': '$0',
                    'difficulty': 'hard',
                    'expected_improvement': 5.0,
                    'recommended': True
                }
            ]

        return strategies

    # ========================================
    # OBJECTION HANDLING
    # ========================================

    def generate_objection_script(self, blocker: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate interview objection handling script

        Returns:
            {
                'opening': str,
                'acknowledgment': str,
                'mitigation': str,
                'commitment': str,
                'value_proposition': str
            }
        """
        gap = blocker['gap']
        requirement = blocker['requirement']

        return {
            'opening': "I want to be transparent about my background and share how I'm addressing this.",
            'acknowledgment': f"While the JD mentions {requirement.lower()}, {gap.lower()}. I recognize this is an area I'm actively strengthening.",
            'mitigation': f"In the past 3 months, I've enrolled in relevant coursework (60% complete), built 2 projects addressing this gap, and I'm actively working on it daily.",
            'commitment': "I'm committed to achieving full proficiency within my first 90 days on the team, with measurable checkpoints at 30, 60, and 90 days.",
            'value_proposition': "What this means for your team is you get someone with cutting-edge, recent knowledge, proven ability to learn quickly, and the hunger to grow. My concentrated experience gives me fresh perspectives."
        }


# ========================================
# USAGE EXAMPLE
# ========================================

if __name__ == "__main__":
    # Example usage in resume upload or job matching
    detector = BlockerDetector()

    jd_text = """
    Senior ML Engineer - AWS Focus

    We're seeking an experienced ML Engineer with 5+ years of Python development
    and deep expertise in AWS services (SageMaker, Lambda, EC2, S3).

    Requirements:
    - 5+ years Python experience
    - AWS Machine Learning Specialty certification preferred
    - Experience with NLP and transformer models (BERT, GPT)
    - Proven team leadership experience (3+ direct reports)
    - Master's degree in Computer Science preferred
    """

    resume_data = {
        'skills': ['Python', 'TensorFlow', 'Docker', 'Git', 'SQL'],
        'experience_years': 3,
        'certifications': [],
        'education_level': 'bachelor',
        'has_leadership': False
    }

    result = detector.detect_blockers(jd_text, resume_data)

    print(f"Total Blockers: {result['total_blockers']}")
    print(f"Critical: {result['critical_count']}, Major: {result['major_count']}")
    print(f"Overall Impact: {result['overall_impact']:.1f}/10")
    print(f"Addressable: {result['addressable_count']}/{result['total_blockers']}")

    print("\nTop 3 Blockers:")
    for i, blocker in enumerate(result['blockers'][:3], 1):
        print(f"\n{i}. [{blocker['severity']}] {blocker['requirement']}")
        print(f"   Gap: {blocker['gap']}")
        print(f"   Timeline: {blocker['improvement_timeline']}")

        # Get improvement suggestions
        improvements = detector.suggest_improvements(blocker)
        print(f"   Top Improvement: {improvements[0]['strategy']} ({improvements[0]['timeline']})")

        # Get objection script
        script = detector.generate_objection_script(blocker)
        print(f"   Interview Strategy: {script['opening'][:80]}...")
