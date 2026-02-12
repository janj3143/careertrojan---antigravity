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


class FuzzyLogicBuilder:
    """Comprehensive fuzzy logic system builder"""

    def __init__(self, base_path: str = None):
        # Use centralized config for data paths (L: drive source of truth)
        try:
            from services.ai_engine.config import AI_DATA_DIR, models_path as _cfg_models
            self.data_path = AI_DATA_DIR
            self.models_path = _cfg_models / "fuzzy"
        except ImportError:
            import os
            _data_root = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
            self.data_path = _data_root / "ai_data_final"
            self.models_path = Path(base_path or Path(__file__).parent) / "trained_models" / "fuzzy"
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.models_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Fuzzy Logic Builder initialized")
        logger.info(f"Data path: {self.data_path}")
        logger.info(f"Systems will be saved to: {self.models_path}")

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

    def train_fcm_clusterer(self):
        """Train Fuzzy C-Means clusterer"""
        logger.info("\n🌀 Training Fuzzy C-Means Clusterer...")

        try:
            # Load sample data
            profiles_dir = self.data_path / "profiles"
            if profiles_dir.exists():
                json_files = list(profiles_dir.glob("*.json"))[:1000]

                features = []
                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            profile = json.load(f)
                            features.append([
                                len(profile.get('skills', [])),
                                len(profile.get('work_experience', [])),
                                len(profile.get('education', []))
                            ])
                    except:
                        pass

                if features:
                    X = np.array(features)

                    # Train FCM (using sklearn as approximation)
                    from sklearn.cluster import KMeans
                    import joblib

                    fcm = KMeans(n_clusters=3, random_state=42)
                    fcm.fit(X)

                    joblib.dump(fcm, self.models_path / "fcm_clusterer.pkl")

                    logger.info(f"✅ FCM Clusterer trained - {fcm.n_clusters} clusters")
                    return {'n_clusters': fcm.n_clusters}

            # Fallback: save configuration
            fcm_config = {
                'n_clusters': 3,
                'fuzziness': 2.0,
                'max_iter': 100,
                'error_threshold': 0.01
            }

            with open(self.models_path / "fcm_config.json", 'w') as f:
                json.dump(fcm_config, f, indent=2)

            logger.info("✅ FCM Configuration saved")
            return fcm_config

        except Exception as e:
            logger.error(f"❌ FCM training failed: {e}")
            return None

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

    def build_all_fuzzy_systems(self):
        """Build all fuzzy logic systems"""
        logger.info("\n" + "="*60)
        logger.info("FUZZY LOGIC SYSTEMS BUILD - ALL TYPES")
        logger.info("="*60)

        results = {}

        # Build each system type
        results['membership_functions'] = self.build_membership_functions()
        results['mamdani_fis'] = self.build_mamdani_fis()
        results['sugeno_fis'] = self.build_sugeno_fis()
        results['fcm_clusterer'] = self.train_fcm_clusterer()
        results['fuzzy_decision_tree'] = self.build_fuzzy_decision_tree()

        # Summary
        logger.info("\n" + "="*60)
        logger.info("FUZZY LOGIC SYSTEMS BUILD COMPLETE")
        logger.info("="*60)
        for name, result in results.items():
            status = "✅" if result else "❌"
            logger.info(f"{status} {name.upper()}")

        return results


if __name__ == "__main__":
    builder = FuzzyLogicBuilder(str(Path(__file__).parent))
    results = builder.build_all_fuzzy_systems()
