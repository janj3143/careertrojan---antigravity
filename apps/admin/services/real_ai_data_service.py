"""
Real AI Data Service for IntelliCV Admin Portal
Connects to actual ai_data_final and live data sources instead of mock data
"""

import json
import os
import csv
import requests
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import subprocess
import sys
from collections import defaultdict, Counter

class RealAIDataService:
    """Service to provide real AI data from actual ai_data_final and live sources"""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent.parent
        self.ai_data_final_path = self.base_path / "ai_data_final"
        self.ai_data_path = self.base_path / "ai_data" if not self.ai_data_final_path.exists() else self.ai_data_final_path
        self.automated_parser_path = self.base_path / "automated_parser"
        self.full_system_path = self.base_path / "Full system"

        # Initialize data caches
        self.ai_profiles_cache = []
        self.companies_cache = []
        self.market_data_cache = {}
        self.competitive_data_cache = {}
        self.last_update = None
        self.last_error: Optional[str] = None

        # Load real data on initialization
        self.load_real_ai_data()

    def load_real_ai_data(self):
        """Load real AI data from ai_data_final directories"""
        try:
            self.ai_profiles_cache = self._load_ai_profiles()
            self.companies_cache = self._load_companies_data()
            self.market_data_cache = self._load_market_intelligence()
            self.competitive_data_cache = self._load_competitive_data()
            self.last_update = datetime.now()
            self.last_error = None

        except Exception as e:
            self.ai_profiles_cache = []
            self.companies_cache = []
            self.market_data_cache = {}
            self.competitive_data_cache = {}
            self.last_update = None
            self.last_error = f"Error loading real AI data: {e}"

    def _load_ai_profiles(self) -> List[Dict]:
        """Load AI profiles from JSON files in ai_data directories"""
        profiles = []

        # Check multiple directories for AI data
        search_paths = [
            self.ai_data_path / "cv_parsed",
            self.ai_data_path / "profiles_parsed",
            self.ai_data_path / "complete_parsing_output",
            self.automated_parser_path / "ai_data" / "complete_parsing_output"
        ]

        for search_path in search_paths:
            if search_path.exists():
                json_files = list(search_path.glob("*.json"))
                for json_file in json_files[:100]:  # Limit to first 100 for performance
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                data['source_file'] = str(json_file)
                                data['parsed_date'] = datetime.fromtimestamp(json_file.stat().st_mtime).isoformat()
                                profiles.append(data)
                    except Exception as e:
                        continue

        return profiles

    def _load_companies_data(self) -> List[Dict]:
        """Load companies data from real sources"""
        companies = []

        # Load from CSV files
        csv_files = [
            self.automated_parser_path / "Companies.csv",
            self.automated_parser_path / "Contacts.csv"
        ]

        for csv_file in csv_files:
            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file)
                    for _, row in df.iterrows():
                        company_data = row.to_dict()
                        company_data['source'] = csv_file.name
                        company_data['last_updated'] = datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat()
                        companies.append(company_data)
                except Exception as e:
                    continue

        # Load from JSON files in ai_data
        company_paths = [
            self.ai_data_path / "companies_parsed",
            self.ai_data_path / "leads_parsed"
        ]

        for company_path in company_paths:
            if company_path.exists():
                json_files = list(company_path.glob("*.json"))
                for json_file in json_files[:50]:  # Limit for performance
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                data['source_file'] = str(json_file)
                                companies.append(data)
                    except Exception as e:
                        continue

        return companies

    def _load_market_intelligence(self) -> Dict:
        """Load market intelligence from real data sources"""
        market_data = {
            'skills_trending': self._extract_trending_skills(),
            'job_market_trends': self._analyze_job_market_trends(),
            'salary_data': self._extract_salary_intelligence(),
            'industry_growth': self._analyze_industry_growth()
        }
        return market_data

    def _load_competitive_data(self) -> Dict:
        """Load competitive intelligence from real sources"""
        competitive_data = {
            'competitors': self._identify_real_competitors(),
            'market_positioning': self._analyze_market_position(),
            'competitive_advantages': self._extract_our_advantages(),
            'threat_analysis': self._analyze_competitive_threats()
        }
        return competitive_data

    def _extract_trending_skills(self) -> List[Dict]:
        """Extract trending skills from real profile data"""
        skills_counter = Counter()

        for profile in self.ai_profiles_cache:
            # Extract skills from various profile fields
            skills = []
            if isinstance(profile, dict):
                # Look for skills in common profile fields
                skill_fields = ['skills', 'technical_skills', 'core_competencies', 'expertise', 'technologies']
                for field in skill_fields:
                    if field in profile and profile[field]:
                        if isinstance(profile[field], list):
                            skills.extend(profile[field])
                        elif isinstance(profile[field], str):
                            # Split by common delimiters
                            skills.extend([s.strip() for s in profile[field].replace(',', '|').replace(';', '|').split('|')])

                # Extract from job titles and descriptions
                if 'current_position' in profile and profile['current_position']:
                    skills.append(profile['current_position'])
                if 'job_title' in profile and profile['job_title']:
                    skills.append(profile['job_title'])

            for skill in skills:
                if skill and len(skill.strip()) > 2:
                    skills_counter[skill.strip().title()] += 1

        # Convert to trending format
        trending_skills = []
        for skill, count in skills_counter.most_common(50):
            trending_skills.append({
                'skill': skill,
                'mentions': count,
                'growth_rate': min(100, count * 2),  # Estimated growth
                'category': self._categorize_skill(skill),
                'demand_level': 'High' if count > 10 else 'Medium' if count > 5 else 'Emerging'
            })

        return trending_skills

    def _categorize_skill(self, skill: str) -> str:
        """Categorize skill into technology areas"""
        skill_lower = skill.lower()

        if any(term in skill_lower for term in ['python', 'java', 'javascript', 'react', 'node', 'angular', 'vue']):
            return 'Programming'
        elif any(term in skill_lower for term in ['aws', 'azure', 'cloud', 'docker', 'kubernetes']):
            return 'Cloud/DevOps'
        elif any(term in skill_lower for term in ['data', 'analytics', 'sql', 'tableau', 'power bi']):
            return 'Data/Analytics'
        elif any(term in skill_lower for term in ['ai', 'ml', 'machine learning', 'deep learning']):
            return 'AI/ML'
        elif any(term in skill_lower for term in ['manager', 'lead', 'director', 'strategy']):
            return 'Leadership'
        else:
            return 'Other'

    def _analyze_job_market_trends(self) -> Dict:
        """Analyze job market trends from real data"""
        job_titles = Counter()
        industries = Counter()
        locations = Counter()

        for profile in self.ai_profiles_cache:
            if isinstance(profile, dict):
                if 'job_title' in profile and profile['job_title']:
                    job_titles[profile['job_title']] += 1
                if 'industry' in profile and profile['industry']:
                    industries[profile['industry']] += 1
                if 'location' in profile and profile['location']:
                    locations[profile['location']] += 1

        return {
            'trending_roles': [{'role': role, 'growth': count} for role, count in job_titles.most_common(20)],
            'hot_industries': [{'industry': ind, 'activity': count} for ind, count in industries.most_common(15)],
            'active_locations': [{'location': loc, 'demand': count} for loc, count in locations.most_common(20)]
        }

    def _extract_salary_intelligence(self) -> Dict:
        """Extract salary intelligence from real profile data"""
        # This would need to be enhanced with actual salary APIs or data sources
        # For now, provide structure based on real roles found
        salary_data = {
            'salary_ranges': {},
            'role_progression': {},
            'industry_comparison': {}
        }

        # Analyze roles from real data and provide realistic estimates
        job_titles = [p.get('job_title', '') for p in self.ai_profiles_cache if p.get('job_title')]

        for title in set(job_titles):
            if title:
                # Provide realistic salary estimates based on role
                salary_data['salary_ranges'][title] = self._estimate_salary_range(title)

        return salary_data

    def _estimate_salary_range(self, job_title: str) -> Dict:
        """Estimate salary range based on job title"""
        title_lower = job_title.lower()

        # Basic salary estimation logic
        if any(term in title_lower for term in ['director', 'vp', 'head of']):
            return {'min': 120000, 'max': 200000, 'currency': 'USD', 'confidence': 'estimated'}
        elif any(term in title_lower for term in ['senior', 'lead', 'principal']):
            return {'min': 80000, 'max': 140000, 'currency': 'USD', 'confidence': 'estimated'}
        elif any(term in title_lower for term in ['manager', 'supervisor']):
            return {'min': 70000, 'max': 120000, 'currency': 'USD', 'confidence': 'estimated'}
        else:
            return {'min': 50000, 'max': 90000, 'currency': 'USD', 'confidence': 'estimated'}

    def _analyze_industry_growth(self) -> Dict:
        """Analyze industry growth from real data"""
        industries = Counter()

        for profile in self.ai_profiles_cache:
            if isinstance(profile, dict) and 'industry' in profile and profile['industry']:
                industries[profile['industry']] += 1

        growth_data = {}
        for industry, count in industries.most_common(20):
            growth_data[industry] = {
                'active_professionals': count,
                'growth_rate': min(100, count * 1.5),  # Estimated
                'market_size': 'Large' if count > 20 else 'Medium' if count > 10 else 'Small'
            }

        return growth_data

    def _identify_real_competitors(self) -> List[Dict]:
        """Identify real competitors from companies data"""
        competitors = []

        # Look for companies in similar space
        for company in self.companies_cache:
            if isinstance(company, dict):
                company_name = company.get('company', company.get('Company', company.get('name', '')))
                industry = company.get('industry', company.get('Industry', ''))

                # Identify CV/HR/Recruitment related companies
                if any(term in str(company_name + ' ' + industry).lower() for term in
                       ['recruit', 'hr', 'talent', 'cv', 'resume', 'hiring', 'careers']):
                    competitors.append({
                        'name': company_name,
                        'industry': industry,
                        'source': 'real_data',
                        'threat_level': self._assess_threat_level(company_name, industry),
                        'last_seen': company.get('last_updated', datetime.now().isoformat())
                    })

        return competitors[:20]  # Limit to top 20

    def _assess_threat_level(self, company_name: str, industry: str) -> str:
        """Assess competitive threat level"""
        name_lower = str(company_name).lower()
        industry_lower = str(industry).lower()

        # High threat indicators
        if any(term in name_lower for term in ['indeed', 'linkedin', 'monster', 'glassdoor']):
            return 'High'
        elif any(term in industry_lower for term in ['technology', 'software', 'ai']):
            return 'Medium'
        else:
            return 'Low'

    def _analyze_market_position(self) -> Dict:
        """Analyze our market position vs competitors"""
        return {
            'market_share': f"{len(self.ai_profiles_cache)} profiles processed",
            'unique_features': [
                'AI-powered CV parsing',
                'Real-time data processing',
                'Comprehensive candidate analytics',
                'Industry-specific insights'
            ],
            'competitive_advantages': self._extract_our_advantages(),
            'areas_for_improvement': [
                'Market reach expansion',
                'API integrations',
                'Real-time data feeds'
            ]
        }

    def _extract_our_advantages(self) -> List[str]:
        """Extract our competitive advantages based on real capabilities"""
        advantages = []

        # Based on actual data processing capabilities
        if len(self.ai_profiles_cache) > 100:
            advantages.append(f"Large-scale data processing ({len(self.ai_profiles_cache)} profiles)")

        if len(self.companies_cache) > 50:
            advantages.append(f"Comprehensive company database ({len(self.companies_cache)} companies)")

        # Check for AI processing capabilities
        if self.ai_data_path.exists():
            advantages.append("Advanced AI data processing pipeline")

        # Check for real-time capabilities
        if (self.full_system_path / "admin_portal").exists():
            advantages.append("Real-time admin monitoring and analytics")

        return advantages

    def _analyze_competitive_threats(self) -> List[Dict]:
        """Analyze competitive threats from real market data"""
        threats = []

        # Analyze based on real competitor data
        for competitor in self._identify_real_competitors():
            if competitor['threat_level'] == 'High':
                threats.append({
                    'threat': f"Competition from {competitor['name']}",
                    'impact': 'High',
                    'probability': 'Medium',
                    'mitigation': f"Enhance unique features vs {competitor['name']}"
                })

        return threats

    def _load_csv_fallback_data(self):
        raise RuntimeError("CSV loading helper is disabled")

    def get_ai_content_data(self) -> Dict:
        """Get real AI content generation data"""
        return {
            'total_profiles': len(self.ai_profiles_cache),
            'companies_analyzed': len(self.companies_cache),
            'skills_database': len(self.market_data_cache.get('skills_trending', [])),
            'last_update': self.last_update.isoformat() if self.last_update else 'Never',
            'error': self.last_error,
            'data_sources': {
                'ai_profiles': len(self.ai_profiles_cache) > 0,
                'companies': len(self.companies_cache) > 0,
                'market_intelligence': bool(self.market_data_cache),
                'competitive_data': bool(self.competitive_data_cache)
            }
        }

    def get_market_intelligence_data(self) -> Dict:
        """Get real market intelligence data"""
        return {
            'trending_skills': self.market_data_cache.get('skills_trending', [])[:20],
            'job_trends': self.market_data_cache.get('job_market_trends', {}),
            'salary_intelligence': self.market_data_cache.get('salary_data', {}),
            'industry_analysis': self.market_data_cache.get('industry_growth', {}),
            'data_freshness': self.last_update.isoformat() if self.last_update else 'Unknown'
        }

    def get_competitive_intelligence_data(self) -> Dict:
        """Get real competitive intelligence data"""
        return {
            'identified_competitors': self.competitive_data_cache.get('competitors', []),
            'market_position': self.competitive_data_cache.get('market_positioning', {}),
            'competitive_advantages': self.competitive_data_cache.get('competitive_advantages', []),
            'threat_analysis': self.competitive_data_cache.get('threat_analysis', []),
            'analysis_date': self.last_update.isoformat() if self.last_update else 'Unknown'
        }

    def search_companies_live(self, company_name: str) -> Dict:
        """Search for company information in real data and external sources"""
        # First check local data
        local_results = []
        for company in self.companies_cache:
            if isinstance(company, dict):
                name = company.get('company', company.get('Company', company.get('name', '')))
                if company_name.lower() in str(name).lower():
                    local_results.append(company)

        # External search must be implemented via real web search integrations.
        return {
            'local_matches': local_results[:10],
            'external_data': None,
            'error': 'External company search not integrated',
            'search_timestamp': datetime.now().isoformat()
        }

    def get_real_system_status(self) -> Dict:
        """Get real system health status"""
        return {
            'ai_data_connection': self.ai_data_path.exists(),
            'profiles_loaded': len(self.ai_profiles_cache),
            'companies_loaded': len(self.companies_cache),
            'last_data_refresh': self.last_update.isoformat() if self.last_update else 'Never',
            'data_sources_active': {
                'ai_data_final': self.ai_data_final_path.exists(),
                'automated_parser': self.automated_parser_path.exists(),
                'csv_files_available': any((self.automated_parser_path / f).exists()
                                        for f in ['Candidate.csv', 'Companies.csv', 'Contacts.csv'])
            }
        }

    def refresh_data(self) -> bool:
        """Refresh all data from sources"""
        try:
            self.load_real_ai_data()
            return True
        except Exception as e:
            print(f"Data refresh failed: {e}")
            return False
