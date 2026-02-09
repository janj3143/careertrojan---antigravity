"""
Enhanced Job Title & LinkedIn Industry Integration Engine
========================================================

This module combines job title enhancement with comprehensive LinkedIn industry
classification and business software categorization for advanced AI enrichment.

Author: IntelliCV-AI Team
Date: September 30, 2025
"""

import json
import re
import sys
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging, get_logger, LoggingMixin
from utils.exception_handler import ExceptionHandler, SafeOperationsMixin

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Import the LinkedIn classifier
try:
    from services.linkedin_industry_classifier import LinkedInIndustryClassifier
    LINKEDIN_CLASSIFIER_AVAILABLE = True
except ImportError:
    LINKEDIN_CLASSIFIER_AVAILABLE = False

class EnhancedJobTitleEngine(LoggingMixin, SafeOperationsMixin):
    """Enhanced job title engine with LinkedIn industry integration"""
    
    def __init__(self):
        super().__init__()
        self.linkedin_classifier = LinkedInIndustryClassifier() if LINKEDIN_CLASSIFIER_AVAILABLE else None
        self.job_titles_db = self._load_job_titles_database()
        self.skill_mappings = self._load_skill_mappings()
        self.salary_ranges = self._load_salary_estimates()
        
    def _load_job_titles_database(self) -> Dict:
        """Load existing job titles database"""
        try:
            db_path = Path("ai_data/enhanced_job_titles_database.json")
            if db_path.exists():
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def _load_skill_mappings(self) -> Dict[str, List[str]]:
        """Load comprehensive skill mappings by job title and industry"""
        return {
            # Technology & Software
            "Software Engineer": ["Programming", "Software Development", "Problem Solving", "Testing", "Documentation", "Version Control", "Agile", "Code Review"],
            "Data Scientist": ["Python", "R", "Machine Learning", "Statistics", "Data Analysis", "SQL", "Data Visualization", "Deep Learning"],
            "DevOps Engineer": ["CI/CD", "Docker", "Kubernetes", "Cloud Platforms", "Infrastructure as Code", "Monitoring", "Automation", "Linux"],
            "Product Manager": ["Product Strategy", "Market Research", "User Experience", "Project Management", "Analytics", "Stakeholder Management", "Roadmapping"],
            "UX Designer": ["User Research", "Wireframing", "Prototyping", "Design Thinking", "Usability Testing", "Information Architecture", "Visual Design"],
            
            # Business & Management
            "Marketing Manager": ["Digital Marketing", "Content Strategy", "Campaign Management", "Analytics", "Brand Management", "Social Media", "SEO/SEM"],
            "Sales Manager": ["Sales Strategy", "Team Leadership", "CRM", "Pipeline Management", "Negotiation", "Client Relationship Management", "Revenue Growth"],
            "Project Manager": ["Project Planning", "Risk Management", "Team Leadership", "Budget Management", "Stakeholder Communication", "Agile/Scrum", "Timeline Management"],
            "Business Analyst": ["Requirements Gathering", "Process Mapping", "Data Analysis", "Stakeholder Management", "Documentation", "Business Intelligence", "SQL"],
            "Operations Manager": ["Process Optimization", "Team Management", "Budget Planning", "Quality Control", "Supply Chain", "Performance Metrics", "Strategic Planning"],
            
            # Finance & Accounting
            "Financial Analyst": ["Financial Modeling", "Excel", "Data Analysis", "Forecasting", "Budgeting", "Risk Assessment", "Financial Reporting", "Valuation"],
            "Accountant": ["Financial Reporting", "Tax Preparation", "Auditing", "Bookkeeping", "Compliance", "Financial Analysis", "ERP Systems", "GAAP"],
            "Investment Banker": ["Financial Modeling", "Valuation", "M&A", "Capital Markets", "Due Diligence", "Presentation Skills", "Client Management", "Excel"],
            "Risk Manager": ["Risk Assessment", "Compliance", "Regulatory Requirements", "Data Analysis", "Report Writing", "Risk Mitigation", "Insurance", "Auditing"],
            
            # Healthcare
            "Registered Nurse": ["Patient Care", "Medical Procedures", "Electronic Health Records", "Medication Administration", "Patient Assessment", "Healthcare Compliance", "Emergency Response"],
            "Physical Therapist": ["Patient Assessment", "Treatment Planning", "Rehabilitation Techniques", "Exercise Prescription", "Patient Education", "Medical Documentation", "Anatomy"],
            "Medical Assistant": ["Patient Care", "Medical Procedures", "Administrative Tasks", "Medical Records", "Appointment Scheduling", "Insurance Processing", "Clinical Skills"],
            "Healthcare Administrator": ["Healthcare Management", "Regulatory Compliance", "Budget Management", "Staff Management", "Healthcare Policy", "Quality Improvement", "Electronic Health Records"],
            
            # Education
            "Teacher": ["Curriculum Development", "Classroom Management", "Student Assessment", "Educational Technology", "Lesson Planning", "Parent Communication", "Differentiated Instruction"],
            "Principal": ["Educational Leadership", "Staff Management", "Budget Management", "Curriculum Oversight", "Parent Relations", "Regulatory Compliance", "Strategic Planning"],
            "Instructional Designer": ["Curriculum Development", "Learning Management Systems", "Educational Technology", "Assessment Design", "Adult Learning Theory", "E-learning", "Training Development"],
            
            # Engineering
            "Civil Engineer": ["AutoCAD", "Project Management", "Structural Analysis", "Construction Management", "Regulatory Compliance", "Site Planning", "Cost Estimation"],
            "Mechanical Engineer": ["CAD Software", "Product Design", "Manufacturing Processes", "Materials Science", "Project Management", "Quality Control", "Testing and Validation"],
            "Electrical Engineer": ["Circuit Design", "Power Systems", "Control Systems", "Programming", "Testing and Troubleshooting", "Project Management", "Regulatory Compliance"],
            
            # Legal
            "Lawyer": ["Legal Research", "Writing", "Litigation", "Client Counseling", "Negotiation", "Contract Review", "Regulatory Compliance", "Case Management"],
            "Paralegal": ["Legal Research", "Document Preparation", "Case Management", "Client Communication", "Court Filing", "Legal Software", "Administrative Support"],
            
            # Default skills for unknown titles
            "Generic": ["Communication", "Problem Solving", "Teamwork", "Time Management", "Leadership", "Analytical Thinking", "Adaptability", "Customer Service"]
        }
    
    def _load_salary_estimates(self) -> Dict[str, Dict[str, int]]:
        """Load salary estimates by job title and experience level"""
        return {
            # Technology roles (in USD thousands)
            "Software Engineer": {"entry": 75, "mid": 105, "senior": 145, "lead": 180},
            "Data Scientist": {"entry": 85, "mid": 115, "senior": 155, "lead": 190},
            "Product Manager": {"entry": 90, "mid": 125, "senior": 165, "lead": 200},
            "DevOps Engineer": {"entry": 80, "mid": 110, "senior": 150, "lead": 185},
            
            # Business roles
            "Marketing Manager": {"entry": 55, "mid": 75, "senior": 95, "lead": 125},
            "Sales Manager": {"entry": 60, "mid": 80, "senior": 110, "lead": 145},
            "Project Manager": {"entry": 65, "mid": 85, "senior": 115, "lead": 145},
            "Business Analyst": {"entry": 60, "mid": 75, "senior": 95, "lead": 120},
            
            # Finance roles
            "Financial Analyst": {"entry": 60, "mid": 75, "senior": 95, "lead": 125},
            "Accountant": {"entry": 45, "mid": 60, "senior": 75, "lead": 95},
            "Investment Banker": {"entry": 85, "mid": 125, "senior": 175, "lead": 250},
            
            # Healthcare roles
            "Registered Nurse": {"entry": 60, "mid": 75, "senior": 85, "lead": 95},
            "Physical Therapist": {"entry": 75, "mid": 85, "senior": 95, "lead": 105},
            
            # Default salary range
            "Generic": {"entry": 45, "mid": 65, "senior": 85, "lead": 110}
        }
    
    def analyze_job_title_comprehensive(self, job_title: str, experience_level: str = "mid") -> Dict:
        """Comprehensive analysis of job title with LinkedIn integration"""
        if not job_title:
            return {"error": "No job title provided"}
        
        # Normalize the job title
        normalized_title = self._normalize_title(job_title)
        
        # LinkedIn industry classification
        industry_analysis = {}
        if self.linkedin_classifier:
            industry_analysis = self.linkedin_classifier.classify_job_title(normalized_title)
        
        # Skill recommendations
        skills = self._get_skills_for_title(normalized_title)
        
        # Salary estimates
        salary_info = self._get_salary_estimates(normalized_title, experience_level)
        
        # Career progression
        career_path = self._get_career_progression(normalized_title, industry_analysis.get('primary_industry'))
        
        # Related job titles
        similar_titles = self._find_similar_titles(normalized_title)
        
        # Technology adoption for the industry
        tech_adoption = self._assess_tech_adoption(industry_analysis.get('primary_industry', ''))
        
        return {
            "original_title": job_title,
            "normalized_title": normalized_title,
            "industry_analysis": industry_analysis,
            "required_skills": skills,
            "salary_estimates": salary_info,
            "career_progression": career_path,
            "similar_titles": similar_titles,
            "technology_adoption": tech_adoption,
            "market_demand": self._assess_market_demand(normalized_title),
            "remote_work_potential": self._assess_remote_work_potential(normalized_title),
            "generated_at": datetime.now().isoformat()
        }
    
    def _normalize_title(self, title: str) -> str:
        """Enhanced title normalization"""
        if not title:
            return ""
        
        # Common typo fixes (from previous implementation)
        typo_fixes = {
            'Specilaist': 'Specialist', 'Assisitant': 'Assistant', 'Develpoment': 'Development',
            'Programer': 'Programmer', 'Qaulity': 'Quality', 'Legasl': 'Legal',
            'Vetenarian': 'Veterinarian', 'Pharceutical': 'Pharmaceutical'
        }
        
        normalized = title.strip()
        for typo, correct in typo_fixes.items():
            normalized = re.sub(r'\b' + re.escape(typo) + r'\b', correct, normalized, flags=re.IGNORECASE)
        
        # Standardize abbreviations
        abbreviations = {
            r'\bVP\b': 'Vice President', r'\bSVP\b': 'Senior Vice President',
            r'\bCEO\b': 'Chief Executive Officer', r'\bCTO\b': 'Chief Technology Officer',
            r'\bCFO\b': 'Chief Financial Officer', r'\bHR\b': 'Human Resources',
            r'\bIT\b': 'Information Technology', r'\bQA\b': 'Quality Assurance'
        }
        
        for abbrev, full_form in abbreviations.items():
            normalized = re.sub(abbrev, full_form, normalized, flags=re.IGNORECASE)
        
        # Clean formatting
        normalized = re.sub(r'\s+', ' ', normalized).strip().title()
        
        return normalized
    
    def _get_skills_for_title(self, title: str) -> List[str]:
        """Get skills for a job title with intelligent matching"""
        # Direct match
        if title in self.skill_mappings:
            return self.skill_mappings[title]
        
        # Partial matching
        title_lower = title.lower()
        for mapped_title, skills in self.skill_mappings.items():
            if any(word in title_lower for word in mapped_title.lower().split()):
                return skills
        
        # Role-based defaults
        if any(word in title_lower for word in ['manager', 'director', 'lead']):
            return ["Leadership", "Team Management", "Strategic Planning", "Budget Management", "Communication", "Decision Making", "Performance Management"]
        elif any(word in title_lower for word in ['developer', 'programmer', 'engineer']):
            return ["Programming", "Problem Solving", "Technical Documentation", "Testing", "Debugging", "Code Review", "Version Control"]
        elif any(word in title_lower for word in ['analyst', 'researcher']):
            return ["Data Analysis", "Research", "Critical Thinking", "Reporting", "Excel", "Statistical Analysis", "Presentation Skills"]
        elif any(word in title_lower for word in ['specialist', 'consultant']):
            return ["Subject Matter Expertise", "Problem Solving", "Client Communication", "Project Management", "Training", "Documentation"]
        else:
            return self.skill_mappings["Generic"]
    
    def _get_salary_estimates(self, title: str, experience_level: str) -> Dict:
        """Get salary estimates for job title and experience level"""
        # Direct match
        if title in self.salary_ranges:
            salary_data = self.salary_ranges[title]
        else:
            # Use generic ranges
            salary_data = self.salary_ranges["Generic"]
        
        base_salary = salary_data.get(experience_level, salary_data["mid"])
        
        return {
            "base_salary_usd": base_salary * 1000,  # Convert to actual USD
            "experience_level": experience_level,
            "salary_range": {
                "min": int(base_salary * 0.85 * 1000),
                "max": int(base_salary * 1.15 * 1000)
            },
            "currency": "USD",
            "note": "Estimates based on US market averages"
        }
    
    def _get_career_progression(self, title: str, industry: str) -> List[str]:
        """Get career progression path"""
        # Industry-specific progressions
        if industry and self.linkedin_classifier:
            industry_paths = self.linkedin_classifier._suggest_career_paths(industry)
            if industry_paths:
                return industry_paths
        
        # Generic progressions based on role level
        title_lower = title.lower()
        
        if 'junior' in title_lower or 'associate' in title_lower:
            return [
                f"{title} → Senior {title} → Lead {title} → Manager → Director"
            ]
        elif 'senior' in title_lower:
            return [
                f"{title} → Lead {title.replace('Senior ', '')} → Manager → Director → VP"
            ]
        elif 'manager' in title_lower:
            return [
                f"{title} → Senior Manager → Director → VP → C-Level Executive"
            ]
        else:
            return [
                f"{title} → Senior {title} → Lead {title} → Manager → Director"
            ]
    
    def _find_similar_titles(self, title: str) -> List[str]:
        """Find similar job titles"""
        if not self.job_titles_db.get('normalized_job_titles'):
            return []
        
        title_lower = title.lower()
        all_titles = self.job_titles_db.get('normalized_job_titles', [])
        
        # Extract key words from title
        title_words = set(re.findall(r'\w+', title_lower))
        
        similar_titles = []
        for candidate_title in all_titles:
            candidate_words = set(re.findall(r'\w+', candidate_title.lower()))
            
            # Calculate similarity based on common words
            common_words = title_words.intersection(candidate_words)
            if len(common_words) >= 1 and candidate_title.lower() != title_lower:
                similarity_score = len(common_words) / len(title_words.union(candidate_words))
                if similarity_score > 0.2:  # Threshold for similarity
                    similar_titles.append((candidate_title, similarity_score))
        
        # Sort by similarity and return top 5
        similar_titles.sort(key=lambda x: x[1], reverse=True)
        return [title for title, score in similar_titles[:5]]
    
    def _assess_tech_adoption(self, industry: str) -> Dict:
        """Assess technology adoption level for industry"""
        if not industry or not self.linkedin_classifier:
            return {"level": "Unknown", "description": "Unable to assess"}
        
        try:
            industry_info = self.linkedin_classifier.get_industry_insights(industry)
            tech_level = industry_info.get('technology_adoption', 'Moderate Technology Adoption')
            
            tech_descriptions = {
                "High Technology Adoption": "Industry leaders in digital transformation with extensive use of AI, automation, and modern software solutions",
                "Moderate Technology Adoption": "Balanced approach to technology with growing digital initiatives and selective automation",
                "Traditional Industry": "Focus on established processes with gradual technology integration and proven solutions"
            }
            
            return {
                "level": tech_level,
                "description": tech_descriptions.get(tech_level, "Standard technology usage patterns"),
                "related_software": industry_info.get('related_software', [])
            }
        except Exception:
            return {"level": "Unknown", "description": "Unable to assess technology adoption"}
    
    def _assess_market_demand(self, title: str) -> Dict:
        """Assess market demand for job title"""
        # High-demand roles (based on current market trends)
        high_demand_keywords = [
            'data scientist', 'software engineer', 'devops', 'cloud', 'ai', 'machine learning',
            'cybersecurity', 'product manager', 'ux designer', 'digital marketing'
        ]
        
        moderate_demand_keywords = [
            'project manager', 'business analyst', 'sales', 'marketing', 'accountant',
            'nurse', 'teacher', 'consultant'
        ]
        
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in high_demand_keywords):
            return {
                "level": "High",
                "description": "Strong market demand with competitive salaries and growth opportunities",
                "growth_outlook": "Excellent"
            }
        elif any(keyword in title_lower for keyword in moderate_demand_keywords):
            return {
                "level": "Moderate",
                "description": "Steady market demand with regular opportunities and stable career prospects",
                "growth_outlook": "Good"
            }
        else:
            return {
                "level": "Stable",
                "description": "Consistent market presence with traditional career pathways",
                "growth_outlook": "Stable"
            }
    
    def _assess_remote_work_potential(self, title: str) -> Dict:
        """Assess remote work potential for job title"""
        high_remote_keywords = [
            'software', 'developer', 'programmer', 'data scientist', 'analyst', 'writer',
            'designer', 'marketing', 'consultant', 'project manager', 'accountant'
        ]
        
        low_remote_keywords = [
            'nurse', 'doctor', 'teacher', 'mechanic', 'construction', 'retail',
            'server', 'driver', 'technician', 'operator'
        ]
        
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in high_remote_keywords):
            return {
                "potential": "High",
                "description": "Excellent potential for remote work with digital-first responsibilities",
                "percentage": "80-100%"
            }
        elif any(keyword in title_lower for keyword in low_remote_keywords):
            return {
                "potential": "Low",
                "description": "Limited remote work potential due to hands-on or location-specific requirements",
                "percentage": "0-20%"
            }
        else:
            return {
                "potential": "Moderate",
                "description": "Some remote work opportunities depending on company policies and role specifics",
                "percentage": "30-60%"
            }

