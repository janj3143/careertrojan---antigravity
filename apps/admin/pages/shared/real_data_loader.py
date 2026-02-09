"""
=============================================================================
IntelliCV Comprehensive Data Loader - Full Access to ALL AI Data Final
=============================================================================

This module provides comprehensive access to ALL 3,418+ JSON files from the 
ai_data_final directory structure, replacing mock data with real processed data
across the entire IntelliCV ecosystem.

Complete Data Sources:
- ai_data_final/parsed_resumes/ (249 parsed resume JSON files)
- ai_data_final/normalized/ (1,536 normalized profile JSON files)  
- ai_data_final/normalized/users/ (1,535 user profile JSON files)
- ai_data_final/email_extracted/ (52 email extraction JSON files)
- ai_data_final/complete_parsing_output/ (10 parsing result JSON files)
- ai_data_final/companies/ (4 company JSON files)
- ai_data_final/locations/ (3 location JSON files)
- ai_data_final/metadata/ (8+3 metadata JSON files)
- ai_data_final/job_titles/ (1 job titles database)
- ai_data_final/titles/ (4 title analysis JSON files)
- ai_data_final/data_cloud_solutions/ (4 solution JSON files)
- ai_data_final/emails/ (1 email integration JSON)

TOTAL: 3,418+ JSON files with comprehensive real data
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RealDataLoader:
    """Comprehensive loader for ALL 3,418+ JSON files from SANDBOX ai_data_final directory"""
    
    def __init__(self):
        # Set correct SANDBOX path structure
        self.base_path = Path(__file__).parent.parent.parent.parent  # Go up to SANDBOX level
        self.ai_data_path = self.base_path / "ai_data_final"
        
        # ALL Data directories (comprehensive access)
        self.parsed_resumes_dir = self.ai_data_path / "parsed_resumes"  # 249 files
        self.normalized_dir = self.ai_data_path / "normalized"  # 1,536 files
        self.users_dir = self.normalized_dir / "users"  # 1,535 files
        self.email_extracted_dir = self.ai_data_path / "email_extracted"  # 52 files
        self.complete_parsing_dir = self.ai_data_path / "complete_parsing_output"  # 10 files
        self.companies_dir = self.ai_data_path / "companies"  # 4 files
        self.locations_dir = self.ai_data_path / "locations"  # 3 files
        self.metadata_dir = self.ai_data_path / "metadata"  # 8 files
        self.job_titles_dir = self.ai_data_path / "job_titles"  # 1 file
        self.titles_dir = self.ai_data_path / "titles"  # 4 files
        self.data_cloud_dir = self.ai_data_path / "data_cloud_solutions"  # 4 files
        self.emails_dir = self.ai_data_path / "emails"  # 1 file
        
        # Additional metadata sources
        self.email_metadata_dir = self.ai_data_path / "email_extracted" / "metadata"  # 3 files
        
        logger.info(f"Comprehensive RealDataLoader initialized with base path: {self.ai_data_path}")
        logger.info(f"Total directories mapped: 13 main directories + subdirectories")
    
    def load_parsed_resumes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load parsed resume JSON files"""
        resumes = []
        
        if not self.parsed_resumes_dir.exists():
            logger.warning(f"Parsed resumes directory not found: {self.parsed_resumes_dir}")
            return []
        
        json_files = list(self.parsed_resumes_dir.glob("*_parsed.json"))
        
        if limit:
            json_files = json_files[:limit]
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                    resume_data['_file_path'] = str(json_file)
                    resumes.append(resume_data)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(resumes)} parsed resumes")
        return resumes
    
    def load_normalized_profiles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load normalized profile JSON files (1,536 files)"""
        profiles = []
        
        if not self.normalized_dir.exists():
            logger.warning(f"Normalized directory not found: {self.normalized_dir}")
            return []
        
        json_files = list(self.normalized_dir.glob("*.json"))
        
        if limit:
            json_files = json_files[:limit]
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                    profile_data['_file_path'] = str(json_file)
                    profile_data['_data_source'] = 'normalized'
                    profiles.append(profile_data)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(profiles)} normalized profiles")
        return profiles
    
    def load_user_profiles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load user profile JSON files (1,535 files)"""
        users = []
        
        if not self.users_dir.exists():
            logger.warning(f"Users directory not found: {self.users_dir}")
            return []
        
        json_files = list(self.users_dir.glob("*.json"))
        
        if limit:
            json_files = json_files[:limit]
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                    user_data['_file_path'] = str(json_file)
                    user_data['_data_source'] = 'users'
                    users.append(user_data)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(users)} user profiles")
        return users
    
    def load_email_extractions(self) -> List[Dict[str, Any]]:
        """Load email extraction JSON files (52 files)"""
        emails = []
        
        if not self.email_extracted_dir.exists():
            logger.warning(f"Email extracted directory not found: {self.email_extracted_dir}")
            return []
        
        json_files = list(self.email_extracted_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    email_data = json.load(f)
                    email_data['_file_path'] = str(json_file)
                    email_data['_data_source'] = 'email_extracted'
                    emails.append(email_data)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(emails)} email extractions")
        return emails
    
    def load_companies_data(self) -> List[Dict[str, Any]]:
        """Load company JSON data (4 files)"""
        companies = []
        
        if not self.companies_dir.exists():
            logger.warning(f"Companies directory not found: {self.companies_dir}")
            return []
        
        json_files = list(self.companies_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    company_data = json.load(f)
                    company_data['_file_path'] = str(json_file)
                    company_data['_data_source'] = 'companies'
                    companies.append(company_data)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(companies)} company files")
        return companies
    
    def load_complete_parsing_results(self) -> List[Dict[str, Any]]:
        """Load complete parsing result JSON files (10 files)"""
        results = []
        
        if not self.complete_parsing_dir.exists():
            logger.warning(f"Complete parsing directory not found: {self.complete_parsing_dir}")
            return []
        
        json_files = list(self.complete_parsing_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                    result_data['_file_path'] = str(json_file)
                    result_data['_data_source'] = 'complete_parsing'
                    results.append(result_data)
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(results)} complete parsing results")
        return results
    
    def get_comprehensive_data_overview(self) -> Dict[str, Any]:
        """Get comprehensive overview of ALL 3,418+ JSON files"""
        overview = {
            "total_files": 0,
            "data_sources": {},
            "file_counts": {},
            "processing_status": "Loading..."
        }
        
        # Count files in each directory
        directories = [
            ("parsed_resumes", self.parsed_resumes_dir),
            ("normalized_profiles", self.normalized_dir),
            ("user_profiles", self.users_dir),
            ("email_extractions", self.email_extracted_dir),
            ("complete_parsing", self.complete_parsing_dir),
            ("companies", self.companies_dir),
            ("locations", self.locations_dir),
            ("metadata", self.metadata_dir),
            ("job_titles", self.job_titles_dir),
            ("titles", self.titles_dir),
            ("data_cloud_solutions", self.data_cloud_dir),
            ("emails", self.emails_dir)
        ]
        
        for name, directory in directories:
            if directory.exists():
                json_count = len(list(directory.glob("*.json")))
                overview["file_counts"][name] = json_count
                overview["total_files"] += json_count
                overview["data_sources"][name] = str(directory)
        
        overview["processing_status"] = "Complete"
        logger.info(f"Comprehensive overview: {overview['total_files']} total JSON files")
        return overview
    
    def load_all_data_sample(self, sample_size: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Load a sample from ALL data sources for comprehensive analysis"""
        all_data = {}
        
        # Sample from each major data source
        all_data["parsed_resumes"] = self.load_parsed_resumes(limit=sample_size)
        all_data["normalized_profiles"] = self.load_normalized_profiles(limit=sample_size)
        all_data["user_profiles"] = self.load_user_profiles(limit=sample_size)
        all_data["email_extractions"] = self.load_email_extractions()[:sample_size]
        all_data["companies"] = self.load_companies_data()
        all_data["parsing_results"] = self.load_complete_parsing_results()
        
        logger.info(f"Loaded sample data from {len(all_data)} sources")
        return all_data
    
    def get_resume_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from ALL resume and profile data"""
        # Load from multiple sources for comprehensive view
        resumes = self.load_parsed_resumes()
        normalized = self.load_normalized_profiles(limit=100)  # Sample for performance
        users = self.load_user_profiles(limit=100)  # Sample for performance
        
        # Combine all data sources
        all_profiles = resumes + normalized + users
        
        if not all_profiles:
            return {"total_profiles": 0}
        
        # Extract comprehensive statistics
        total_profiles = len(all_profiles)
        industries = {}
        skills_count = {}
        companies_mentioned = set()
        data_sources = {}
        
        for profile in all_profiles:
            # Track data source
            source = profile.get('_data_source', 'parsed_resumes')
            data_sources[source] = data_sources.get(source, 0) + 1
            
            # Industry analysis
            industry_info = profile.get('industry_analysis', {})
            primary_industry = industry_info.get('primary_industry', 'unknown')
            industries[primary_industry] = industries.get(primary_industry, 0) + 1
            
            # Skills analysis
            skills = profile.get('skills_detected', {})
            for skill_category, skill_list in skills.items():
                if isinstance(skill_list, list):
                    for skill in skill_list:
                        skills_count[skill] = skills_count.get(skill, 0) + 1
            
            # Companies mentioned
            companies = profile.get('companies', [])
            if isinstance(companies, list):
                companies_mentioned.update(companies)
        
        return {
            "total_profiles": total_profiles,
            "data_sources": data_sources,
            "industries": industries,
            "top_skills": dict(sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:20]),
            "companies_mentioned": len(companies_mentioned),
            "top_industries": dict(sorted(industries.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def get_chemical_engineering_data(self) -> Dict[str, Any]:
        """Get chemical engineering specific data across ALL data sources"""
        # Load from ALL sources for comprehensive analysis
        resumes = self.load_parsed_resumes()
        normalized = self.load_normalized_profiles(limit=200)  # Sample for performance
        users = self.load_user_profiles(limit=200)  # Sample for performance
        
        # Combine all sources
        all_profiles = resumes + normalized + users
        
        chemical_eng_profiles = []
        chemical_companies = set()
        chemical_skills = {}
        data_source_breakdown = {}
        
        for profile in all_profiles:
            source = profile.get('_data_source', 'parsed_resumes')
            
            # Check for chemical engineering indicators across all profile types
            text_sample = profile.get('text_sample', '').lower()
            companies = profile.get('companies', [])
            job_titles = profile.get('job_titles', [])
            
            # Convert to strings for analysis
            if isinstance(companies, list):
                companies_str = [str(c).lower() for c in companies]
            else:
                companies_str = []
                
            if isinstance(job_titles, list):
                job_titles_str = [str(j).lower() for j in job_titles]
            else:
                job_titles_str = []
            
            # Enhanced chemical engineering detection
            is_chemical = any([
                'chemical' in text_sample,
                'petrochemical' in text_sample,
                'refinery' in text_sample,
                'petroleum' in text_sample,
                'process engineer' in ' '.join(job_titles_str),
                'chemical engineer' in text_sample,
                'oil and gas' in text_sample,
                'polymer' in text_sample,
                'catalyst' in text_sample,
                any('chemical' in company for company in companies_str),
                any('petro' in company for company in companies_str),
                any('oil' in company for company in companies_str)
            ])
            
            if is_chemical:
                chemical_eng_profiles.append(profile)
                if isinstance(companies, list):
                    chemical_companies.update([str(c) for c in companies])
                
                # Track source breakdown
                data_source_breakdown[source] = data_source_breakdown.get(source, 0) + 1
                
                # Extract chemical engineering skills
                skills = profile.get('skills_detected', {})
                if isinstance(skills, dict):
                    for skill_category, skill_list in skills.items():
                        if isinstance(skill_list, list):
                            for skill in skill_list:
                                chemical_skills[skill] = chemical_skills.get(skill, 0) + 1
        
        return {
            "chemical_engineering_profiles": len(chemical_eng_profiles),
            "data_source_breakdown": data_source_breakdown,
            "chemical_companies": list(chemical_companies)[:20],  # Top 20
            "chemical_skills": dict(sorted(chemical_skills.items(), key=lambda x: x[1], reverse=True)[:15]),
            "sample_profiles": chemical_eng_profiles[:5],  # First 5 for display
            "total_sources_searched": len(set(p.get('_data_source', 'parsed_resumes') for p in all_profiles))
        }
    
    def create_comprehensive_dataframe(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Create a comprehensive pandas DataFrame from ALL data sources"""
        # Load from all sources
        resumes = self.load_parsed_resumes(limit)
        normalized = self.load_normalized_profiles(limit=limit//2 if limit else 200)
        users = self.load_user_profiles(limit=limit//2 if limit else 200)
        
        all_profiles = resumes + normalized + users
        
        if not all_profiles:
            return pd.DataFrame()
        
        # Extract key fields for comprehensive DataFrame
        data_rows = []
        for profile in all_profiles:
            metadata = profile.get('metadata', {})
            contact = profile.get('contact_info', {})
            industry = profile.get('industry_analysis', {})
            
            # Handle different data structures across sources
            companies = profile.get('companies', [])
            job_titles = profile.get('job_titles', [])
            skills = profile.get('skills_detected', {})
            
            row = {
                'data_source': profile.get('_data_source', 'parsed_resumes'),
                'file_name': metadata.get('file_name', '') or profile.get('_file_path', '').split('/')[-1],
                'processing_date': metadata.get('processing_date', ''),
                'text_length': metadata.get('text_length', 0),
                'emails': len(contact.get('emails', [])) if isinstance(contact.get('emails', []), list) else 0,
                'phones': len(contact.get('phones', [])) if isinstance(contact.get('phones', []), list) else 0,
                'companies_count': len(companies) if isinstance(companies, list) else 0,
                'job_titles_count': len(job_titles) if isinstance(job_titles, list) else 0,
                'primary_industry': industry.get('primary_industry', 'unknown'),
                'industry_confidence': industry.get('confidence', 0.0),
                'has_programming_skills': bool(skills.get('programming', [])) if isinstance(skills, dict) else False,
                'has_leadership_skills': bool(skills.get('soft_skills', [])) if isinstance(skills, dict) else False,
                'total_skills': sum(len(v) for v in skills.values()) if isinstance(skills, dict) and all(isinstance(v, list) for v in skills.values()) else 0,
                'file_path': profile.get('_file_path', '')
            }
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        logger.info(f"Created comprehensive DataFrame with {len(df)} records from {df['data_source'].nunique()} sources")
        return df
    
    def create_resume_dataframe(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Legacy method - calls comprehensive dataframe"""
        return self.create_comprehensive_dataframe(limit)
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Analyze data quality across ALL data sources (3,418+ files)"""
        # Get comprehensive overview
        overview = self.get_comprehensive_data_overview()
        
        # Sample from multiple sources for quality analysis
        resumes = self.load_parsed_resumes()
        normalized = self.load_normalized_profiles(limit=100)
        users = self.load_user_profiles(limit=100)
        emails = self.load_email_extractions()
        
        all_profiles = resumes + normalized + users
        
        if not all_profiles:
            return {"error": "No profile data available"}
        
        total_profiles = len(all_profiles)
        complete_contact_info = 0
        has_companies = 0
        has_job_titles = 0
        has_skills = 0
        source_quality = {}
        
        for profile in all_profiles:
            source = profile.get('_data_source', 'parsed_resumes')
            if source not in source_quality:
                source_quality[source] = {"total": 0, "quality_score": 0}
            source_quality[source]["total"] += 1
            
            quality_points = 0
            
            # Contact info quality
            contact = profile.get('contact_info', {})
            if contact.get('emails') and contact.get('phones'):
                complete_contact_info += 1
                quality_points += 1
            
            # Companies extraction
            if profile.get('companies'):
                has_companies += 1
                quality_points += 1
            
            # Job titles extraction
            if profile.get('job_titles'):
                has_job_titles += 1
                quality_points += 1
            
            # Skills detection
            if profile.get('skills_detected'):
                has_skills += 1
                quality_points += 1
            
            source_quality[source]["quality_score"] += quality_points
        
        # Calculate per-source quality scores
        for source in source_quality:
            if source_quality[source]["total"] > 0:
                source_quality[source]["quality_percentage"] = (
                    source_quality[source]["quality_score"] / (source_quality[source]["total"] * 4)
                ) * 100
        
        return {
            "total_profiles_analyzed": total_profiles,
            "total_files_available": overview["total_files"],
            "source_breakdown": overview["file_counts"],
            "complete_contact_info": complete_contact_info,
            "contact_completeness": (complete_contact_info / total_profiles) * 100,
            "companies_extracted": has_companies,
            "companies_rate": (has_companies / total_profiles) * 100,
            "job_titles_extracted": has_job_titles,
            "job_titles_rate": (has_job_titles / total_profiles) * 100,
            "skills_extracted": has_skills,
            "skills_rate": (has_skills / total_profiles) * 100,
            "overall_quality_score": ((complete_contact_info + has_companies + has_job_titles + has_skills) / (total_profiles * 4)) * 100,
            "source_quality": source_quality,
            "email_extractions": len(emails)
        }

# Global instance for easy access
real_data_loader = RealDataLoader()