"""
=============================================================================
IntelliCV Real AI Data Connector - Production-Ready Data Integration
=============================================================================

Replaces ALL sample/demo data with real data from ai_data_final directory.
Provides comprehensive access to parsed resumes, normalized profiles, 
companies, job titles, and metadata with intelligent caching and performance optimization.

Author: IntelliCV-AI System
Date: December 2024
Version: 2.0 (Production)
"""

import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from collections import Counter, defaultdict
import threading
import time
import logging
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealAIDataConnector:
    """
    Production-ready AI data connector that provides seamless access to real ai_data_final
    instead of sample/demo data across all admin portal pages.
    """
    
    def __init__(self, cache_size: int = 10000):
        self.base_path = Path("C:/IntelliCV-AI/IntelliCV/SANDBOX/ai_data_final")
        self.cache_size = cache_size
        self.data_cache = {}
        self.metadata_cache = {}
        self.last_refresh = None
        
        # Data directory mapping
        self.data_directories = {
            'parsed_resumes': 'parsed_resumes',
            'normalized_profiles': 'normalized_profiles',
            'user_profiles': 'user_profiles',
            'email_extractions': 'email_extractions',
            'companies': 'companies',
            'locations': 'locations',
            'metadata': 'metadata',
            'skills_database': 'skills_database',
            'job_titles': 'job_titles',
            'industries': 'industries',
            'education': 'education',
            'certifications': 'certifications',
            'experience_levels': 'experience_levels'
        }
        
        # Initialize connector
        self.initialize_connector()
    
    def initialize_connector(self):
        """Initialize the connector and build initial cache"""
        if not self.base_path.exists():
            logger.error(f"AI data path does not exist: {self.base_path}")
            return False
        
        logger.info("Initializing Real AI Data Connector...")
        
        try:
            # Build metadata for each directory
            for data_type, directory in self.data_directories.items():
                dir_path = self.base_path / directory
                if dir_path.exists():
                    self.metadata_cache[data_type] = self._build_directory_metadata(dir_path)
                else:
                    logger.warning(f"Directory not found: {dir_path}")
            
            # Cache frequently accessed data
            self._build_initial_cache()
            
            self.last_refresh = datetime.now()
            logger.info("Real AI Data Connector initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing connector: {e}")
            return False
    
    def _build_directory_metadata(self, directory: Path) -> Dict[str, Any]:
        """Build metadata for a data directory"""
        json_files = list(directory.glob("**/*.json"))
        
        metadata = {
            'total_files': len(json_files),
            'directory_path': str(directory),
            'last_updated': datetime.now(),
            'file_sizes': {},
            'sample_data': None
        }
        
        # Get file sizes and sample data
        if json_files:
            # Sample a few files for preview
            sample_files = random.sample(json_files, min(3, len(json_files)))
            
            for file in sample_files:
                try:
                    file_size = os.path.getsize(file)
                    metadata['file_sizes'][file.name] = file_size
                    
                    # Load sample data from first file
                    if metadata['sample_data'] is None:
                        with open(file, 'r', encoding='utf-8') as f:
                            metadata['sample_data'] = json.load(f)
                except Exception as e:
                    logger.warning(f"Error processing file {file}: {e}")
        
        return metadata
    
    def _build_initial_cache(self):
        """Build initial cache with most commonly accessed data"""
        try:
            # Cache resumes (limited for performance)
            self.data_cache['resumes'] = self.get_parsed_resumes(limit=1000)
            
            # Cache profiles
            self.data_cache['profiles'] = self.get_normalized_profiles(limit=1000)
            
            # Cache companies
            self.data_cache['companies'] = self.get_company_data(limit=500)
            
            # Cache job titles
            self.data_cache['job_titles'] = self.get_job_titles_data(limit=500)
            
            logger.info(f"Initial cache built with {len(self.data_cache)} categories")
            
        except Exception as e:
            logger.error(f"Error building initial cache: {e}")
    
    def get_parsed_resumes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get parsed resume data from ai_data_final"""
        if 'resumes' in self.data_cache and limit and limit <= len(self.data_cache['resumes']):
            return self.data_cache['resumes'][:limit]
        
        return self._load_data_from_directory('parsed_resumes', limit)
    
    def get_normalized_profiles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get normalized profile data from ai_data_final"""
        if 'profiles' in self.data_cache and limit and limit <= len(self.data_cache['profiles']):
            return self.data_cache['profiles'][:limit]
        
        return self._load_data_from_directory('normalized_profiles', limit)
    
    def get_company_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get company data from ai_data_final"""
        if 'companies' in self.data_cache and limit and limit <= len(self.data_cache['companies']):
            return self.data_cache['companies'][:limit]
        
        return self._load_data_from_directory('companies', limit)
    
    def get_job_titles_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get job titles data from ai_data_final"""
        if 'job_titles' in self.data_cache and limit and limit <= len(self.data_cache['job_titles']):
            return self.data_cache['job_titles'][:limit]
        
        return self._load_data_from_directory('job_titles', limit)
    
    def get_user_profiles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get user profile data from ai_data_final"""
        return self._load_data_from_directory('user_profiles', limit)
    
    def get_email_extractions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get email extraction data from ai_data_final"""
        return self._load_data_from_directory('email_extractions', limit)
    
    def get_locations_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get locations data from ai_data_final"""
        return self._load_data_from_directory('locations', limit)
    
    def get_metadata(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get metadata from ai_data_final"""
        return self._load_data_from_directory('metadata', limit)
    
    def _load_data_from_directory(self, data_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load data from a specific directory in ai_data_final"""
        if data_type not in self.data_directories:
            logger.error(f"Unknown data type: {data_type}")
            return []
        
        directory_name = self.data_directories[data_type]
        directory_path = self.base_path / directory_name
        
        if not directory_path.exists():
            logger.warning(f"Directory not found: {directory_path}")
            return []
        
        try:
            data = []
            json_files = list(directory_path.glob("**/*.json"))
            
            # Apply limit if specified
            if limit:
                json_files = json_files[:limit]
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        
                        # Add metadata
                        file_data['_source_file'] = str(json_file)
                        file_data['_data_type'] = data_type
                        file_data['_loaded_at'] = datetime.now().isoformat()
                        
                        data.append(file_data)
                        
                except Exception as e:
                    logger.warning(f"Error loading {json_file}: {e}")
                    continue
            
            logger.info(f"Loaded {len(data)} records from {data_type}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading data from {data_type}: {e}")
            return []
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary of all ai_data_final"""
        summary = {
            'total_directories': len(self.data_directories),
            'data_categories': {},
            'last_updated': self.last_refresh.isoformat() if self.last_refresh else None,
            'cache_status': len(self.data_cache),
            'total_files': 0,
            'total_size_mb': 0.0
        }
        
        for data_type, metadata in self.metadata_cache.items():
            if metadata:
                summary['data_categories'][data_type] = {
                    'file_count': metadata.get('total_files', 0),
                    'directory': metadata.get('directory_path', ''),
                    'has_sample': metadata.get('sample_data') is not None
                }
                summary['total_files'] += metadata.get('total_files', 0)
        
        return summary
    
    def get_skills_analysis(self) -> Dict[str, Any]:
        """Extract and analyze skills from parsed resumes"""
        try:
            resumes = self.get_parsed_resumes(limit=1000)
            
            skills_counter = Counter()
            skills_by_industry = defaultdict(Counter)
            skills_by_experience = defaultdict(Counter)
            
            for resume in resumes:
                # Extract skills
                skills = []
                
                # Try different skill fields
                skill_fields = ['skills', 'technical_skills', 'core_skills', 'competencies']
                for field in skill_fields:
                    if field in resume:
                        field_data = resume[field]
                        if isinstance(field_data, list):
                            skills.extend(field_data)
                        elif isinstance(field_data, str):
                            skills.append(field_data)
                
                # Count skills
                for skill in skills:
                    if skill and isinstance(skill, str):
                        clean_skill = skill.strip().lower()
                        if clean_skill:
                            skills_counter[clean_skill] += 1
                            
                            # Group by industry if available
                            industry = resume.get('industry', resume.get('current_industry', 'Unknown'))
                            skills_by_industry[industry][clean_skill] += 1
                            
                            # Group by experience level if available
                            experience = resume.get('experience_level', resume.get('years_experience', 'Unknown'))
                            skills_by_experience[str(experience)][clean_skill] += 1
            
            return {
                'total_skills': len(skills_counter),
                'top_skills': dict(skills_counter.most_common(50)),
                'skills_by_industry': dict(skills_by_industry),
                'skills_by_experience': dict(skills_by_experience),
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing skills: {e}")
            return {
                'total_skills': 0,
                'top_skills': {},
                'skills_by_industry': {},
                'skills_by_experience': {},
                'error': str(e)
            }
    
    def get_company_analysis(self) -> Dict[str, Any]:
        """Extract and analyze company data"""
        try:
            companies = self.get_company_data(limit=500)
            
            company_counter = Counter()
            industries = Counter()
            locations = Counter()
            sizes = Counter()
            
            for company in companies:
                # Company names
                company_name = company.get('company_name', company.get('name', 'Unknown'))
                if company_name:
                    company_counter[company_name] += 1
                
                # Industries
                industry = company.get('industry', company.get('sector', 'Unknown'))
                if industry:
                    industries[industry] += 1
                
                # Locations
                location = company.get('location', company.get('headquarters', 'Unknown'))
                if location:
                    locations[location] += 1
                
                # Company sizes
                size = company.get('size', company.get('employee_count', 'Unknown'))
                if size:
                    sizes[str(size)] += 1
            
            return {
                'total_companies': len(company_counter),
                'top_companies': dict(company_counter.most_common(30)),
                'top_industries': dict(industries.most_common(20)),
                'top_locations': dict(locations.most_common(20)),
                'company_sizes': dict(sizes),
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing companies: {e}")
            return {
                'total_companies': 0,
                'top_companies': {},
                'top_industries': {},
                'top_locations': {},
                'company_sizes': {},
                'error': str(e)
            }
    
    def get_job_titles_analysis(self) -> Dict[str, Any]:
        """Extract and analyze job titles"""
        try:
            # Get job titles from both dedicated folder and resumes
            job_titles_data = self.get_job_titles_data(limit=500)
            resume_data = self.get_parsed_resumes(limit=1000)
            
            job_titles = Counter()
            job_levels = Counter()
            
            # Process dedicated job titles data
            for job_data in job_titles_data:
                title = job_data.get('job_title', job_data.get('title', ''))
                if title:
                    job_titles[title.strip().lower()] += 1
                
                level = job_data.get('level', job_data.get('seniority_level', 'Unknown'))
                if level:
                    job_levels[level] += 1
            
            # Process job titles from resumes
            for resume in resume_data:
                # Current job title
                current_title = resume.get('current_job_title', resume.get('job_title', ''))
                if current_title:
                    job_titles[current_title.strip().lower()] += 1
                
                # Experience entries
                experience = resume.get('experience', resume.get('work_history', []))
                if isinstance(experience, list):
                    for exp in experience:
                        if isinstance(exp, dict):
                            exp_title = exp.get('job_title', exp.get('position', ''))
                            if exp_title:
                                job_titles[exp_title.strip().lower()] += 1
            
            return {
                'total_unique_titles': len(job_titles),
                'top_job_titles': dict(job_titles.most_common(50)),
                'job_levels': dict(job_levels),
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing job titles: {e}")
            return {
                'total_unique_titles': 0,
                'top_job_titles': {},
                'job_levels': {},
                'error': str(e)
            }
    
    def refresh_cache(self):
        """Refresh the data cache"""
        logger.info("Refreshing Real AI Data Connector cache...")
        
        self.data_cache.clear()
        self.metadata_cache.clear()
        
        self.initialize_connector()
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        report = {
            'connector_status': 'active',
            'last_refresh': self.last_refresh.isoformat() if self.last_refresh else None,
            'directories_available': len([d for d in self.data_directories.values() 
                                        if (self.base_path / d).exists()]),
            'total_directories_configured': len(self.data_directories),
            'cache_categories': len(self.data_cache),
            'data_summary': self.get_analytics_summary(),
            'quality_checks': []
        }
        
        # Quality checks
        for data_type, metadata in self.metadata_cache.items():
            if metadata and metadata.get('total_files', 0) > 0:
                report['quality_checks'].append({
                    'data_type': data_type,
                    'status': 'available',
                    'file_count': metadata.get('total_files', 0),
                    'has_sample_data': metadata.get('sample_data') is not None
                })
            else:
                report['quality_checks'].append({
                    'data_type': data_type,
                    'status': 'missing',
                    'file_count': 0,
                    'has_sample_data': False
                })
        
        return report

# Global instance
_real_ai_connector = None

def get_real_ai_connector() -> RealAIDataConnector:
    """Get or create the global real AI data connector instance"""
    global _real_ai_connector
    
    if _real_ai_connector is None:
        _real_ai_connector = RealAIDataConnector()
    
    return _real_ai_connector

def get_real_sample_data(data_type: str = 'resumes', limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get real sample data instead of demo data.
    
    Args:
        data_type: Type of data ('resumes', 'profiles', 'companies', 'job_titles')
        limit: Maximum number of records to return
        
    Returns:
        List of real data records from ai_data_final
    """
    connector = get_real_ai_connector()
    
    if data_type == 'resumes':
        return connector.get_parsed_resumes(limit=limit)
    elif data_type == 'profiles':
        return connector.get_normalized_profiles(limit=limit)
    elif data_type == 'companies':
        return connector.get_company_data(limit=limit)
    elif data_type == 'job_titles':
        return connector.get_job_titles_data(limit=limit)
    elif data_type == 'users':
        return connector.get_user_profiles(limit=limit)
    elif data_type == 'emails':
        return connector.get_email_extractions(limit=limit)
    elif data_type == 'locations':
        return connector.get_locations_data(limit=limit)
    elif data_type == 'metadata':
        return connector.get_metadata(limit=limit)
    else:
        logger.warning(f"Unknown data type: {data_type}")
        return []

def get_real_analytics_data() -> Dict[str, Any]:
    """Get comprehensive real analytics data for dashboard display"""
    connector = get_real_ai_connector()
    
    return {
        'summary': connector.get_analytics_summary(),
        'skills_analysis': connector.get_skills_analysis(),
        'company_analysis': connector.get_company_analysis(),
        'job_titles_analysis': connector.get_job_titles_analysis(),
        'quality_report': connector.get_data_quality_report()
    }

# Compatibility functions to replace demo data imports
def load_sample_resumes(limit: int = 100) -> List[Dict[str, Any]]:
    """Replace demo resume loading with real data"""
    return get_real_sample_data('resumes', limit)

def load_sample_profiles(limit: int = 100) -> List[Dict[str, Any]]:
    """Replace demo profile loading with real data"""
    return get_real_sample_data('profiles', limit)

def load_sample_companies(limit: int = 100) -> List[Dict[str, Any]]:
    """Replace demo company loading with real data"""
    return get_real_sample_data('companies', limit)

def load_sample_job_titles(limit: int = 100) -> List[Dict[str, Any]]:
    """Replace demo job titles loading with real data"""
    return get_real_sample_data('job_titles', limit)

# Demo data replacement warning
def __getattr__(name):
    """Catch any remaining demo data imports and redirect to real data"""
    if 'sample_' in name or 'demo_' in name or 'mock_' in name:
        logger.warning(f"Attempted to access demo data '{name}' - redirecting to real data")
        return lambda *args, **kwargs: get_real_sample_data('resumes', 50)
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

if __name__ == "__main__":
    # Test the connector
    connector = get_real_ai_connector()
    print(f"Connector initialized: {connector.last_refresh}")
    
    # Test data loading
    resumes = connector.get_parsed_resumes(limit=5)
    print(f"Loaded {len(resumes)} resumes")
    
    # Test analytics
    analytics = get_real_analytics_data()
    print(f"Analytics summary: {analytics['summary']['total_files']} total files")