def main():
    """Test the enhanced job title engine"""
    engine = EnhancedJobTitleEngine()
    
    test_titles = [
        "Software Engineer",
        "Marketing Manager",
        "Data Scientist", 
        "Registered Nurse",
        "Financial Analyst"
    ]
    
    logger.info("🚀 Enhanced Job Title Analysis Engine Test")
    logger.info("=" * 60)
    
    for title in test_titles:
        logger.info(f"\n📋 **Analyzing: {title}**")
        analysis = engine.analyze_job_title_comprehensive(title)
        
        logger.info(f"   Industry: {analysis.get('industry_analysis', {}).get('primary_industry', 'Unknown')}")
        logger.info(f"   Salary Range: ${analysis.get('salary_estimates', {}).get('salary_range', {}).get('min', 'N/A'):,} - ${analysis.get('salary_estimates', {}).get('salary_range', {}).get('max', 'N/A'):,}")
        logger.info(f"   Market Demand: {analysis.get('market_demand', {}).get('level', 'Unknown')}")
        logger.info(f"   Remote Work: {analysis.get('remote_work_potential', {}).get('potential', 'Unknown')}")
        logger.info(f"   Top Skills: {', '.join(analysis.get('required_skills', [])[:4])}")

if __name__ == "__main__":
    main()