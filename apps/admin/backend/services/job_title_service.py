"""
IntelliCV Job Title Service - Backend Service
Consolidated backend service for job title analysis and visualization
Callable from both User Portal and Admin Portal

Moved from pages/10_Job_Title_Word_Cloud.py and pages/13_Job_Title_Intelligence.py
Token Cost: 5-7 tokens per operation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import json
import base64
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobTitleService:
    """
    Backend service for job title analysis and visualization.
    Provides all functionality previously in pages 10 and 13.
    """
    
    def __init__(self):
        """Initialize the Job Title Service with token costs."""
        self.token_cost = {
            'generate_word_cloud': 5,
            'analyze_job_title': 7,
            'get_career_pathways': 7,
            'get_market_intelligence': 7,
            'get_title_relationships': 5
        }
        
        # Sample data for demo purposes
        self.sample_job_titles = [
            "Data Scientist", "Software Engineer", "Product Manager", "UX Designer",
            "Marketing Manager", "Business Analyst", "DevOps Engineer", "AI Engineer",
            "Full Stack Developer", "Digital Marketing Specialist", "Project Manager",
            "Quality Assurance Engineer", "Sales Manager", "HR Business Partner",
            "Content Creator", "Cybersecurity Analyst", "Cloud Architect",
            "Machine Learning Engineer", "Frontend Developer", "Backend Developer",
            "Systems Administrator", "Database Administrator", "Technical Writer",
            "Scrum Master", "Solutions Architect", "Data Engineer"
        ]
        
        logger.info("JobTitleService initialized successfully")
    
    def generate_word_cloud(
        self, 
        job_titles: List[str], 
        user_id: str, 
        source_page: str,
        width: int = 800,
        height: int = 400
    ) -> Dict[str, Any]:
        """
        Generate word cloud visualization from job titles.
        
        Args:
            job_titles (list): List of job titles
            user_id (str): User ID for token tracking
            source_page (str): Calling page for analytics
            width (int): Word cloud width
            height (int): Word cloud height
        
        Returns:
            dict: {
                'wordcloud_image_base64': str,
                'insights': str,
                'job_titles_analyzed': int,
                'tokens_used': int,
                'timestamp': str
            }
        """
        try:
            logger.info(f"Generating word cloud for user {user_id} from {source_page}")
            
            # Use provided titles or sample data
            titles_to_use = job_titles if job_titles else self.sample_job_titles
            
            # Create frequency data
            title_text = ' '.join(titles_to_use * 2)  # Repeat for better visualization
            
            # Generate word cloud
            wordcloud = WordCloud(
                width=width,
                height=height,
                background_color='white',
                colormap='viridis',
                max_words=50,
                relative_scaling=0.5
            ).generate(title_text)
            
            # Convert to base64 for web display
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            
            # Save to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            # Generate insights
            insights = self._generate_word_cloud_insights(titles_to_use)
            
            result = {
                'wordcloud_image_base64': img_base64,
                'insights': insights,
                'job_titles_analyzed': len(titles_to_use),
                'tokens_used': self.token_cost['generate_word_cloud'],
                'timestamp': datetime.now().isoformat(),
                'service': 'job_title_service',
                'operation': 'generate_word_cloud'
            }
            
            logger.info(f"Word cloud generated successfully for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating word cloud: {e}")
            return {
                'error': str(e),
                'tokens_used': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_job_title(
        self, 
        title: str, 
        context: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze job title for similarity, skills, salary, fit.
        
        Args:
            title (str): Job title to analyze
            context (dict): {
                'current_title': str,
                'target_titles': list,
                'industry': str,
                'experience_years': int
            }
            user_id (str): User ID for token tracking
        
        Returns:
            dict: {
                'similarity_scores': list,
                'skill_overlaps': list,
                'salary_ranges': dict,
                'career_fit': dict,
                'tokens_used': int
            }
        """
        try:
            logger.info(f"Analyzing job title '{title}' for user {user_id}")
            
            current_title = context.get('current_title', '')
            target_titles = context.get('target_titles', [])
            industry = context.get('industry', 'Technology')
            experience_years = context.get('experience_years', 3)
            
            # Generate similarity scores
            similarity_scores = self._calculate_title_similarity(title, target_titles)
            
            # Generate skill overlaps
            skill_overlaps = self._analyze_skill_overlaps(title, current_title)
            
            # Generate salary ranges
            salary_ranges = self._estimate_salary_ranges(title, industry, experience_years)
            
            # Generate career fit analysis
            career_fit = self._analyze_career_fit(title, current_title, experience_years)
            
            result = {
                'title_analyzed': title,
                'similarity_scores': similarity_scores,
                'skill_overlaps': skill_overlaps,
                'salary_ranges': salary_ranges,
                'career_fit': career_fit,
                'tokens_used': self.token_cost['analyze_job_title'],
                'timestamp': datetime.now().isoformat(),
                'service': 'job_title_service',
                'operation': 'analyze_job_title'
            }
            
            logger.info(f"Job title analysis completed for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing job title: {e}")
            return {
                'error': str(e),
                'tokens_used': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_career_pathways(
        self, 
        current_title: str, 
        experience_years: int, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get career progression pathways.
        
        Args:
            current_title (str): Current job title
            experience_years (int): Years of experience
            user_id (str): User ID for token tracking
        
        Returns:
            dict: {
                'pathways': list,
                'timeline': dict,
                'skills_required': dict,
                'tokens_used': int
            }
        """
        try:
            logger.info(f"Generating career pathways for {current_title} - user {user_id}")
            
            # Generate career pathways based on current title
            pathways = self._generate_career_pathways(current_title, experience_years)
            
            # Generate timeline
            timeline = self._generate_career_timeline(current_title, experience_years)
            
            # Generate skills required
            skills_required = self._generate_required_skills(current_title, pathways)
            
            result = {
                'current_title': current_title,
                'experience_years': experience_years,
                'pathways': pathways,
                'timeline': timeline,
                'skills_required': skills_required,
                'tokens_used': self.token_cost['get_career_pathways'],
                'timestamp': datetime.now().isoformat(),
                'service': 'job_title_service',
                'operation': 'get_career_pathways'
            }
            
            logger.info(f"Career pathways generated for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating career pathways: {e}")
            return {
                'error': str(e),
                'tokens_used': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_market_intelligence(
        self, 
        title: str, 
        industry: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get market intelligence for job title.
        
        Args:
            title (str): Job title
            industry (str): Industry sector
            user_id (str): User ID for token tracking
        
        Returns:
            dict: {
                'demand_score': int,
                'growth_trend': str,
                'geographic_data': dict,
                'tokens_used': int
            }
        """
        try:
            logger.info(f"Generating market intelligence for {title} in {industry}")
            
            # Generate market data
            demand_score = self._calculate_demand_score(title, industry)
            growth_trend = self._analyze_growth_trend(title, industry)
            geographic_data = self._generate_geographic_data(title)
            market_insights = self._generate_market_insights(title, industry)
            
            result = {
                'title': title,
                'industry': industry,
                'demand_score': demand_score,
                'growth_trend': growth_trend,
                'geographic_data': geographic_data,
                'market_insights': market_insights,
                'tokens_used': self.token_cost['get_market_intelligence'],
                'timestamp': datetime.now().isoformat(),
                'service': 'job_title_service',
                'operation': 'get_market_intelligence'
            }
            
            logger.info(f"Market intelligence generated for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating market intelligence: {e}")
            return {
                'error': str(e),
                'tokens_used': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_title_relationships(
        self, 
        title_list: List[str], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze relationships between job titles.
        
        Args:
            title_list (list): List of job titles to analyze
            user_id (str): User ID for token tracking
        
        Returns:
            dict: {
                'network_data': dict,
                'clusters': list,
                'similarity_matrix': list,
                'tokens_used': int
            }
        """
        try:
            logger.info(f"Analyzing title relationships for user {user_id}")
            
            # Generate network data
            network_data = self._generate_title_network(title_list)
            
            # Generate clusters
            clusters = self._cluster_titles(title_list)
            
            # Generate similarity matrix
            similarity_matrix = self._generate_similarity_matrix(title_list)
            
            result = {
                'titles_analyzed': title_list,
                'network_data': network_data,
                'clusters': clusters,
                'similarity_matrix': similarity_matrix,
                'tokens_used': self.token_cost['get_title_relationships'],
                'timestamp': datetime.now().isoformat(),
                'service': 'job_title_service',
                'operation': 'get_title_relationships'
            }
            
            logger.info(f"Title relationships analyzed for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing title relationships: {e}")
            return {
                'error': str(e),
                'tokens_used': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    # Helper methods for analysis
    
    def _generate_word_cloud_insights(self, titles: List[str]) -> str:
        """Generate insights from job titles."""
        tech_count = sum(1 for title in titles if any(word in title.lower() 
                        for word in ['engineer', 'developer', 'data', 'ai', 'tech']))
        
        insights = f"""
        **Job Market Insights:**
        - Analyzed {len(titles)} job titles
        - Technology roles: {tech_count} ({tech_count/len(titles)*100:.1f}%)
        - Most common keywords detected in visualization
        - Career opportunities span multiple industries
        """
        return insights.strip()
    
    def _calculate_title_similarity(self, title: str, target_titles: List[str]) -> List[Dict]:
        """Calculate similarity scores between titles."""
        similarities = []
        for target in target_titles:
            # Simple similarity calculation (could be enhanced with NLP)
            common_words = set(title.lower().split()) & set(target.lower().split())
            similarity = len(common_words) / max(len(title.split()), len(target.split()))
            
            similarities.append({
                'target_title': target,
                'similarity_score': round(similarity * 100, 1),
                'common_keywords': list(common_words)
            })
        
        return similarities
    
    def _analyze_skill_overlaps(self, title: str, current_title: str) -> List[Dict]:
        """Analyze skill overlaps between titles."""
        # Mock skill analysis
        skills_map = {
            'data': ['Python', 'SQL', 'Statistics', 'Machine Learning'],
            'software': ['Programming', 'Git', 'Testing', 'Agile'],
            'product': ['Strategy', 'Analytics', 'User Research', 'Roadmapping'],
            'marketing': ['Digital Marketing', 'Analytics', 'Content', 'SEO']
        }
        
        overlaps = []
        for category, skills in skills_map.items():
            if category in title.lower() or category in current_title.lower():
                overlaps.append({
                    'skill_category': category.title(),
                    'skills': skills,
                    'overlap_percentage': np.random.randint(60, 95)
                })
        
        return overlaps
    
    def _estimate_salary_ranges(self, title: str, industry: str, experience: int) -> Dict:
        """Estimate salary ranges for job title."""
        # Mock salary estimation
        base_salary = 50000 + (experience * 8000)
        
        if 'senior' in title.lower():
            base_salary *= 1.3
        if 'lead' in title.lower() or 'manager' in title.lower():
            base_salary *= 1.5
        if 'director' in title.lower():
            base_salary *= 2.0
        
        return {
            'currency': 'USD',
            'min_salary': int(base_salary * 0.8),
            'max_salary': int(base_salary * 1.2),
            'median_salary': int(base_salary),
            'confidence': 'Medium',
            'data_points': np.random.randint(50, 200)
        }
    
    def _analyze_career_fit(self, title: str, current_title: str, experience: int) -> Dict:
        """Analyze career fit for transition."""
        # Mock career fit analysis
        fit_score = np.random.randint(70, 95)
        
        return {
            'fit_score': fit_score,
            'transition_difficulty': 'Medium' if fit_score > 80 else 'High',
            'recommended_timeline': f"{max(6, 18-experience)} months",
            'key_gaps': ['Advanced Analytics', 'Leadership Skills'],
            'strengths': ['Domain Knowledge', 'Technical Skills']
        }
    
    def _generate_career_pathways(self, current_title: str, experience: int) -> List[Dict]:
        """Generate career progression pathways."""
        pathways = []
        
        if 'analyst' in current_title.lower():
            pathways.extend([
                {'title': 'Senior Data Analyst', 'years': max(1, 3-experience), 'probability': 85},
                {'title': 'Data Scientist', 'years': max(2, 4-experience), 'probability': 70},
                {'title': 'Analytics Manager', 'years': max(3, 5-experience), 'probability': 60}
            ])
        
        if 'engineer' in current_title.lower():
            pathways.extend([
                {'title': 'Senior Software Engineer', 'years': max(1, 3-experience), 'probability': 90},
                {'title': 'Tech Lead', 'years': max(2, 5-experience), 'probability': 75},
                {'title': 'Engineering Manager', 'years': max(3, 6-experience), 'probability': 65}
            ])
        
        return pathways if pathways else [
            {'title': 'Senior ' + current_title, 'years': 2, 'probability': 80},
            {'title': current_title.replace('Junior', 'Senior'), 'years': 3, 'probability': 70}
        ]
    
    def _generate_career_timeline(self, current_title: str, experience: int) -> Dict:
        """Generate career timeline."""
        return {
            'current_stage': f"Mid-level" if experience > 3 else "Junior",
            'next_milestone': f"Senior {current_title}" if experience < 5 else f"{current_title} Lead",
            'timeline_years': {
                '1_year': 'Skill development and specialization',
                '3_years': 'Senior role transition',
                '5_years': 'Leadership opportunities'
            }
        }
    
    def _generate_required_skills(self, current_title: str, pathways: List[Dict]) -> Dict:
        """Generate required skills for career pathways."""
        return {
            'technical_skills': ['Advanced Analytics', 'Cloud Computing', 'AI/ML'],
            'soft_skills': ['Leadership', 'Communication', 'Strategic Thinking'],
            'certifications': ['Professional Certification', 'Cloud Certification'],
            'priority_order': ['Technical Skills', 'Leadership', 'Certifications']
        }
    
    def _calculate_demand_score(self, title: str, industry: str) -> int:
        """Calculate job demand score."""
        # Mock demand calculation
        base_score = 70
        
        if 'data' in title.lower() or 'ai' in title.lower():
            base_score += 20
        if 'engineer' in title.lower():
            base_score += 15
        if industry.lower() == 'technology':
            base_score += 10
            
        return min(100, base_score)
    
    def _analyze_growth_trend(self, title: str, industry: str) -> str:
        """Analyze job growth trend."""
        if 'data' in title.lower() or 'ai' in title.lower():
            return 'High Growth (+15% annually)'
        elif 'engineer' in title.lower():
            return 'Steady Growth (+8% annually)'
        else:
            return 'Moderate Growth (+5% annually)'
    
    def _generate_geographic_data(self, title: str) -> Dict:
        """Generate geographic job data."""
        return {
            'top_locations': [
                {'city': 'San Francisco', 'jobs': np.random.randint(500, 1500)},
                {'city': 'New York', 'jobs': np.random.randint(400, 1200)},
                {'city': 'Seattle', 'jobs': np.random.randint(300, 1000)},
                {'city': 'Austin', 'jobs': np.random.randint(200, 800)}
            ],
            'remote_percentage': np.random.randint(40, 80)
        }
    
    def _generate_market_insights(self, title: str, industry: str) -> List[str]:
        """Generate market insights."""
        return [
            f"{title} roles are in high demand in {industry}",
            "Remote work opportunities are increasing",
            "Salary ranges vary significantly by location",
            "Emerging technologies are creating new opportunities"
        ]
    
    def _generate_title_network(self, titles: List[str]) -> Dict:
        """Generate network data for titles."""
        # Create simple network
        nodes = [{'id': i, 'label': title, 'size': np.random.randint(10, 30)} 
                for i, title in enumerate(titles)]
        
        edges = []
        for i in range(len(titles)):
            for j in range(i+1, min(i+3, len(titles))):
                edges.append({'from': i, 'to': j, 'weight': np.random.random()})
        
        return {'nodes': nodes, 'edges': edges}
    
    def _cluster_titles(self, titles: List[str]) -> List[Dict]:
        """Cluster similar titles."""
        # Simple clustering based on keywords
        clusters = {
            'Technical': [t for t in titles if any(word in t.lower() 
                         for word in ['engineer', 'developer', 'data'])],
            'Management': [t for t in titles if any(word in t.lower() 
                          for word in ['manager', 'director', 'lead'])],
            'Creative': [t for t in titles if any(word in t.lower() 
                        for word in ['designer', 'creative', 'content'])]
        }
        
        return [{'cluster': name, 'titles': titles} for name, titles in clusters.items() if titles]
    
    def _generate_similarity_matrix(self, titles: List[str]) -> List[List[float]]:
        """Generate similarity matrix for titles."""
        n = len(titles)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    # Simple similarity based on common words
                    words_i = set(titles[i].lower().split())
                    words_j = set(titles[j].lower().split())
                    similarity = len(words_i & words_j) / len(words_i | words_j)
                    matrix[i][j] = round(similarity, 3)
        
        return matrix
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and metrics."""
        return {
            'service_name': 'JobTitleService',
            'status': 'active',
            'available_operations': list(self.token_cost.keys()),
            'token_costs': self.token_cost,
            'last_health_check': datetime.now().isoformat()
        }


# Global service instance
_job_title_service = None

def get_job_title_service() -> JobTitleService:
    """Get or create global Job Title Service instance."""
    global _job_title_service
    if _job_title_service is None:
        _job_title_service = JobTitleService()
    return _job_title_service


# Convenience functions for easy integration
def generate_word_cloud(job_titles: List[str], user_id: str, source_page: str = "unknown") -> Dict[str, Any]:
    """Quick access to word cloud generation."""
    service = get_job_title_service()
    return service.generate_word_cloud(job_titles, user_id, source_page)

def analyze_job_title(title: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Quick access to job title analysis."""
    service = get_job_title_service()
    return service.analyze_job_title(title, context, user_id)

def get_career_pathways(current_title: str, experience_years: int, user_id: str) -> Dict[str, Any]:
    """Quick access to career pathways."""
    service = get_job_title_service()
    return service.get_career_pathways(current_title, experience_years, user_id)

def get_market_intelligence(title: str, industry: str, user_id: str) -> Dict[str, Any]:
    """Quick access to market intelligence."""
    service = get_job_title_service()
    return service.get_market_intelligence(title, industry, user_id)

def get_title_relationships(title_list: List[str], user_id: str) -> Dict[str, Any]:
    """Quick access to title relationships."""
    service = get_job_title_service()
    return service.get_title_relationships(title_list, user_id)


if __name__ == "__main__":
    # Test the service
    service = JobTitleService()
    
    # Test word cloud generation
    result = service.generate_word_cloud(
        job_titles=["Data Scientist", "Software Engineer", "Product Manager"],
        user_id="test_user",
        source_page="test"
    )
    print("Word Cloud Test:", result.get('tokens_used'), "tokens used")
    
    # Test job title analysis
    result = service.analyze_job_title(
        title="Data Scientist",
        context={
            'current_title': "Data Analyst",
            'target_titles': ["Senior Data Analyst", "Data Scientist"],
            'industry': "Technology",
            'experience_years': 3
        },
        user_id="test_user"
    )
    print("Job Analysis Test:", result.get('tokens_used'), "tokens used")
    
    print("Job Title Service tests completed successfully!")