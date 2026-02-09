"""
Advanced Analytics Service - Integration Layer
Connects statistical engine with existing IntelliCV services
Provides high-level analytics workflows for admin dashboard
"""

import sys
from pathlib import Path
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

# Add analytics to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analytics.stats_engine import ZeroCostStatsEngine, get_stats_engine
from analytics.feature_builder import ZeroCostFeatureBuilder, get_feature_builder

logger = logging.getLogger(__name__)


class AdvancedAnalyticsService:
    """
    High-level analytics service integrating statistical engine
    with existing IntelliCV admin services.

    Provides:
    - Candidate pool analysis
    - Job market intelligence
    - Resume quality scoring
    - Predictive analytics
    - A/B testing capabilities
    - Performance benchmarking
    """

    def __init__(self, data_dir: Path = None):
        """
        Initialize advanced analytics service.

        Args:
            data_dir: Path to ai_data_final directory
        """
        if data_dir is None:
            # Default to SANDBOX ai_data_final
            data_dir = Path(__file__).parent.parent.parent.parent / "ai_data_final"

        self.data_dir = Path(data_dir)
        self.stats_engine = get_stats_engine(data_dir=self.data_dir)
        self.feature_builder = get_feature_builder()

        logger.info(f"📊 Advanced Analytics Service initialized with data_dir: {self.data_dir}")

    # ==================== CANDIDATE ANALYTICS ====================

    def analyze_candidate_pool(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Comprehensive candidate pool analysis.

        Args:
            filters: Optional filters (e.g., {'location': 'London', 'min_experience': 3})

        Returns:
            Complete analysis including stats, distributions, insights
        """
        logger.info("📊 Starting candidate pool analysis...")

        # Load candidates
        df = self.stats_engine.load_candidates()

        if df.empty:
            return {
                'error': 'No candidate data available',
                'timestamp': datetime.now().isoformat()
            }

        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if key in df.columns:
                    df = df[df[key] == value]

        # Descriptive statistics
        descriptive_stats = self.stats_engine.describe_candidate_pool(df)

        # Build features for ML readiness
        try:
            candidate_features = self.feature_builder.build_candidate_features(df)
            feature_summary = {
                'original_columns': len(df.columns),
                'enhanced_columns': len(candidate_features.columns),
                'new_features': len(candidate_features.columns) - len(df.columns),
                'ml_ready': True
            }
        except Exception as e:
            logger.warning(f"Feature building failed: {e}")
            feature_summary = {'ml_ready': False, 'error': str(e)}

        # Distribution analysis for key metrics
        distributions = {}
        if 'salary_expectation' in df.columns:
            salaries = df['salary_expectation'].dropna().tolist()
            if len(salaries) >= 10:
                distributions['salary'] = self.stats_engine.fit_salary_distribution(salaries)

        # Time-based analysis if date column exists
        time_series_analysis = None
        if 'application_date' in df.columns or 'created_at' in df.columns:
            date_col = 'application_date' if 'application_date' in df.columns else 'created_at'
            try:
                time_series_analysis = self.stats_engine.analyze_application_trends(
                    df, date_col=date_col, value_col='id'
                )
            except Exception as e:
                logger.warning(f"Time series analysis failed: {e}")

        # Compile comprehensive report
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'filters_applied': filters or {},
            'total_candidates': len(df),
            'descriptive_statistics': descriptive_stats,
            'feature_engineering': feature_summary,
            'distributions': distributions,
            'time_series': time_series_analysis,
            'insights': self._generate_candidate_insights(df, descriptive_stats)
        }

        # Save analysis
        filename = f"candidate_pool_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats_engine.save_analysis(filename, analysis)

        logger.info(f"✅ Candidate pool analysis complete: {len(df)} candidates analyzed")
        return analysis

    def _generate_candidate_insights(self, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Generate actionable insights from candidate data."""
        insights = []

        # Experience insights
        if 'years_experience' in df.columns:
            avg_exp = df['years_experience'].mean()
            if avg_exp < 3:
                insights.append(f"⚠️ Pool skews junior (avg {avg_exp:.1f} years) - consider mid-level recruitment")
            elif avg_exp > 10:
                insights.append(f"💡 Pool has strong senior talent (avg {avg_exp:.1f} years) - ideal for leadership roles")

        # Salary insights
        if 'salary_expectation' in df.columns:
            salary_std = df['salary_expectation'].std()
            salary_mean = df['salary_expectation'].mean()
            cv = (salary_std / salary_mean) * 100 if salary_mean > 0 else 0

            if cv > 30:
                insights.append(f"📊 High salary variance (CV={cv:.1f}%) - diverse experience levels")

        # Data quality insights
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if missing_pct > 20:
            insights.append(f"⚠️ {missing_pct:.1f}% missing data - data quality improvement needed")

        return insights

    # ==================== JOB MARKET ANALYTICS ====================

    def analyze_job_market(self, job_category: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze job market trends and requirements.

        Args:
            job_category: Optional category filter

        Returns:
            Job market analysis with trends and insights
        """
        logger.info("📈 Starting job market analysis...")

        df = self.stats_engine.load_jobs()

        if df.empty:
            return {
                'error': 'No job data available',
                'timestamp': datetime.now().isoformat()
            }

        # Filter by category if provided
        if job_category and 'category' in df.columns:
            df = df[df['category'] == job_category]

        # Descriptive statistics
        descriptive_stats = self.stats_engine.describe_candidate_pool(df)

        # Salary analysis
        salary_distributions = {}
        if 'salary_min' in df.columns and 'salary_max' in df.columns:
            # Analyze salary ranges
            df['salary_midpoint'] = (df['salary_min'] + df['salary_max']) / 2
            midpoints = df['salary_midpoint'].dropna().tolist()

            if len(midpoints) >= 10:
                salary_distributions = self.stats_engine.fit_salary_distribution(midpoints)

        # Build job features
        try:
            job_features = self.feature_builder.build_job_features(df)
            feature_summary = {
                'original_columns': len(df.columns),
                'enhanced_columns': len(job_features.columns),
                'new_features': len(job_features.columns) - len(df.columns)
            }
        except Exception as e:
            logger.warning(f"Job feature building failed: {e}")
            feature_summary = {'error': str(e)}

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'job_category': job_category,
            'total_jobs': len(df),
            'descriptive_statistics': descriptive_stats,
            'salary_distributions': salary_distributions,
            'feature_engineering': feature_summary,
            'insights': self._generate_job_insights(df)
        }

        # Save analysis
        filename = f"job_market_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats_engine.save_analysis(filename, analysis)

        logger.info(f"✅ Job market analysis complete: {len(df)} jobs analyzed")
        return analysis

    def _generate_job_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate actionable insights from job data."""
        insights = []

        # Experience requirements
        if 'experience_required' in df.columns:
            avg_req = df['experience_required'].mean()
            if avg_req > 7:
                insights.append(f"📊 High experience requirements (avg {avg_req:.1f} years) - competitive market")

        # Remote work trends
        if 'is_remote' in df.columns:
            remote_pct = (df['is_remote'].sum() / len(df)) * 100
            insights.append(f"🏠 {remote_pct:.1f}% remote positions - {'high' if remote_pct > 30 else 'low'} remote availability")

        # Salary competitiveness
        if 'salary_min' in df.columns:
            low_salary_pct = (df['salary_min'] < 35000).sum() / len(df) * 100
            if low_salary_pct > 40:
                insights.append(f"⚠️ {low_salary_pct:.1f}% positions below £35k - salary competitiveness concern")

        return insights

    # ==================== MATCHING ANALYTICS ====================

    def calculate_candidate_job_matches(
        self,
        top_n_candidates: int = 50,
        top_n_jobs: int = 20,
        min_score: float = 50.0
    ) -> Dict[str, Any]:
        """
        Calculate compatibility scores between candidates and jobs.

        Args:
            top_n_candidates: Number of top candidates to match
            top_n_jobs: Number of jobs to match against
            min_score: Minimum match score threshold (0-100)

        Returns:
            Match analysis with scores and recommendations
        """
        logger.info(f"🔗 Calculating matches: top {top_n_candidates} candidates × {top_n_jobs} jobs...")

        # Load data
        candidates_df = self.stats_engine.load_candidates()
        jobs_df = self.stats_engine.load_jobs()

        if candidates_df.empty or jobs_df.empty:
            return {'error': 'Insufficient data for matching'}

        # Build features
        candidate_features = self.feature_builder.build_candidate_features(
            candidates_df.head(top_n_candidates)
        )
        job_features = self.feature_builder.build_job_features(
            jobs_df.head(top_n_jobs)
        )

        # Calculate matches
        matches_df = self.feature_builder.batch_calculate_matches(
            candidate_features, job_features
        )

        # Filter by minimum score
        matches_df = matches_df[matches_df['match_score'] >= min_score]

        # Statistical analysis of matches
        match_stats = {
            'total_combinations': len(candidate_features) * len(job_features),
            'matches_above_threshold': len(matches_df),
            'match_rate': (len(matches_df) / (len(candidate_features) * len(job_features))) * 100,
            'avg_match_score': float(matches_df['match_score'].mean()) if not matches_df.empty else 0,
            'median_match_score': float(matches_df['match_score'].median()) if not matches_df.empty else 0,
            'top_score': float(matches_df['match_score'].max()) if not matches_df.empty else 0,
            'min_threshold': min_score
        }

        # Top matches
        top_matches = matches_df.nlargest(20, 'match_score').to_dict('records')

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'top_n_candidates': top_n_candidates,
                'top_n_jobs': top_n_jobs,
                'min_score': min_score
            },
            'statistics': match_stats,
            'top_matches': top_matches,
            'insights': self._generate_matching_insights(match_stats, matches_df)
        }

        # Save analysis
        filename = f"candidate_job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats_engine.save_analysis(filename, analysis)

        logger.info(f"✅ Matching complete: {len(matches_df)} matches above {min_score} threshold")
        return analysis

    def _generate_matching_insights(self, stats: Dict, matches_df: pd.DataFrame) -> List[str]:
        """Generate insights from matching analysis."""
        insights = []

        match_rate = stats['match_rate']
        if match_rate < 10:
            insights.append(f"⚠️ Low match rate ({match_rate:.1f}%) - consider relaxing requirements or expanding candidate pool")
        elif match_rate > 30:
            insights.append(f"✅ Strong match rate ({match_rate:.1f}%) - good alignment between candidates and opportunities")

        avg_score = stats['avg_match_score']
        if avg_score < 60:
            insights.append(f"📊 Average match score low ({avg_score:.1f}/100) - skill gap analysis recommended")
        elif avg_score > 75:
            insights.append(f"💡 High average match ({avg_score:.1f}/100) - excellent candidate-job alignment")

        return insights

    # ==================== A/B TESTING ====================

    def run_ab_test(
        self,
        group_a_data: List[float],
        group_b_data: List[float],
        test_name: str,
        metric_name: str
    ) -> Dict[str, Any]:
        """
        Run A/B test with statistical significance testing.

        Args:
            group_a_data: Metrics for control group
            group_b_data: Metrics for test group
            test_name: Name of the A/B test
            metric_name: Name of metric being tested

        Returns:
            A/B test results with statistical analysis
        """
        logger.info(f"🧪 Running A/B test: {test_name} - {metric_name}")

        # Run T-test
        t_test_result = self.stats_engine.compare_resume_quality(group_a_data, group_b_data)

        # Calculate additional metrics
        improvement = ((t_test_result['group_b_mean'] - t_test_result['group_a_mean']) /
                      t_test_result['group_a_mean'] * 100)

        # Determine significance and recommendation
        if t_test_result['significant']:
            if improvement > 0:
                recommendation = f"✅ IMPLEMENT: Group B shows {improvement:.1f}% improvement (p={t_test_result['p_value']:.4f})"
            else:
                recommendation = f"❌ REJECT: Group B shows {abs(improvement):.1f}% decline (p={t_test_result['p_value']:.4f})"
        else:
            recommendation = f"⚠️ INCONCLUSIVE: No significant difference (p={t_test_result['p_value']:.4f}) - need more data"

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'metric_name': metric_name,
            'group_a': {
                'n': len(group_a_data),
                'mean': t_test_result['group_a_mean'],
                'std': t_test_result['std_a']
            },
            'group_b': {
                'n': len(group_b_data),
                'mean': t_test_result['group_b_mean'],
                'std': t_test_result['std_b']
            },
            'test_results': t_test_result,
            'improvement_pct': improvement,
            'recommendation': recommendation
        }

        # Save analysis
        filename = f"ab_test_{test_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats_engine.save_analysis(filename, analysis)

        logger.info(f"✅ A/B test complete: {recommendation}")
        return analysis

    # ==================== PREDICTIVE ANALYTICS ====================

    def predict_callback_probability(
        self,
        candidate_features: pd.DataFrame,
        formula: str = "callbacks_received ~ years_experience + education_score + skills_count"
    ) -> Dict[str, Any]:
        """
        Build predictive model for callback probability.

        Args:
            candidate_features: DataFrame with candidate features
            formula: R-style regression formula

        Returns:
            Regression model results and predictions
        """
        logger.info("🔮 Building callback prediction model...")

        # Run regression
        regression_result = self.stats_engine.predict_callback_rate(
            candidate_features, formula
        )

        # Generate insights
        insights = []
        for coef_name, p_value in regression_result['p_values'].items():
            if p_value < 0.05 and coef_name != 'Intercept':
                coef_value = regression_result['coefficients'][coef_name]
                direction = "increases" if coef_value > 0 else "decreases"
                insights.append(f"📊 {coef_name} significantly {direction} callbacks (p={p_value:.4f})")

        if regression_result['r_squared'] < 0.3:
            insights.append("⚠️ Low R² - model explains limited variance, consider additional features")
        elif regression_result['r_squared'] > 0.7:
            insights.append("✅ Strong R² - model has good predictive power")

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'formula': formula,
            'regression_results': regression_result,
            'insights': insights,
            'model_quality': 'Good' if regression_result['r_squared'] > 0.5 else 'Moderate' if regression_result['r_squared'] > 0.3 else 'Poor'
        }

        # Save analysis
        filename = f"callback_prediction_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats_engine.save_analysis(filename, analysis)

        logger.info(f"✅ Prediction model built: R²={regression_result['r_squared']:.4f}")
        return analysis

    # ==================== SAVED ANALYSES ====================

    def list_recent_analyses(self, limit: int = 20) -> List[Dict]:
        """
        List recent saved analyses.

        Args:
            limit: Maximum number of analyses to return

        Returns:
            List of analysis metadata
        """
        return self.stats_engine.list_saved_analyses()[:limit]

    def load_saved_analysis(self, filename: str) -> Dict:
        """
        Load a previously saved analysis.

        Args:
            filename: Name of saved analysis file

        Returns:
            Analysis results
        """
        return self.stats_engine.load_analysis(filename)


# ==================== SINGLETON ACCESS ====================

_advanced_analytics_service = None

def get_advanced_analytics_service(data_dir: Path = None) -> AdvancedAnalyticsService:
    """Get singleton instance of Advanced Analytics Service."""
    global _advanced_analytics_service
    if _advanced_analytics_service is None:
        _advanced_analytics_service = AdvancedAnalyticsService(data_dir=data_dir)
    return _advanced_analytics_service
