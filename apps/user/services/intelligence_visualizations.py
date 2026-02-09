"""
Intelligence Visualizations - CaReerTroJan
==========================================
Complete visualization service for career intelligence.

Integrates with:
- career_charts.py (Plotly chart generators)
- streamlit_charts.py (Streamlit components)
- SharedIOLayer (data access)

Charts Available:
- Magic Quadrant (career positioning)
- Covey Quadrant (priority matrix)
- Spider/Radar (skills comparison)
- Word Cloud (skill keywords)
- Score Histogram (peer distribution)
- Peer Comparison Table (HTML)
- Experience Bar Chart
- Skills Distribution

Author: CaReerTroJan System
Date: February 2, 2026
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

root = Path(__file__).parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

try:
    from shared.io_layer import get_io_layer
except ImportError:
    get_io_layer = None

# Import career charts service
try:
    from shared_backend.services.career_charts import (
        create_magic_quadrant_chart,
        create_covey_quadrant_chart,
        create_spider_chart,
        create_score_histogram,
        create_peer_comparison_table,
        generate_word_cloud_data,
        create_word_cloud_plotly,
        create_word_cloud_image,
        get_magic_quadrant_zone,
        get_covey_zone,
        MAGIC_QUADRANT_ZONES,
        COVEY_QUADRANT_ZONES
    )
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)


class IntelligenceVisualizations:
    """
    Complete visualization service for career intelligence.
    
    Creates interactive Plotly charts for:
    - Career positioning (Magic Quadrant)
    - Skills analysis (Spider/Radar charts)
    - Peer comparison (histograms, tables)
    - Priority management (Covey Quadrant)
    - Keyword visualization (Word Clouds)
    """

    def __init__(self):
        """Initialize with SharedIOLayer if available."""
        self.io = get_io_layer() if get_io_layer else None
        self.charts_enabled = CHARTS_AVAILABLE

    # ==========================================================================
    # MAGIC QUADRANT - Career Positioning
    # ==========================================================================
    
    def create_quadrant_chart(
        self,
        visualization_data: Dict[str, Any],
        quadrant_config: Optional[Dict] = None,
        candidate_name: str = "You"
    ) -> go.Figure:
        """
        Create a Magic Quadrant positioning chart.
        
        Args:
            visualization_data: {score, keyword_count, peers, ...}
            quadrant_config: Optional quadrant customization
            candidate_name: Display name
        
        Returns:
            Plotly Figure object
        """
        if self.charts_enabled:
            # Extract values
            score = visualization_data.get('score', 50)
            keywords = visualization_data.get('keyword_count', 10)
            
            # Scale to 0-100
            x = min(100, max(0, score))
            y = min(100, max(0, keywords * 5))
            
            # Extract peers
            peers = visualization_data.get('peers', [])
            peer_data = [
                {
                    'name': p.get('name', f'Peer {i+1}'),
                    'x': min(100, p.get('score', 50)),
                    'y': min(100, p.get('keywords', 10) * 5)
                }
                for i, p in enumerate(peers[:10])
            ]
            
            return create_magic_quadrant_chart(
                candidate_x=x,
                candidate_y=y,
                candidate_name=candidate_name,
                peers=peer_data
            )
        else:
            return self._create_simple_quadrant(visualization_data)
    
    def _create_simple_quadrant(self, data: Dict) -> go.Figure:
        """Fallback simple quadrant chart."""
        fig = go.Figure()
        
        x, y = data.get('score', 50), data.get('keyword_count', 10) * 5
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            text=['You'],
            textposition='top center',
            marker=dict(size=20, color='purple', symbol='star')
        ))
        
        # Add quadrant lines
        fig.add_hline(y=50, line_dash="dash", line_color="gray")
        fig.add_vline(x=50, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title="Career Positioning",
            xaxis=dict(title="Ability", range=[0, 100]),
            yaxis=dict(title="Vision", range=[0, 100]),
            height=450
        )
        
        return fig
    
    def get_quadrant_insights(self, score: float, keywords: int) -> Dict[str, str]:
        """
        Get insights about quadrant position.
        
        Returns:
            Dict with zone info and recommendations
        """
        x = min(100, max(0, score))
        y = min(100, max(0, keywords * 5))
        
        if self.charts_enabled:
            zone = get_magic_quadrant_zone(x, y)
            return {
                'zone_name': zone.name,
                'description': zone.description,
                'color': zone.color,
                'x_position': x,
                'y_position': y
            }
        else:
            # Simple quadrant determination
            if x >= 50 and y >= 50:
                return {'zone_name': '🌟 Leader', 'description': 'Strong position'}
            elif x >= 50:
                return {'zone_name': '⚔️ Challenger', 'description': 'Build vision'}
            elif y >= 50:
                return {'zone_name': '💡 Visionary', 'description': 'Improve execution'}
            else:
                return {'zone_name': '🎯 Niche', 'description': 'Growing potential'}

    # ==========================================================================
    # SPIDER/RADAR CHART - Skills Analysis
    # ==========================================================================
    
    def create_spider_chart(
        self,
        skills: Dict[str, float],
        peer_average: Optional[Dict[str, float]] = None,
        candidate_name: str = "You",
        title: str = "Skills Radar"
    ) -> go.Figure:
        """
        Create a spider/radar chart for skills visualization.
        
        Args:
            skills: Dict of {skill_name: score (0-100)}
            peer_average: Optional peer comparison data
            candidate_name: Display name
            title: Chart title
        
        Returns:
            Plotly Figure object
        """
        if self.charts_enabled:
            return create_spider_chart(
                candidate_skills=skills,
                peer_average=peer_average,
                candidate_name=candidate_name,
                title=title
            )
        else:
            return self._create_simple_radar(skills, peer_average, title)
    
    def _create_simple_radar(
        self,
        skills: Dict[str, float],
        peer_avg: Optional[Dict] = None,
        title: str = "Skills"
    ) -> go.Figure:
        """Fallback simple radar chart."""
        categories = list(skills.keys())
        values = list(skills.values())
        
        # Close the polygon
        categories = categories + [categories[0]]
        values = values + [values[0]]
        
        fig = go.Figure()
        
        if peer_avg:
            peer_values = [peer_avg.get(c, 50) for c in categories[:-1]] + [peer_avg.get(categories[0], 50)]
            fig.add_trace(go.Scatterpolar(
                r=peer_values, theta=categories,
                fill='toself', name='Peer Average',
                fillcolor='rgba(100,100,100,0.2)'
            ))
        
        fig.add_trace(go.Scatterpolar(
            r=values, theta=categories,
            fill='toself', name='You',
            fillcolor='rgba(124,58,237,0.3)',
            line=dict(color='#7c3aed')
        ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title=title,
            height=400
        )
        
        return fig
    
    def create_skills_from_resume(
        self,
        resume_skills: List[str],
        job_requirements: Optional[List[str]] = None
    ) -> go.Figure:
        """
        Auto-generate skills radar from resume data.
        
        Args:
            resume_skills: List of skills extracted from resume
            job_requirements: Optional job requirements for peer comparison
        
        Returns:
            Plotly Figure with skills radar
        """
        # Categorize skills into competency areas
        categories = self._categorize_skills(resume_skills)
        
        # Generate peer baseline if job requirements provided
        peer_avg = None
        if job_requirements:
            peer_avg = {cat: 60 for cat in categories}  # Industry baseline
        
        return self.create_spider_chart(categories, peer_avg)
    
    def _categorize_skills(self, skills: List[str]) -> Dict[str, float]:
        """Categorize skills into competency areas with scores."""
        categories = {
            "Technical": 0,
            "Leadership": 0,
            "Communication": 0,
            "Problem Solving": 0,
            "Domain Knowledge": 0,
            "Soft Skills": 0
        }
        
        # Keyword mappings
        mappings = {
            "Technical": ['python', 'java', 'sql', 'aws', 'cloud', 'api', 'data', 'ml', 'ai'],
            "Leadership": ['lead', 'manage', 'direct', 'team', 'mentor', 'supervise'],
            "Communication": ['present', 'communicate', 'collaborate', 'negotiate'],
            "Problem Solving": ['solve', 'analyze', 'optimize', 'design', 'architect'],
            "Domain Knowledge": ['finance', 'healthcare', 'retail', 'manufacturing'],
            "Soft Skills": ['creative', 'adaptable', 'detail', 'organized']
        }
        
        for skill in skills:
            skill_lower = skill.lower()
            for cat, keywords in mappings.items():
                if any(kw in skill_lower for kw in keywords):
                    categories[cat] += 15
        
        # Normalize and add baseline
        return {k: min(100, max(25, v)) for k, v in categories.items()}

    # ==========================================================================
    # SCORE HISTOGRAM - Peer Distribution
    # ==========================================================================
    
    def create_score_histogram(
        self,
        candidate_score: float,
        peer_scores: Optional[List[float]] = None,
        candidate_name: str = "You",
        title: str = "Score Distribution"
    ) -> go.Figure:
        """
        Create a histogram showing candidate position vs peers.
        
        Args:
            candidate_score: Candidate's score
            peer_scores: List of peer scores
            candidate_name: Display name
            title: Chart title
        
        Returns:
            Plotly Figure object
        """
        import random
        
        # Generate synthetic peers if not provided
        if not peer_scores:
            peer_scores = [max(0, min(100, random.gauss(55, 18))) for _ in range(200)]
        
        if self.charts_enabled:
            return create_score_histogram(
                candidate_score=candidate_score,
                peer_scores=peer_scores,
                candidate_name=candidate_name,
                title=title
            )
        else:
            return self._create_simple_histogram(candidate_score, peer_scores, title)
    
    def _create_simple_histogram(
        self,
        score: float,
        peers: List[float],
        title: str
    ) -> go.Figure:
        """Fallback simple histogram."""
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=peers, nbinsx=20,
            name='Peers', opacity=0.7
        ))
        
        fig.add_vline(
            x=score,
            line_dash="dash",
            line_color="purple",
            annotation_text=f"You: {score:.1f}"
        )
        
        fig.update_layout(title=title, height=350)
        
        return fig

    # ==========================================================================
    # PEER COMPARISON TABLE
    # ==========================================================================
    
    def create_peer_comparison_table(
        self,
        candidate_data: Dict[str, Any],
        top_performers: List[Dict[str, Any]],
        show_names: bool = False
    ) -> str:
        """
        Create an HTML peer comparison table.
        
        Args:
            candidate_data: Candidate's data
            top_performers: List of top performer data
            show_names: Whether to show actual names
        
        Returns:
            HTML string for the table
        """
        if self.charts_enabled:
            return create_peer_comparison_table(
                candidate_data=candidate_data,
                top_performers=top_performers,
                show_names=show_names
            )
        else:
            return self._create_simple_table(candidate_data, top_performers)
    
    def _create_simple_table(
        self,
        candidate: Dict,
        peers: List[Dict]
    ) -> str:
        """Fallback simple HTML table."""
        html = "<table><tr><th>Rank</th><th>Score</th></tr>"
        html += f"<tr style='background:#fef3c7'><td>You</td><td>{candidate.get('score', 0):.1f}</td></tr>"
        
        for i, p in enumerate(peers[:5], 1):
            html += f"<tr><td>#{i}</td><td>{p.get('score', 0):.1f}</td></tr>"
        
        html += "</table>"
        return html

    # ==========================================================================
    # WORD CLOUD
    # ==========================================================================
    
    def create_word_cloud(
        self,
        skills: List[str],
        weights: Optional[Dict[str, float]] = None,
        title: str = "Skills Cloud"
    ) -> go.Figure:
        """
        Create a word cloud visualization.
        
        Args:
            skills: List of skills/keywords
            weights: Optional frequency weights
            title: Chart title
        
        Returns:
            Plotly Figure object
        """
        if self.charts_enabled:
            word_freq = generate_word_cloud_data(skills, weights)
            return create_word_cloud_plotly(word_freq, title)
        else:
            return self._create_simple_word_display(skills, title)
    
    def _create_simple_word_display(
        self,
        skills: List[str],
        title: str
    ) -> go.Figure:
        """Fallback: display skills as sized text."""
        import random
        
        fig = go.Figure()
        
        # Position words randomly
        x_pos = [random.uniform(10, 90) for _ in skills[:30]]
        y_pos = [random.uniform(10, 90) for _ in skills[:30]]
        sizes = [random.randint(12, 24) for _ in skills[:30]]
        
        fig.add_trace(go.Scatter(
            x=x_pos, y=y_pos,
            mode='text',
            text=skills[:30],
            textfont=dict(size=sizes)
        ))
        
        fig.update_layout(
            title=title,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        
        return fig

    # ==========================================================================
    # COVEY QUADRANT - Priority Matrix
    # ==========================================================================
    
    def create_covey_quadrant(
        self,
        tasks: List[Dict[str, Any]],
        title: str = "Priority Matrix"
    ) -> go.Figure:
        """
        Create a Covey Priority Quadrant chart.
        
        Args:
            tasks: List of tasks [{name, urgent, important}]
            title: Chart title
        
        Returns:
            Plotly Figure object
        """
        if self.charts_enabled:
            return create_covey_quadrant_chart(tasks, title)
        else:
            return self._create_simple_priority_chart(tasks, title)
    
    def _create_simple_priority_chart(
        self,
        tasks: List[Dict],
        title: str
    ) -> go.Figure:
        """Fallback simple priority scatter."""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=[t.get('urgent', 50) for t in tasks],
            y=[t.get('important', 50) for t in tasks],
            mode='markers+text',
            text=[t.get('name', '')[:15] for t in tasks],
            textposition='top center'
        ))
        
        fig.add_hline(y=50, line_dash="dash")
        fig.add_vline(x=50, line_dash="dash")
        
        fig.update_layout(
            title=title,
            xaxis=dict(title="Urgency", range=[0, 100]),
            yaxis=dict(title="Importance", range=[0, 100]),
            height=450
        )
        
        return fig

    # ==========================================================================
    # LEGACY COMPATIBILITY METHODS
    # ==========================================================================

    def get_analysis_charts(self, analysis_type: str = 'candidate') -> List[Dict]:
        """
        Get visualization configs from analysis results.

        Args:
            analysis_type: Type of analysis

        Returns:
            List of Plotly chart configs
        """
        if not self.io:
            return []
            
        # Get latest analysis
        analysis = self.io.get_latest_analysis(analysis_type)

        if not analysis:
            return []

        # Extract visualizations from analysis results
        results = analysis.get('results', {})
        visualizations = results.get('visualizations', [])

        return visualizations

    def create_candidate_comparison_chart(self, user_id: str) -> Optional[Dict]:
        """
        Create comparison chart for candidate vs peers.

        Args:
            user_id: Candidate ID

        Returns:
            Plotly chart config dict
        """
        if not self.io:
            return None
            
        # Get candidate
        candidate = self.io.get_candidate_data(user_id)
        if not candidate:
            return None

        # Get peers
        peers = self.io.get_all_candidates(limit=10)
        peers = [p for p in peers if p.get('user_id') != user_id]

        # Extract experience years
        candidate_exp = candidate.get('profile', {}).get('experience_years', 0)
        peer_exps = [p.get('profile', {}).get('experience_years', 0) for p in peers]

        # Use enhanced bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=['You'] + [f"Peer {i+1}" for i in range(len(peers))],
            y=[candidate_exp] + peer_exps,
            marker_color=['#7c3aed'] + ['#94a3b8'] * len(peers),
            name='Experience (Years)'
        ))
        
        fig.update_layout(
            title='Experience Comparison',
            yaxis_title='Years of Experience',
            height=350
        )

        return fig.to_dict()

    def create_skills_distribution_chart(self) -> Optional[Dict]:
        """
        Create skills distribution chart from all candidates.

        Returns:
            Plotly chart config dict
        """
        if not self.io:
            return None
            
        # Get all candidates
        candidates = self.io.get_all_candidates()

        if not candidates:
            return None

        # Count skills
        skill_counts = {}
        for candidate in candidates:
            skills = candidate.get('profile', {}).get('skills', [])
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Top 10 skills
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        fig = px.bar(
            x=[s[0] for s in sorted_skills],
            y=[s[1] for s in sorted_skills],
            labels={'x': 'Skill', 'y': 'Count'},
            title='Top 10 Skills in Talent Pool',
            color_discrete_sequence=['#7c3aed']
        )
        
        fig.update_layout(height=350)

        return fig.to_dict()


# ==========================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ==========================================================================

# Create singleton instance
_viz_instance = None

def get_visualizations() -> IntelligenceVisualizations:
    """Get the visualization service singleton."""
    global _viz_instance
    if _viz_instance is None:
        _viz_instance = IntelligenceVisualizations()
    return _viz_instance

# Convenience aliases for direct import
def create_quadrant_chart(visualization_data: Dict, quadrant: Dict = None, name: str = "You") -> go.Figure:
    """Create Magic Quadrant chart."""
    return get_visualizations().create_quadrant_chart(visualization_data, quadrant, name)

def create_spider_chart(skills: Dict, peer_avg: Dict = None, name: str = "You") -> go.Figure:
    """Create Spider/Radar chart."""
    return get_visualizations().create_spider_chart(skills, peer_avg, name)

def create_score_histogram(score: float, peers: List[float] = None, name: str = "You") -> go.Figure:
    """Create Score Histogram."""
    return get_visualizations().create_score_histogram(score, peers, name)

def create_peer_comparison_table(candidate: Dict, top_performers: List[Dict], show_names: bool = False) -> str:
    """Create Peer Comparison Table HTML."""
    return get_visualizations().create_peer_comparison_table(candidate, top_performers, show_names)
