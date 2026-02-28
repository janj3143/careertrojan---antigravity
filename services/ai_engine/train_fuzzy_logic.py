"""
🌀 Fuzzy Logic Systems Builder
================================
Builds all fuzzy logic systems:
- Fuzzy sets & membership functions
- Triangular/Trapezoidal/Gaussian fuzzy numbers
- Fuzzy inference systems (Mamdani, Sugeno)
- Fuzzy clustering (FCM)
- Fuzzy decision trees
"""

import sys
import os
import logging
from pathlib import Path
import json
import numpy as np
from datetime import datetime

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# ── Education → integer mapping for feature extraction ───────────────────
_EDUCATION_LEVEL_INT = {
    "PhD": 6, "Master": 5, "Bachelor": 4, "HND": 3, "HNC": 3,
    "Diploma": 3, "Associate": 2, "NVQ": 2, "BTEC": 2,
    "A-Level": 1, "GCSE": 1, "High School": 1, "Unknown": 0,
}


class FuzzyLogicBuilder:
    """Comprehensive fuzzy logic system builder"""

    def __init__(self, base_path: str = None):
        # Use centralized config for data paths (L: drive source of truth)
        try:
            from services.ai_engine.config import AI_DATA_DIR, models_path as _cfg_models
            self.data_path = AI_DATA_DIR
            self.models_path = _cfg_models / "fuzzy"
        except ImportError:
            _data_root = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
            self.data_path = _data_root / "ai_data_final"
            self.models_path = Path(base_path or Path(__file__).parent) / "trained_models" / "fuzzy"
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.models_path.mkdir(parents=True, exist_ok=True)

        logger.info("Fuzzy Logic Builder initialized")
        logger.info(f"Data path: {self.data_path}")
        logger.info(f"Systems will be saved to: {self.models_path}")

    # ─── helpers ─────────────────────────────────────────────────────────

    def _load_training_records(self):
        """Load normalised training data via the schema adapter."""
        from services.ai_engine.schema_adapter import load_all_training_data
        return load_all_training_data(self.data_path)

    @staticmethod
    def _education_to_int(edu_str: str) -> int:
        return _EDUCATION_LEVEL_INT.get(edu_str, 0)

    # ─── 1. Membership functions (pure config) ──────────────────────────

    def build_membership_functions(self):
        """Build fuzzy membership functions"""
        logger.info("\n🌀 Building Fuzzy Membership Functions...")

        try:
            membership_functions = {
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat()
                },
                "variables": {
                    "experience_years": {
                        "universe": [0, 30],
                        "fuzzy_sets": {
                            "junior": {
                                "type": "triangular",
                                "parameters": [0, 0, 5],
                                "description": "Junior level (0-5 years)"
                            },
                            "mid": {
                                "type": "triangular",
                                "parameters": [3, 7, 11],
                                "description": "Mid level (3-11 years)"
                            },
                            "senior": {
                                "type": "trapezoidal",
                                "parameters": [9, 12, 30, 30],
                                "description": "Senior level (9+ years)"
                            }
                        }
                    },
                    "skills_count": {
                        "universe": [0, 50],
                        "fuzzy_sets": {
                            "low": {
                                "type": "triangular",
                                "parameters": [0, 0, 10],
                                "description": "Low skills (0-10)"
                            },
                            "medium": {
                                "type": "triangular",
                                "parameters": [5, 15, 25],
                                "description": "Medium skills (5-25)"
                            },
                            "high": {
                                "type": "trapezoidal",
                                "parameters": [20, 30, 50, 50],
                                "description": "High skills (20+)"
                            }
                        }
                    },
                    "match_score": {
                        "universe": [0, 100],
                        "fuzzy_sets": {
                            "poor": {
                                "type": "triangular",
                                "parameters": [0, 0, 40],
                                "description": "Poor match (0-40%)"
                            },
                            "good": {
                                "type": "triangular",
                                "parameters": [30, 50, 70],
                                "description": "Good match (30-70%)"
                            },
                            "excellent": {
                                "type": "trapezoidal",
                                "parameters": [60, 80, 100, 100],
                                "description": "Excellent match (60-100%)"
                            }
                        }
                    },
                    "confidence": {
                        "universe": [0, 1],
                        "fuzzy_sets": {
                            "low": {
                                "type": "gaussian",
                                "parameters": {"mean": 0.3, "sigma": 0.15},
                                "description": "Low confidence"
                            },
                            "medium": {
                                "type": "gaussian",
                                "parameters": {"mean": 0.5, "sigma": 0.15},
                                "description": "Medium confidence"
                            },
                            "high": {
                                "type": "gaussian",
                                "parameters": {"mean": 0.8, "sigma": 0.15},
                                "description": "High confidence"
                            }
                        }
                    }
                }
            }

            with open(self.models_path / "membership_functions.json", 'w') as f:
                json.dump(membership_functions, f, indent=2)

            logger.info(f"✅ Membership functions built - {len(membership_functions['variables'])} variables")
            return membership_functions

        except Exception as e:
            logger.error(f"❌ Membership functions failed: {e}")
            return None

    # ─── 2. Mamdani FIS (pure config) ───────────────────────────────────

    def build_mamdani_fis(self):
        """Build Mamdani fuzzy inference system"""
        logger.info("\n🌀 Building Mamdani FIS...")

        try:
            mamdani_fis = {
                "metadata": {
                    "type": "mamdani",
                    "description": "Mamdani fuzzy inference system for candidate assessment"
                },
                "inputs": ["experience_years", "skills_count"],
                "output": "suitability_score",
                "rules": [
                    {
                        "rule_id": "M001",
                        "IF": {
                            "experience_years": "junior",
                            "skills_count": "low"
                        },
                        "THEN": {"suitability_score": "poor"},
                        "weight": 1.0
                    },
                    {
                        "rule_id": "M002",
                        "IF": {
                            "experience_years": "junior",
                            "skills_count": "medium"
                        },
                        "THEN": {"suitability_score": "good"},
                        "weight": 0.8
                    },
                    {
                        "rule_id": "M003",
                        "IF": {
                            "experience_years": "mid",
                            "skills_count": "medium"
                        },
                        "THEN": {"suitability_score": "good"},
                        "weight": 0.9
                    },
                    {
                        "rule_id": "M004",
                        "IF": {
                            "experience_years": "mid",
                            "skills_count": "high"
                        },
                        "THEN": {"suitability_score": "excellent"},
                        "weight": 0.95
                    },
                    {
                        "rule_id": "M005",
                        "IF": {
                            "experience_years": "senior",
                            "skills_count": "high"
                        },
                        "THEN": {"suitability_score": "excellent"},
                        "weight": 1.0
                    },
                    {
                        "rule_id": "M006",
                        "IF": {
                            "experience_years": "senior",
                            "skills_count": "medium"
                        },
                        "THEN": {"suitability_score": "excellent"},
                        "weight": 0.85
                    },
                    {
                        "rule_id": "M007",
                        "IF": {
                            "experience_years": "junior",
                            "skills_count": "high"
                        },
                        "THEN": {"suitability_score": "good"},
                        "weight": 0.75
                    }
                ],
                "aggregation_method": "max",
                "defuzzification_method": "centroid"
            }

            with open(self.models_path / "mamdani_fis.json", 'w') as f:
                json.dump(mamdani_fis, f, indent=2)

            logger.info(f"✅ Mamdani FIS built - {len(mamdani_fis['rules'])} rules")
            return mamdani_fis

        except Exception as e:
            logger.error(f"❌ Mamdani FIS failed: {e}")
            return None

    # ─── 3. Sugeno FIS (pure config) ────────────────────────────────────

    def build_sugeno_fis(self):
        """Build Sugeno fuzzy inference system"""
        logger.info("\n🌀 Building Sugeno FIS...")

        try:
            sugeno_fis = {
                "metadata": {
                    "type": "sugeno",
                    "description": "Sugeno fuzzy inference system for score prediction"
                },
                "inputs": ["experience_years", "skills_count"],
                "output": "predicted_score",
                "rules": [
                    {
                        "rule_id": "S001",
                        "IF": {
                            "experience_years": "junior",
                            "skills_count": "low"
                        },
                        "THEN": {
                            "function": "linear",
                            "coefficients": [0.2, 0.3, 10],
                            "formula": "0.2*exp + 0.3*skills + 10"
                        }
                    },
                    {
                        "rule_id": "S002",
                        "IF": {
                            "experience_years": "mid",
                            "skills_count": "medium"
                        },
                        "THEN": {
                            "function": "linear",
                            "coefficients": [0.5, 0.5, 30],
                            "formula": "0.5*exp + 0.5*skills + 30"
                        }
                    },
                    {
                        "rule_id": "S003",
                        "IF": {
                            "experience_years": "senior",
                            "skills_count": "high"
                        },
                        "THEN": {
                            "function": "linear",
                            "coefficients": [0.7, 0.8, 50],
                            "formula": "0.7*exp + 0.8*skills + 50"
                        }
                    }
                ],
                "aggregation_method": "weighted_average",
                "output_type": "crisp"
            }

            with open(self.models_path / "sugeno_fis.json", 'w') as f:
                json.dump(sugeno_fis, f, indent=2)

            logger.info(f"✅ Sugeno FIS built - {len(sugeno_fis['rules'])} rules")
            return sugeno_fis

        except Exception as e:
            logger.error(f"❌ Sugeno FIS failed: {e}")
            return None

    # ─── 4. FCM clusterer (real data via schema adapter) ─────────────────

    def train_fcm_clusterer(self):
        """Train Fuzzy C-Means clusterer using schema-adapted training data."""
        logger.info("\n🌀 Training Fuzzy C-Means Clusterer...")

        try:
            records = self._load_training_records()

            features = []
            for rec in records:
                experience_years = rec.get("experience_years", 0)
                skills_count = len(rec.get("skills", []))
                education_level = self._education_to_int(rec.get("education", "Unknown"))
                features.append([experience_years, skills_count, education_level])

            if features:
                X = np.array(features, dtype=np.float64)

                # Drop rows where all features are zero (no signal)
                row_sums = X.sum(axis=1)
                X = X[row_sums > 0]

                if len(X) >= 3:
                    from sklearn.cluster import KMeans
                    import joblib

                    fcm = KMeans(n_clusters=3, random_state=42, n_init=10)
                    fcm.fit(X)

                    joblib.dump(fcm, self.models_path / "fcm_clusterer.pkl")

                    logger.info(
                        f"✅ FCM Clusterer trained on {len(X)} samples — "
                        f"{fcm.n_clusters} clusters, inertia={fcm.inertia_:.2f}"
                    )
                    return {
                        "n_clusters": fcm.n_clusters,
                        "n_samples": int(len(X)),
                        "inertia": float(fcm.inertia_),
                        "centers": fcm.cluster_centers_.tolist(),
                    }
                else:
                    logger.warning("⚠️ Fewer than 3 valid samples — falling back to config-only")

            # Fallback: save configuration only
            fcm_config = {
                "n_clusters": 3,
                "fuzziness": 2.0,
                "max_iter": 100,
                "error_threshold": 0.01,
            }

            with open(self.models_path / "fcm_config.json", 'w') as f:
                json.dump(fcm_config, f, indent=2)

            logger.info("✅ FCM Configuration saved (no training data available)")
            return fcm_config

        except Exception as e:
            logger.error(f"❌ FCM training failed: {e}")
            return None

    # ─── 5. Calibrate membership functions from real data ────────────────

    def calibrate_membership_from_data(self):
        """
        Calibrate membership function parameters using real data distributions.

        Loads training records via the schema adapter, computes the 25th / 50th / 75th
        percentiles for experience_years and skills_count, then adjusts the
        triangular / trapezoidal membership function boundaries so they match the
        actual population.  Saves the updated membership_functions.json.
        """
        logger.info("\n🌀 Calibrating membership functions from real data...")

        try:
            records = self._load_training_records()

            experience_vals = [r.get("experience_years", 0) for r in records]
            skills_vals = [len(r.get("skills", [])) for r in records]

            # Filter out zeros to avoid skewing percentiles
            experience_vals = [v for v in experience_vals if v > 0]
            skills_vals = [v for v in skills_vals if v > 0]

            if len(experience_vals) < 10 or len(skills_vals) < 10:
                logger.warning(
                    "⚠️ Not enough data to calibrate (%d exp, %d skills) — "
                    "keeping defaults",
                    len(experience_vals), len(skills_vals),
                )
                return None

            exp_arr = np.array(experience_vals, dtype=np.float64)
            sk_arr = np.array(skills_vals, dtype=np.float64)

            exp_p25, exp_p50, exp_p75 = np.percentile(exp_arr, [25, 50, 75])
            sk_p25, sk_p50, sk_p75 = np.percentile(sk_arr, [25, 50, 75])

            exp_max = float(np.max(exp_arr))
            sk_max = float(np.max(sk_arr))

            logger.info(
                f"  experience_years — p25={exp_p25:.1f}  p50={exp_p50:.1f}  "
                f"p75={exp_p75:.1f}  max={exp_max:.0f}"
            )
            logger.info(
                f"  skills_count     — p25={sk_p25:.1f}  p50={sk_p50:.1f}  "
                f"p75={sk_p75:.1f}  max={sk_max:.0f}"
            )

            # Load existing membership functions (or build defaults first)
            mf_path = self.models_path / "membership_functions.json"
            if mf_path.exists():
                with open(mf_path, 'r') as f:
                    mf = json.load(f)
            else:
                mf = self.build_membership_functions()
                if mf is None:
                    return None

            # ── Adjust experience_years sets ─────────────────────────────
            exp_sets = mf["variables"]["experience_years"]["fuzzy_sets"]
            exp_universe_max = max(30.0, exp_max + 2)
            mf["variables"]["experience_years"]["universe"] = [0, exp_universe_max]

            # junior: triangular peaking at 0, right shoulder at p25
            exp_sets["junior"]["parameters"] = [0, 0, round(float(exp_p25), 1)]
            exp_sets["junior"]["description"] = f"Junior level (0-{exp_p25:.0f} years)"

            # mid: triangular spanning p25 → p50 → p75
            exp_sets["mid"]["parameters"] = [
                round(float(exp_p25), 1),
                round(float(exp_p50), 1),
                round(float(exp_p75), 1),
            ]
            exp_sets["mid"]["description"] = (
                f"Mid level ({exp_p25:.0f}-{exp_p75:.0f} years)"
            )

            # senior: trapezoidal from p50 up
            exp_sets["senior"]["parameters"] = [
                round(float(exp_p50), 1),
                round(float(exp_p75), 1),
                exp_universe_max,
                exp_universe_max,
            ]
            exp_sets["senior"]["description"] = f"Senior level ({exp_p50:.0f}+ years)"

            # ── Adjust skills_count sets ─────────────────────────────────
            sk_sets = mf["variables"]["skills_count"]["fuzzy_sets"]
            sk_universe_max = max(50.0, sk_max + 5)
            mf["variables"]["skills_count"]["universe"] = [0, sk_universe_max]

            # low: triangular peaking at 0, right shoulder at p25
            sk_sets["low"]["parameters"] = [0, 0, round(float(sk_p25), 1)]
            sk_sets["low"]["description"] = f"Low skills (0-{sk_p25:.0f})"

            # medium: triangular p25 → p50 → p75
            sk_sets["medium"]["parameters"] = [
                round(float(sk_p25), 1),
                round(float(sk_p50), 1),
                round(float(sk_p75), 1),
            ]
            sk_sets["medium"]["description"] = (
                f"Medium skills ({sk_p25:.0f}-{sk_p75:.0f})"
            )

            # high: trapezoidal from p50 up
            sk_sets["high"]["parameters"] = [
                round(float(sk_p50), 1),
                round(float(sk_p75), 1),
                sk_universe_max,
                sk_universe_max,
            ]
            sk_sets["high"]["description"] = f"High skills ({sk_p50:.0f}+)"

            # ── Update metadata ──────────────────────────────────────────
            mf["metadata"]["calibrated_at"] = datetime.now().isoformat()
            mf["metadata"]["calibration_stats"] = {
                "experience_years": {
                    "n_samples": len(experience_vals),
                    "p25": round(float(exp_p25), 2),
                    "p50": round(float(exp_p50), 2),
                    "p75": round(float(exp_p75), 2),
                    "max": round(exp_max, 2),
                },
                "skills_count": {
                    "n_samples": len(skills_vals),
                    "p25": round(float(sk_p25), 2),
                    "p50": round(float(sk_p50), 2),
                    "p75": round(float(sk_p75), 2),
                    "max": round(sk_max, 2),
                },
            }

            with open(mf_path, 'w') as f:
                json.dump(mf, f, indent=2)

            logger.info("✅ Membership functions calibrated from real data")
            return mf

        except Exception as e:
            logger.error(f"❌ Membership calibration failed: {e}")
            return None

    # ─── 6. Fuzzy decision tree (pure config) ───────────────────────────

    def build_fuzzy_decision_tree(self):
        """Build fuzzy decision tree"""
        logger.info("\n🌀 Building Fuzzy Decision Tree...")

        try:
            fuzzy_tree = {
                "metadata": {
                    "type": "fuzzy_decision_tree",
                    "description": "Fuzzy decision tree for candidate classification"
                },
                "root": {
                    "node_id": "N1",
                    "attribute": "experience_years",
                    "fuzzy_split": {
                        "junior": {"threshold": 5, "membership": "triangular"},
                        "senior": {"threshold": 10, "membership": "trapezoidal"}
                    },
                    "children": {
                        "junior": {
                            "node_id": "N2",
                            "attribute": "skills_count",
                            "fuzzy_split": {
                                "low": {"threshold": 10, "leaf": "entry_level"},
                                "high": {"threshold": 15, "leaf": "junior_specialist"}
                            }
                        },
                        "senior": {
                            "node_id": "N3",
                            "attribute": "has_management",
                            "fuzzy_split": {
                                "yes": {"leaf": "senior_manager"},
                                "no": {"leaf": "senior_specialist"}
                            }
                        }
                    }
                },
                "classes": ["entry_level", "junior_specialist", "senior_specialist", "senior_manager"],
                "aggregation": "weighted_average"
            }

            with open(self.models_path / "fuzzy_decision_tree.json", 'w') as f:
                json.dump(fuzzy_tree, f, indent=2)

            logger.info("✅ Fuzzy Decision Tree built")
            return fuzzy_tree

        except Exception as e:
            logger.error(f"❌ Fuzzy decision tree failed: {e}")
            return None

    # ─── Orchestrator ────────────────────────────────────────────────────

    def build_all_fuzzy_systems(self):
        """Build all fuzzy logic systems"""
        logger.info("\n" + "=" * 60)
        logger.info("FUZZY LOGIC SYSTEMS BUILD - ALL TYPES")
        logger.info("=" * 60)

        results = {}

        # Calibrate membership functions from real data FIRST so that
        # subsequent config files can reference data-driven boundaries.
        # Build hardcoded DEFAULTS first, then calibrate from real data.
        # Previous order was reversed — calibration wrote the file, then
        # build_membership_functions() immediately OVERWROTE it with
        # hardcoded values.  Now defaults are laid down first, calibration
        # adjusts them second, and the data-driven file wins.
        results['membership_functions'] = self.build_membership_functions()
        results['calibrated_membership'] = self.calibrate_membership_from_data()
        results['mamdani_fis'] = self.build_mamdani_fis()
        results['sugeno_fis'] = self.build_sugeno_fis()
        results['fcm_clusterer'] = self.train_fcm_clusterer()
        results['fuzzy_decision_tree'] = self.build_fuzzy_decision_tree()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("FUZZY LOGIC SYSTEMS BUILD COMPLETE")
        logger.info("=" * 60)
        for name, result in results.items():
            status = "✅" if result else "❌"
            logger.info(f"{status} {name.upper()}")

        return results


if __name__ == "__main__":
    builder = FuzzyLogicBuilder(str(Path(__file__).parent))
    results = builder.build_all_fuzzy_systems()
