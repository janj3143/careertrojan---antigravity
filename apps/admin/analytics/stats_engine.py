"""
Zero-Cost Statistical Analysis Engine for IntelliCV
Integrates with Hybrid AI Engine for advanced analytics
Uses: scipy, statsmodels, pandas (all free)
"""
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from typing import Dict, List, Any, Optional, Tuple
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ZeroCostStatsEngine:
    """
    Free statistical analysis for IntelliCV candidate/job data.
    No cloud costs - runs locally or in existing container.
    Integrates with Hybrid AI Engine for enhanced intelligence.
    """

    def __init__(self, data_dir: Path = None, results_dir: Path = None):
        """
        Initialize the statistical engine.

        Args:
            data_dir: Directory containing AI data (default: ai_data_final)
            results_dir: Directory to save results (default: working_copy/stats_results)
        """
        if data_dir is None:
            data_dir = Path("ai_data_final")
        if results_dir is None:
            results_dir = Path("working_copy/stats_results")

        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📊 Stats Engine initialized - Data: {self.data_dir}, Results: {self.results_dir}")

    # ========== DATA LOADING (FREE) ==========

    def load_candidates(self) -> pd.DataFrame:
        """Load candidate database from JSON."""
        candidates_path = self.data_dir / "candidates_database.json"
        if candidates_path.exists():
            with open(candidates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
            logger.info(f"✅ Loaded {len(df)} candidates")
            return df
        else:
            logger.warning(f"⚠️ Candidates file not found: {candidates_path}")
            return pd.DataFrame()

    def load_jobs(self) -> pd.DataFrame:
        """Load jobs database from JSON."""
        jobs_path = self.data_dir / "scraped_jobs.json"
        if jobs_path.exists():
            with open(jobs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
            logger.info(f"✅ Loaded {len(df)} jobs")
            return df
        else:
            logger.warning(f"⚠️ Jobs file not found: {jobs_path}")
            return pd.DataFrame()

    def load_companies(self) -> pd.DataFrame:
        """Load companies database from JSON."""
        companies_path = self.data_dir / "companies_database.json"
        if companies_path.exists():
            with open(companies_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
            logger.info(f"✅ Loaded {len(df)} companies")
            return df
        else:
            logger.warning(f"⚠️ Companies file not found: {companies_path}")
            return pd.DataFrame()

    # ========== DESCRIPTIVE STATISTICS (FREE) ==========

    def describe_candidate_pool(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Pandas-based descriptive statistics (FREE).
        Example: Mean salary expectations, experience distribution

        Args:
            df: DataFrame to analyze (if None, loads from candidates_database.json)

        Returns:
            Dictionary containing summary stats, correlations, value counts
        """
        if df is None:
            df = self.load_candidates()

        if df.empty:
            return {'error': 'No data available'}

        # Numeric columns only for correlation
        numeric_df = df.select_dtypes(include=[np.number])

        result = {
            'shape': df.shape,
            'total_records': len(df),
            'columns': list(df.columns),
            'numeric_summary': {},
            'categorical_summary': {},
            'correlations': numeric_df.corr().to_dict() if not numeric_df.empty else {},
            'value_counts': {},
            'missing_data': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.astype(str).to_dict()
        }

        # Numeric columns summary
        for col in numeric_df.columns:
            result['numeric_summary'][col] = {
                'mean': float(numeric_df[col].mean()),
                'median': float(numeric_df[col].median()),
                'std': float(numeric_df[col].std()),
                'min': float(numeric_df[col].min()),
                'max': float(numeric_df[col].max()),
                'count': int(numeric_df[col].count())
            }

        # Value counts for categorical columns
        categorical_cols = df.select_dtypes(include='object').columns
        for col in categorical_cols[:10]:  # Limit to first 10 categorical columns
            try:
                result['value_counts'][col] = df[col].value_counts().head(20).to_dict()
            except Exception as e:
                logger.warning(f"Could not get value counts for {col}: {e}")

        logger.info(f"📊 Descriptive analysis complete for {len(df)} records")
        return result

    # ========== HYPOTHESIS TESTING (scipy - FREE) ==========

    def compare_resume_quality(self, group_a: List[float], group_b: List[float]) -> Dict[str, Any]:
        """
        T-test: Does resume format A get more callbacks than format B?
        Uses: scipy.stats.ttest_ind (FREE)

        Args:
            group_a: Callback rates for format A
            group_b: Callback rates for format B

        Returns:
            Test statistics and interpretation
        """
        if len(group_a) < 2 or len(group_b) < 2:
            return {'error': 'Need at least 2 samples per group'}

        t_stat, p_value = stats.ttest_ind(group_a, group_b)

        result = {
            'test': 'Independent T-Test',
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': p_value < 0.05,
            'interpretation': 'Significant difference' if p_value < 0.05 else 'No significant difference',
            'group_a_mean': float(np.mean(group_a)),
            'group_b_mean': float(np.mean(group_b)),
            'mean_difference': float(np.mean(group_b) - np.mean(group_a)),
            'std_a': float(np.std(group_a)),
            'std_b': float(np.std(group_b)),
            'n_a': len(group_a),
            'n_b': len(group_b),
            'confidence_level': 0.95
        }

        logger.info(f"🧪 T-test: p={p_value:.4f}, significant={result['significant']}")
        return result

    def test_salary_variance(self, *groups: List[float]) -> Dict[str, Any]:
        """
        ANOVA: Do salaries differ across job categories?
        Uses: scipy.stats.f_oneway (FREE)

        Args:
            *groups: Multiple salary groups to compare

        Returns:
            ANOVA F-statistic and p-value
        """
        if len(groups) < 2:
            return {'error': 'Need at least 2 groups for ANOVA'}

        # Filter out empty groups
        valid_groups = [g for g in groups if len(g) > 0]
        if len(valid_groups) < 2:
            return {'error': 'Need at least 2 non-empty groups'}

        f_stat, p_value = stats.f_oneway(*valid_groups)

        result = {
            'test': 'One-Way ANOVA',
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            'significant': p_value < 0.05,
            'group_means': [float(np.mean(g)) for g in valid_groups],
            'group_stds': [float(np.std(g)) for g in valid_groups],
            'group_sizes': [len(g) for g in valid_groups],
            'num_groups': len(valid_groups)
        }

        logger.info(f"🧪 ANOVA: F={f_stat:.4f}, p={p_value:.4f}")
        return result

    def chi_square_test(self, observed: List[int], expected: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Chi-square test for categorical data.

        Args:
            observed: Observed frequencies
            expected: Expected frequencies (if None, assumes uniform)

        Returns:
            Chi-square statistic and p-value
        """
        if expected is None:
            expected = [sum(observed) / len(observed)] * len(observed)

        chi2_stat, p_value = stats.chisquare(observed, expected)

        result = {
            'test': 'Chi-Square Goodness of Fit',
            'chi2_statistic': float(chi2_stat),
            'p_value': float(p_value),
            'significant': p_value < 0.05,
            'degrees_of_freedom': len(observed) - 1,
            'observed': observed,
            'expected': expected
        }

        logger.info(f"🧪 Chi-square: χ²={chi2_stat:.4f}, p={p_value:.4f}")
        return result

    # ========== REGRESSION ANALYSIS (statsmodels - FREE) ==========

    def predict_callback_rate(self, df: pd.DataFrame, formula: str) -> Dict[str, Any]:
        """
        OLS Regression: What predicts getting interview callbacks?
        Uses: statsmodels.formula.api.ols (FREE)

        Args:
            df: DataFrame with variables
            formula: R-style formula (e.g., 'callbacks ~ experience + education + skills_count')

        Returns:
            Regression results
        """
        try:
            model = ols(formula, data=df).fit()

            result = {
                'model': 'OLS Regression',
                'formula': formula,
                'r_squared': float(model.rsquared),
                'adj_r_squared': float(model.rsquared_adj),
                'f_statistic': float(model.fvalue),
                'f_pvalue': float(model.f_pvalue),
                'coefficients': model.params.to_dict(),
                'p_values': model.pvalues.to_dict(),
                'std_errors': model.bse.to_dict(),
                'conf_int': model.conf_int().to_dict(),
                'n_observations': int(model.nobs),
                'summary': str(model.summary())
            }

            logger.info(f"📈 OLS Regression: R²={model.rsquared:.4f}")
            return result

        except Exception as e:
            logger.error(f"❌ Regression failed: {e}")
            return {'error': str(e)}

    def logistic_regression_job_offer(self, df: pd.DataFrame, formula: str) -> Dict[str, Any]:
        """
        Logistic Regression: What predicts getting a job offer (binary)?
        Uses: statsmodels Logit (FREE)

        Args:
            df: DataFrame with variables
            formula: R-style formula (e.g., 'got_offer ~ resume_score + interview_performance')

        Returns:
            Logistic regression results
        """
        try:
            from statsmodels.formula.api import logit

            model = logit(formula, data=df).fit()

            result = {
                'model': 'Logistic Regression',
                'formula': formula,
                'pseudo_r_squared': float(model.prsquared),
                'coefficients': model.params.to_dict(),
                'odds_ratios': np.exp(model.params).to_dict(),
                'p_values': model.pvalues.to_dict(),
                'std_errors': model.bse.to_dict(),
                'n_observations': int(model.nobs),
                'summary': str(model.summary())
            }

            logger.info(f"📈 Logistic Regression: Pseudo R²={model.prsquared:.4f}")
            return result

        except Exception as e:
            logger.error(f"❌ Logistic regression failed: {e}")
            return {'error': str(e)}

    # ========== CORRELATION ANALYSIS (FREE) ==========

    def find_skill_correlations(self, df: pd.DataFrame, skills: Optional[List[str]] = None,
                                threshold: float = 0.5) -> Dict[str, Any]:
        """
        Correlation matrix: Which skills appear together?
        Uses: pandas.DataFrame.corr() (FREE)

        Args:
            df: DataFrame with skill columns (binary or numeric)
            skills: List of skill column names (if None, uses all numeric columns)
            threshold: Minimum correlation strength to report

        Returns:
            Correlation matrix and strong pairs
        """
        if skills is None:
            # Use all numeric columns
            skill_matrix = df.select_dtypes(include=[np.number])
        else:
            skill_matrix = df[skills]

        if skill_matrix.empty:
            return {'error': 'No numeric columns found'}

        corr_matrix = skill_matrix.corr()

        # Find strongest correlations
        strong_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if not np.isnan(corr_value) and abs(corr_value) > threshold:
                    strong_pairs.append({
                        'skill_1': corr_matrix.columns[i],
                        'skill_2': corr_matrix.columns[j],
                        'correlation': float(corr_value),
                        'strength': 'strong' if abs(corr_value) > 0.7 else 'moderate'
                    })

        result = {
            'correlation_matrix': corr_matrix.to_dict(),
            'strong_correlations': sorted(strong_pairs, key=lambda x: abs(x['correlation']), reverse=True),
            'threshold': threshold,
            'num_variables': len(corr_matrix.columns)
        }

        logger.info(f"🔗 Found {len(strong_pairs)} strong correlations")
        return result

    # ========== DISTRIBUTION FITTING (scipy - FREE) ==========

    def fit_salary_distribution(self, salaries: List[float]) -> Dict[str, Any]:
        """
        Fit salary data to statistical distributions.
        Uses: scipy.stats distributions (FREE)

        Args:
            salaries: List of salary values

        Returns:
            Distribution fitting results
        """
        if len(salaries) < 10:
            return {'error': 'Need at least 10 data points for distribution fitting'}

        # Clean data
        salaries_clean = [s for s in salaries if not np.isnan(s) and s > 0]

        if len(salaries_clean) < 10:
            return {'error': 'Insufficient valid data after cleaning'}

        # Try common distributions
        distributions = {
            'normal': stats.norm,
            'lognormal': stats.lognorm,
            'gamma': stats.gamma
        }

        results = {}
        for name, dist in distributions.items():
            try:
                params = dist.fit(salaries_clean)

                # Create a frozen distribution with fitted parameters
                frozen_dist = dist(*params)

                # Kolmogorov-Smirnov test
                ks_stat, p_value = stats.kstest(salaries_clean, frozen_dist.cdf)

                results[name] = {
                    'parameters': [float(p) for p in params],
                    'ks_statistic': float(ks_stat),
                    'p_value': float(p_value),
                    'good_fit': p_value > 0.05,
                    'mean': float(np.mean(salaries_clean)),
                    'median': float(np.median(salaries_clean)),
                    'std': float(np.std(salaries_clean))
                }
            except Exception as e:
                logger.warning(f"Could not fit {name} distribution: {e}")
                results[name] = {'error': str(e)}

        logger.info(f"📊 Distribution fitting complete for {len(salaries_clean)} values")
        return results

    # ========== TIME SERIES ANALYSIS (statsmodels - FREE) ==========

    def analyze_application_trends(self, df: pd.DataFrame, date_col: str,
                                   value_col: str, period: int = 7) -> Dict[str, Any]:
        """
        Time series analysis: Are applications increasing/decreasing?
        Uses: statsmodels.tsa (FREE)

        Args:
            df: DataFrame with time series data
            date_col: Name of date column
            value_col: Name of value column to analyze
            period: Seasonality period (default: 7 for weekly)

        Returns:
            Time series decomposition results
        """
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose

            # Prepare time series
            ts_df = df.copy()
            ts_df[date_col] = pd.to_datetime(ts_df[date_col])
            ts_df = ts_df.sort_values(date_col)
            ts = ts_df.set_index(date_col)[value_col]

            # Remove NaN values
            ts = ts.dropna()

            if len(ts) < period * 2:
                return {'error': f'Need at least {period * 2} data points for period={period}'}

            # Decompose
            decomposition = seasonal_decompose(ts, model='additive', period=period, extrapolate_trend='freq')

            result = {
                'trend': decomposition.trend.dropna().to_dict(),
                'seasonal': decomposition.seasonal.dropna().to_dict(),
                'residual': decomposition.resid.dropna().to_dict(),
                'observed': ts.to_dict(),
                'statistics': {
                    'mean': float(ts.mean()),
                    'std': float(ts.std()),
                    'min': float(ts.min()),
                    'max': float(ts.max())
                },
                'period': period,
                'n_observations': len(ts)
            }

            logger.info(f"📈 Time series analysis complete for {len(ts)} observations")
            return result

        except Exception as e:
            logger.error(f"❌ Time series analysis failed: {e}")
            return {'error': str(e)}

    # ========== SAVE RESULTS (FILE-BASED - FREE) ==========

    def save_analysis(self, analysis_name: str, results: Dict[str, Any]) -> Path:
        """
        Save results to JSON (no database needed - FREE).

        Args:
            analysis_name: Name of the analysis
            results: Results dictionary to save

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{analysis_name}_{timestamp}.json"
        filepath = self.results_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"✅ Saved analysis: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Failed to save analysis: {e}")
            raise

    def load_analysis(self, filename: str) -> Dict[str, Any]:
        """Load previously saved analysis results."""
        filepath = self.results_dir / filename

        if not filepath.exists():
            logger.error(f"❌ Analysis file not found: {filepath}")
            return {'error': 'File not found'}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                results = json.load(f)

            logger.info(f"✅ Loaded analysis: {filepath}")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to load analysis: {e}")
            return {'error': str(e)}

    def list_saved_analyses(self) -> List[Dict[str, Any]]:
        """List all saved analysis files."""
        if not self.results_dir.exists():
            return []

        analyses = []
        for filepath in sorted(self.results_dir.glob('*.json'), reverse=True):
            analyses.append({
                'filename': filepath.name,
                'path': str(filepath),
                'created': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                'size_kb': filepath.stat().st_size / 1024
            })

        logger.info(f"📂 Found {len(analyses)} saved analyses")
        return analyses

    # ========== INTEGRATED AI ANALYSIS ==========

    def analyze_with_ai_integration(self, analysis_type: str = 'full') -> Dict[str, Any]:
        """
        Run comprehensive analysis integrated with Hybrid AI Engine.

        Args:
            analysis_type: 'full', 'quick', or 'custom'

        Returns:
            Combined statistical and AI analysis results
        """
        logger.info(f"🤖 Starting AI-integrated analysis: {analysis_type}")

        results = {
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }

        # Load data
        candidates_df = self.load_candidates()
        jobs_df = self.load_jobs()

        if analysis_type in ['full', 'quick']:
            # Descriptive statistics
            if not candidates_df.empty:
                results['components']['candidate_stats'] = self.describe_candidate_pool(candidates_df)

            if not jobs_df.empty:
                results['components']['job_stats'] = self.describe_candidate_pool(jobs_df)

        if analysis_type == 'full':
            # Advanced analyses
            # Correlation analysis
            if not candidates_df.empty:
                numeric_cols = candidates_df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 1:
                    results['components']['correlations'] = self.find_skill_correlations(
                        candidates_df,
                        list(numeric_cols)
                    )

        # Save results
        save_path = self.save_analysis(f'ai_integrated_{analysis_type}', results)
        results['saved_to'] = str(save_path)

        logger.info(f"✅ AI-integrated analysis complete")
        return results


# Singleton instance for easy access
_engine_instance = None


def get_stats_engine() -> ZeroCostStatsEngine:
    """Get or create the singleton stats engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ZeroCostStatsEngine()
    return _engine_instance
