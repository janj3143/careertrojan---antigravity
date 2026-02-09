"""
AI Data Loader Utility
======================
Loads and processes real CV/resume data from ai_data_final directories
and integrates with the unified AI engine for intelligent data processing.

This utility replaces hardcoded sample data throughout the platform with
real data extracted from actual CV files and AI analysis.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global flag to prevent repeated initialization warnings
_AI_ENGINE_CHECKED = False
_AI_DATA_PATHS_CACHED = None

class RealAIConnector:
    """
    Comprehensive data loader that connects real CV data with AI engine analysis.
    Replaces all hardcoded data throughout the platform.
    """

    def __init__(self):
        self.ai_data_paths = self._find_ai_data_directories()
        self.ai_engine = self._initialize_ai_engine()
        self.cached_data = {}

    def _find_ai_data_directories(self) -> List[Path]:
        """Find all ai_data_final directories in the project."""
        global _AI_DATA_PATHS_CACHED

        # Return cached paths if already found
        if _AI_DATA_PATHS_CACHED is not None:
            return _AI_DATA_PATHS_CACHED

        # Use SharedIOLayer for centralized path access
        try:
            from shared.io_layer import get_io_layer
            io = get_io_layer()
            ai_data_path = io.paths['ai_data']
            if ai_data_path.exists():
                found_paths = [ai_data_path]
                logger.info(f"Using SharedIOLayer - AI data path: {ai_data_path}")
            else:
                found_paths = []
                logger.warning(f"SharedIOLayer path does not exist: {ai_data_path}")
        except ImportError:
            # Fallback to searching for paths if SharedIOLayer not available
            logger.warning("SharedIOLayer not available, searching for ai_data paths")
            potential_paths = [
                Path("ai_data_final"),
                Path("../ai_data_final"),
            ]

            found_paths = []
            for path in potential_paths:
                if path.exists():
                    found_paths.append(path)
                    logger.info(f"Found AI data directory: {path}")

        # Cache the result
        _AI_DATA_PATHS_CACHED = found_paths
        return found_paths

    def _initialize_ai_engine(self):
        """Initialize the unified AI engine if available."""
        global _AI_ENGINE_CHECKED

        # Only log warning once
        if not _AI_ENGINE_CHECKED:
            _AI_ENGINE_CHECKED = True
            try:
                from unified_ai_engine import UnifiedAIEngine
                return UnifiedAIEngine()
            except ImportError:
                logger.warning("Unified AI Engine not available - using fallback processing")
                return None
        else:
            # Silent check on subsequent calls
            try:
                from unified_ai_engine import UnifiedAIEngine
                return UnifiedAIEngine()
            except ImportError:
                return None

    def load_real_job_titles(self, limit: int = 50) -> List[str]:
        """Load real job titles from CV data and AI analysis."""
        if 'job_titles' in self.cached_data:
            return self.cached_data['job_titles'][:limit]

        job_titles = []

        # Extract from file names and content
        for data_path in self.ai_data_paths:
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.lower().endswith(('.pdf', '.doc', '.docx', '.txt', '.json')):
                        file_path = Path(root) / file

                        # Extract job titles from filename
                        filename_titles = self._extract_titles_from_filename(file.lower())
                        job_titles.extend(filename_titles)

                        # Extract from JSON files if they contain job data
                        if file.lower().endswith('.json'):
                            json_titles = self._extract_titles_from_json(file_path)
                            job_titles.extend(json_titles)

        # Use AI engine to enhance and validate job titles
        if self.ai_engine:
            job_titles = self._enhance_titles_with_ai(job_titles)

        # Remove duplicates and filter invalid entries
        unique_titles = list(set([title for title in job_titles if len(title.split()) <= 5 and len(title) > 3]))

        # Cache the results
        self.cached_data['job_titles'] = unique_titles
        logger.info(f"Loaded {len(unique_titles)} real job titles from AI data")

        return unique_titles[:limit]

    def _extract_titles_from_filename(self, filename: str) -> List[str]:
        """Extract job titles from filename patterns."""
        titles = []

        # Remove common file extensions and clean filename
        clean_name = filename.replace('.pdf', '').replace('.doc', '').replace('.docx', '').replace('.txt', '').replace('.json', '')
        clean_name = clean_name.replace('_', ' ').replace('-', ' ')

        # Job title patterns
        patterns = [
            r'(data\s+scientist)', r'(machine\s+learning\s+engineer)', r'(software\s+engineer)',
            r'(product\s+manager)', r'(business\s+analyst)', r'(data\s+analyst)',
            r'(full\s+stack\s+developer)', r'(frontend\s+developer)', r'(backend\s+developer)',
            r'(devops\s+engineer)', r'(cloud\s+architect)', r'(security\s+engineer)',
            r'(senior\s+\w+\s+\w+)', r'(lead\s+\w+\s+\w+)', r'(principal\s+\w+\s+\w+)',
            r'(director\s+of\s+\w+)', r'(vp\s+of\s+\w+)', r'(head\s+of\s+\w+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, clean_name, re.IGNORECASE)
            for match in matches:
                title = match.strip().title()
                if title not in titles:
                    titles.append(title)

        return titles

    def _extract_titles_from_json(self, file_path: Path) -> List[str]:
        """Extract job titles from JSON files containing job data."""
        titles = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Look for job title fields in various formats
            title_fields = ['job_title', 'title', 'position', 'role', 'job_position', 'current_role']

            if isinstance(data, dict):
                for field in title_fields:
                    if field in data and isinstance(data[field], str):
                        titles.append(data[field])

                # Look for nested job title data
                if 'analysis' in data and isinstance(data['analysis'], dict):
                    for field in title_fields:
                        if field in data['analysis']:
                            titles.append(data['analysis'][field])

            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for field in title_fields:
                            if field in item and isinstance(item[field], str):
                                titles.append(item[field])

        except Exception as e:
            logger.debug(f"Could not extract titles from {file_path}: {e}")

        return titles

    def _enhance_titles_with_ai(self, raw_titles: List[str]) -> List[str]:
        """Use AI engine to enhance and generate additional realistic job titles."""
        enhanced_titles = list(raw_titles)

        try:
            # Use NLP engine to analyze and generate similar titles
            for title in raw_titles[:10]:  # Process a sample to avoid overload
                similar_analysis = self.ai_engine.nlp_engine.extract_entities(f"Similar job titles to {title}")

                # Use Bayesian engine to predict related categories
                category, confidence = self.ai_engine.bayesian_engine.predict_job_category(title)

                if confidence > 0.6:
                    # Generate variations based on AI analysis
                    variations = self._generate_title_variations(title, category)
                    enhanced_titles.extend(variations)

            # Use AI learning table to get additional learned titles
            learned_titles = self.ai_engine.learning_table.get_learned_terms('job_title')
            enhanced_titles.extend(learned_titles[:20])

        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")

        return enhanced_titles

    def _generate_title_variations(self, base_title: str, category: str) -> List[str]:
        """Generate realistic variations of a job title based on AI analysis."""
        variations = []

        # Seniority variations
        if 'senior' not in base_title.lower():
            variations.append(f"Senior {base_title}")
        if 'lead' not in base_title.lower():
            variations.append(f"Lead {base_title}")
        if 'principal' not in base_title.lower() and 'senior' in base_title.lower():
            variations.append(f"Principal {base_title.replace('Senior', '').strip()}")

        # Department/domain variations
        if 'data' in category.lower():
            variations.extend([f"Healthcare {base_title}", f"Financial {base_title}"])
        elif 'engineer' in category.lower():
            variations.extend([f"Cloud {base_title}", f"Mobile {base_title}"])

        return variations[:3]  # Limit variations

    def load_real_skills_data(self) -> List[str]:
        """Load real skills from CV data and AI analysis."""
        if 'skills' in self.cached_data:
            return self.cached_data['skills']

        skills = []

        # Extract skills from JSON files
        for data_path in self.ai_data_paths:
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.lower().endswith('.json'):
                        file_path = Path(root) / file
                        json_skills = self._extract_skills_from_json(file_path)
                        skills.extend(json_skills)

        # Use AI engine to enhance skills list
        if self.ai_engine:
            learned_skills = self.ai_engine.learning_table.get_learned_terms('skills')
            skills.extend(learned_skills)

        # Remove duplicates and clean up
        unique_skills = list(set([skill.strip().title() for skill in skills if len(skill.strip()) > 2]))

        self.cached_data['skills'] = unique_skills
        logger.info(f"Loaded {len(unique_skills)} real skills from AI data")

        return unique_skills

    def _extract_skills_from_json(self, file_path: Path) -> List[str]:
        """Extract skills from JSON files."""
        skills = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            skill_fields = ['skills', 'technical_skills', 'competencies', 'technologies', 'tools']

            if isinstance(data, dict):
                for field in skill_fields:
                    if field in data:
                        if isinstance(data[field], list):
                            skills.extend([str(skill) for skill in data[field]])
                        elif isinstance(data[field], str):
                            skills.extend(data[field].split(','))

        except Exception as e:
            logger.debug(f"Could not extract skills from {file_path}: {e}")

        return skills

    def load_real_companies_data(self) -> List[str]:
        """Load real company names from CV data."""
        if 'companies' in self.cached_data:
            return self.cached_data['companies']

        companies = []

        # Extract from JSON files
        for data_path in self.ai_data_paths:
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.lower().endswith('.json'):
                        file_path = Path(root) / file
                        json_companies = self._extract_companies_from_json(file_path)
                        companies.extend(json_companies)

        # Clean and deduplicate
        unique_companies = list(set([company.strip() for company in companies if len(company.strip()) > 2]))

        self.cached_data['companies'] = unique_companies
        logger.info(f"Loaded {len(unique_companies)} real companies from AI data")

        return unique_companies

    def _extract_companies_from_json(self, file_path: Path) -> List[str]:
        """Extract company names from JSON files."""
        companies = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            company_fields = ['company', 'employer', 'organization', 'workplace', 'current_company']

            if isinstance(data, dict):
                for field in company_fields:
                    if field in data and isinstance(data[field], str):
                        companies.append(data[field])

                # Look for work experience sections
                if 'experience' in data and isinstance(data['experience'], list):
                    for exp in data['experience']:
                        if isinstance(exp, dict):
                            for field in company_fields:
                                if field in exp and isinstance(exp[field], str):
                                    companies.append(exp[field])

        except Exception as e:
            logger.debug(f"Could not extract companies from {file_path}: {e}")

        return companies

    def get_ai_generated_insights(self, job_title: str) -> Dict[str, Any]:
        """Get AI-generated insights for a job title using real data."""
        if not self.ai_engine:
            return self._fallback_insights(job_title)

        try:
            # Use Bayesian engine for predictions
            category, confidence = self.ai_engine.bayesian_engine.predict_job_category(job_title)

            # Use NLP for entity extraction
            entities = self.ai_engine.nlp_engine.extract_entities(job_title)

            # Use fuzzy logic for quality assessment
            quality_score = self.ai_engine.fuzzy_engine.assess_data_quality(job_title)

            insights = {
                'predicted_category': category,
                'confidence_score': round(confidence, 3),
                'quality_assessment': round(quality_score, 3),
                'extracted_entities': entities.get('entities', []),
                'similar_titles': self.load_real_job_titles()[:5],
                'trending_skills': self.load_real_skills_data()[:8],
                'top_companies': self.load_real_companies_data()[:6],
                'analysis_timestamp': datetime.now().isoformat(),
                'data_source': 'ai_engine_with_real_data'
            }

            # Learn from this analysis
            self.ai_engine.learning_table.add_term(job_title, 'insights_request', f"Generated insights for {job_title}")

            return insights

        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return self._fallback_insights(job_title)

    def _fallback_insights(self, job_title: str) -> Dict[str, Any]:
        """Fallback insights when AI engine is unavailable."""
        return {
            'predicted_category': 'Technology',
            'confidence_score': 0.7,
            'quality_assessment': 0.8,
            'extracted_entities': [job_title],
            'similar_titles': self.load_real_job_titles()[:5],
            'trending_skills': self.load_real_skills_data()[:8],
            'top_companies': self.load_real_companies_data()[:6],
            'analysis_timestamp': datetime.now().isoformat(),
            'data_source': 'fallback_with_real_data'
        }

    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about loaded real data."""
        return {
            'total_job_titles': len(self.load_real_job_titles()),
            'total_skills': len(self.load_real_skills_data()),
            'total_companies': len(self.load_real_companies_data()),
            'ai_data_directories': len(self.ai_data_paths),
            'ai_engine_available': self.ai_engine is not None
        }

# Global instance for easy access throughout the platform
real_ai_connector = RealAIConnector()

# Convenience functions for easy integration
def get_real_job_titles(limit: int = 30) -> List[str]:
    """Get real job titles from AI data."""
    return real_ai_connector.load_real_job_titles(limit)

def get_real_skills(limit: int = 50) -> List[str]:
    """Get real skills from AI data."""
    return real_ai_connector.load_real_skills_data()[:limit]

def get_real_companies(limit: int = 20) -> List[str]:
    """Get real companies from AI data."""
    return real_ai_connector.load_real_companies_data()[:limit]

def get_ai_insights(job_title: str) -> Dict[str, Any]:
    """Get AI-generated insights using real data."""
    return real_ai_connector.get_ai_generated_insights(job_title)

if __name__ == "__main__":
    # Test the data loader
    loader = RealAIConnector()
    stats = loader.get_statistics()
    print("AI Data Loader Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print(f"\nSample job titles: {loader.load_real_job_titles(5)}")
    print(f"Sample skills: {loader.load_real_skills_data()[:5]}")
    print(f"Sample companies: {loader.load_real_companies_data()[:5]}")
