"""
CareerTrojan — Unified AI Engine (Multi-Engine Aggregator)
===========================================================

The "best-of-breed" orchestrator that:
  1. Loads models from ALL six engine families (Bayesian, Neural, NLP,
     Fuzzy, Statistical, Expert System)
  2. Runs inference across available engines
  3. Aggregates results via confidence-weighted voting / blending
  4. Returns a single EnsembleResult with per-engine breakdown

Public API used by routers and the on-login scoring hook:
    engine = get_engine()                   # module-level singleton
    result = engine.score_candidate(text, skills, experience_years, ...)
    quick  = engine.quick_score(text)       # thin wrapper for login hook

Author: CareerTrojan System
Date:   February 2026
"""

import json
import logging
import os
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("UnifiedAIEngine")

# ── Config ────────────────────────────────────────────────────────────────
try:
    from services.ai_engine.config import AI_DATA_DIR, models_path as MODELS_ROOT
except ImportError:
    _data_root = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
    AI_DATA_DIR = _data_root / "ai_data_final"
    MODELS_ROOT = Path(__file__).parent / "trained_models"


# ══════════════════════════════════════════════════════════════════════════
# Data-classes
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class EngineResult:
    """Result from a single engine."""
    engine: str
    prediction: Any
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleResult:
    """Aggregated result across all engines."""
    # Primary outputs
    predicted_industry: str = "Unknown"
    predicted_seniority: str = "Unknown"
    match_score: float = 0.0           # 0-100
    confidence: float = 0.0            # 0-1

    # C-3 FIX: Per-dimension scoring breakdown
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    quality_tier: str = "Unknown"      # "Elite", "Strong", "Competent", "Developing", "Entry"

    # Per-engine breakdown
    engine_results: Dict[str, EngineResult] = field(default_factory=dict)
    engines_used: int = 0
    engines_available: int = 0

    # Adaptive blend metadata
    adaptive_weights: Dict[str, float] = field(default_factory=dict)

    # Expert System overlay
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Metadata
    reasoning: str = ""
    timestamp: str = ""
    scoring_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicted_industry": self.predicted_industry,
            "predicted_seniority": self.predicted_seniority,
            "match_score": round(self.match_score, 2),
            "confidence": round(self.confidence, 3),
            "dimension_scores": {k: round(v, 2) for k, v in self.dimension_scores.items()},
            "quality_tier": self.quality_tier,
            "engines_used": self.engines_used,
            "engines_available": self.engines_available,
            "adaptive_weights": {k: round(v, 4) for k, v in self.adaptive_weights.items()},
            "engine_breakdown": {
                name: {
                    "prediction": er.prediction,
                    "confidence": round(er.confidence, 3),
                }
                for name, er in self.engine_results.items()
            },
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
            "scoring_ms": round(self.scoring_ms, 1),
        }


# ══════════════════════════════════════════════════════════════════════════
# Engine Loaders — each returns a callable or None
# ══════════════════════════════════════════════════════════════════════════

def _load_bayesian() -> Optional[Dict[str, Any]]:
    """Load Bayesian models (tfidf + label_encoder + classifier)."""
    try:
        import joblib
        bay_dir = MODELS_ROOT / "bayesian"
        tfidf_path = bay_dir / "tfidf_vectorizer.pkl"
        le_path = bay_dir / "label_encoder.pkl"

        # Try classifiers in preference order
        classifier_names = [
            "gaussian_naive_bayes.pkl",
            "multinomial_naive_bayes.pkl",
            "bernoulli_naive_bayes.pkl",
            "bayesian_network_model.pkl",
        ]
        clf = None
        clf_name = None
        for name in classifier_names:
            p = bay_dir / name
            if p.exists():
                clf = joblib.load(p)
                clf_name = name.replace(".pkl", "")
                break

        if clf is None or not tfidf_path.exists() or not le_path.exists():
            return None

        tfidf = joblib.load(tfidf_path)
        le = joblib.load(le_path)

        # Check for SVD
        svd = None
        svd_path = bay_dir / "svd_reducer.pkl"
        if svd_path.exists():
            svd = joblib.load(svd_path)

        # Check for industry_encoder
        ie = None
        ie_path = bay_dir / "industry_encoder.pkl"
        if ie_path.exists():
            ie = joblib.load(ie_path)

        logger.info("Bayesian engine loaded: %s", clf_name)
        return {
            "classifier": clf,
            "tfidf": tfidf,
            "label_encoder": le,
            "svd": svd,
            "industry_encoder": ie,
            "name": clf_name,
        }
    except Exception as e:
        logger.warning("Bayesian engine load failed: %s", e)
        return None


def _load_neural() -> Optional[Dict[str, Any]]:
    """Load PyTorch neural network classifier."""
    try:
        import torch
        import joblib
        nn_dir = MODELS_ROOT / "neural"

        model_path = nn_dir / "dnn_classifier.pt"
        meta_path = nn_dir / "dnn_metadata.json"
        tfidf_path = nn_dir / "tfidf_vectorizer.pkl"
        svd_path = nn_dir / "svd_reducer.pkl"
        scaler_path = nn_dir / "feature_scaler.pkl"
        le_path = nn_dir / "label_encoder.pkl"

        if not model_path.exists():
            return None

        # Load metadata for architecture params
        meta = {}
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)

        input_dim = meta.get("input_dim", 54)
        num_classes = meta.get("num_classes", 9)

        # Rebuild architecture
        import torch.nn as nn

        class DNNClassifier(nn.Module):
            def __init__(self, in_dim, n_cls):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(in_dim, 128), nn.ReLU(), nn.Dropout(0.3),
                    nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.2),
                    nn.Linear(64, 32), nn.ReLU(),
                    nn.Linear(32, n_cls),
                )

            def forward(self, x):
                return self.net(x)

        model = DNNClassifier(input_dim, num_classes)
        model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
        model.eval()

        tfidf = joblib.load(tfidf_path) if tfidf_path.exists() else None
        svd = joblib.load(svd_path) if svd_path.exists() else None
        scaler = joblib.load(scaler_path) if scaler_path.exists() else None
        le = joblib.load(le_path) if le_path.exists() else None

        logger.info("Neural engine loaded (DNN %d->%d)", input_dim, num_classes)
        return {
            "model": model,
            "tfidf": tfidf,
            "svd": svd,
            "scaler": scaler,
            "label_encoder": le,
        }
    except Exception as e:
        logger.warning("Neural engine load failed: %s", e)
        return None


def _load_nlp() -> Optional[Dict[str, Any]]:
    """Load NLP text classifier + topic model."""
    try:
        import joblib
        nlp_dir = MODELS_ROOT / "nlp"

        clf_path = nlp_dir / "text_classifier.pkl"
        vec_path = nlp_dir / "text_classifier_vectorizer.pkl"
        topic_path = nlp_dir / "topic_model_lda.pkl"
        topic_vec_path = nlp_dir / "topic_vectorizer.pkl"

        result = {}
        if clf_path.exists() and vec_path.exists():
            result["classifier"] = joblib.load(clf_path)
            result["vectorizer"] = joblib.load(vec_path)

        if topic_path.exists() and topic_vec_path.exists():
            result["topic_model"] = joblib.load(topic_path)
            result["topic_vectorizer"] = joblib.load(topic_vec_path)

        # Try to load label metadata
        meta_path = nlp_dir / "text_classifier_metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                result["metadata"] = json.load(f)

        if result:
            logger.info("NLP engine loaded (%d components)", len(result))
            return result
        return None
    except Exception as e:
        logger.warning("NLP engine load failed: %s", e)
        return None


def _load_fuzzy() -> Optional[Dict[str, Any]]:
    """Load fuzzy inference system configs."""
    try:
        fz_dir = MODELS_ROOT / "fuzzy"
        mf_path = fz_dir / "membership_functions.json"
        mamdani_path = fz_dir / "mamdani_fis.json"

        if not mf_path.exists():
            return None

        with open(mf_path) as f:
            mf = json.load(f)

        mamdani = {}
        if mamdani_path.exists():
            with open(mamdani_path) as f:
                mamdani = json.load(f)

        logger.info("Fuzzy engine loaded (membership functions + Mamdani FIS)")
        return {"membership_functions": mf, "mamdani": mamdani}
    except Exception as e:
        logger.warning("Fuzzy engine load failed: %s", e)
        return None


def _load_statistical() -> Optional[Dict[str, Any]]:
    """Load statistical analysis results for scoring context."""
    try:
        stat_dir = MODELS_ROOT / "statistical"
        analytics_path = AI_DATA_DIR / "analytics" / "statistical_methods_analysis.json"

        result = {}
        if analytics_path.exists():
            with open(analytics_path) as f:
                result["analysis"] = json.load(f)

        # Load any trained statistical models
        import joblib
        for pkl in stat_dir.glob("*.pkl"):
            try:
                result[pkl.stem] = joblib.load(pkl)
            except Exception:
                pass

        if result:
            logger.info("Statistical engine loaded (%d artifacts)", len(result))
            return result
        return None
    except Exception as e:
        logger.warning("Statistical engine load failed: %s", e)
        return None


def _load_expert_system() -> Optional[Dict[str, Any]]:
    """Load the expert system singletons."""
    try:
        from services.ai_engine.expert_system import career_rules, skill_matcher
        logger.info("Expert System engine loaded (career_rules + skill_matcher)")
        return {"career_rules": career_rules, "skill_matcher": skill_matcher}
    except Exception as e:
        logger.warning("Expert System engine load failed: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════════
# Helper utilities
# ══════════════════════════════════════════════════════════════════════════

_EDUCATION_MAP = {
    "phd": 5, "master": 4, "bachelor": 3, "hnd": 2.5, "hnc": 2.5,
    "diploma": 2, "associate": 2, "a-level": 1.5, "gcse": 1,
    "high school": 1, "unknown": 1,
}


def _education_to_int(edu: str) -> int:
    return int(_EDUCATION_MAP.get(edu.lower().strip(), 1))


def _infer_seniority(experience_years: int, skills_count: int) -> str:
    if experience_years >= 10 or skills_count >= 20:
        return "Senior"
    elif experience_years >= 4 or skills_count >= 10:
        return "Mid-Level"
    return "Junior"


def _fuzzy_score(fuzzy_data: Dict, experience_years: int, skills_count: int) -> float:
    """Evaluate Mamdani-style suitability score using loaded membership functions."""
    try:
        mf = fuzzy_data.get("membership_functions", {}).get("variables", {})
        mamdani = fuzzy_data.get("mamdani", {})

        exp_vars = mf.get("experience_years", {}).get("fuzzy_sets", {})
        skill_vars = mf.get("skills_count", {}).get("fuzzy_sets", {})

        def triangular_mf(x, params):
            a, b, c = params
            if x <= a or x >= c:
                return 0.0
            elif x <= b:
                return (x - a) / max(b - a, 1e-9)
            else:
                return (c - x) / max(c - b, 1e-9)

        def trapezoidal_mf(x, params):
            a, b, c, d = params
            if x <= a or x >= d:
                return 0.0
            elif a < x <= b:
                return (x - a) / max(b - a, 1e-9)
            elif b < x <= c:
                return 1.0
            else:
                return (d - x) / max(d - c, 1e-9)

        def eval_mf(x, fset):
            mf_type = fset.get("type", "triangular")
            params = fset.get("parameters", [0, 0, 0])
            if mf_type == "triangular":
                return triangular_mf(x, params)
            elif mf_type == "trapezoidal":
                return trapezoidal_mf(x, params)
            elif mf_type == "gaussian":
                mean = params.get("mean", 0.5) if isinstance(params, dict) else params[0]
                sigma = params.get("sigma", 0.15) if isinstance(params, dict) else params[1]
                return float(np.exp(-0.5 * ((x - mean) / max(sigma, 1e-9)) ** 2))
            return 0.0

        rules = mamdani.get("rules", [])
        if not rules:
            return 50.0

        numerator = 0.0
        denominator = 0.0
        output_centroids = {"poor": 20, "good": 50, "excellent": 85}

        for rule in rules:
            cond = rule.get("IF", {})
            then = rule.get("THEN", {})
            weight = rule.get("weight", 1.0)

            exp_label = cond.get("experience_years", "")
            skill_label = cond.get("skills_count", "")
            out_label = then.get("suitability_score", "")

            exp_deg = eval_mf(experience_years, exp_vars.get(exp_label, {})) if exp_label else 1.0
            skill_deg = eval_mf(skills_count, skill_vars.get(skill_label, {})) if skill_label else 1.0

            firing = min(exp_deg, skill_deg) * weight
            centroid = output_centroids.get(out_label, 50)

            numerator += firing * centroid
            denominator += firing

        return numerator / max(denominator, 1e-9)
    except Exception:
        return 50.0


# ══════════════════════════════════════════════════════════════════════════
# Main Engine Class
# ══════════════════════════════════════════════════════════════════════════

class UnifiedAIEngine:
    """
    Multi-engine aggregator.  Loads all available engines at init time,
    then scores candidates using confidence-weighted ensemble voting.
    """

    DEFAULT_WEIGHTS = {
        "bayesian": 0.30,
        "neural": 0.20,
        "nlp": 0.15,
        "fuzzy": 0.10,
        "statistical": 0.05,
        "expert_system": 0.20,
    }

    def __init__(self):
        self.engines: Dict[str, Any] = {}
        self.weights = dict(self.DEFAULT_WEIGHTS)
        self._loaded = False

    def load_all_engines(self) -> int:
        loaders = {
            "bayesian": _load_bayesian,
            "neural": _load_neural,
            "nlp": _load_nlp,
            "fuzzy": _load_fuzzy,
            "statistical": _load_statistical,
            "expert_system": _load_expert_system,
        }

        for name, loader in loaders.items():
            try:
                result = loader()
                if result is not None:
                    self.engines[name] = result
            except Exception as e:
                logger.warning("Engine '%s' load failed: %s", name, e)

        self._loaded = True
        logger.info(
            "Unified AI Engine: %d / %d engines loaded (%s)",
            len(self.engines), len(loaders),
            ", ".join(sorted(self.engines.keys())),
        )
        return len(self.engines)

    @property
    def available_engines(self) -> List[str]:
        return sorted(self.engines.keys())

    # ── Per-engine inference ─────────────────────────────────────────────

    def _infer_bayesian(self, text: str, **ctx) -> Optional[EngineResult]:
        bay = self.engines.get("bayesian")
        if not bay:
            return None
        try:
            tfidf = bay["tfidf"]
            le = bay["label_encoder"]
            clf = bay["classifier"]
            svd = bay.get("svd")

            X_tfidf = tfidf.transform([text])
            if svd is not None:
                X_svd = svd.transform(X_tfidf)
            else:
                X_svd = X_tfidf.toarray()

            # Scalar features must match training order in prepare_features():
            # [skills_count, experience_years, education_encoded]
            n_skills = ctx.get("skills_count", 0)
            exp_years = ctx.get("experience_years", 0)
            edu_int = ctx.get("education_int", 1)

            scalars = np.array([[n_skills, exp_years, edu_int]])
            X = np.hstack([X_svd, scalars]) if X_svd.shape[1] > 0 else scalars

            pred_idx = clf.predict(X)[0]
            try:
                proba = clf.predict_proba(X)[0]
                confidence = float(np.max(proba))
            except Exception:
                confidence = 0.5

            prediction = le.inverse_transform([pred_idx])[0]

            return EngineResult(
                engine="bayesian",
                prediction=prediction,
                confidence=confidence,
                metadata={"classifier": bay.get("name", "unknown")},
            )
        except Exception as e:
            logger.debug("Bayesian inference error: %s", e)
            return None

    def _infer_neural(self, text: str, **ctx) -> Optional[EngineResult]:
        nn_data = self.engines.get("neural")
        if not nn_data:
            return None
        try:
            import torch
            model = nn_data["model"]
            tfidf = nn_data.get("tfidf")
            svd = nn_data.get("svd")
            scaler = nn_data.get("scaler")
            le = nn_data.get("label_encoder")

            if tfidf is None or le is None:
                return None

            X_tfidf = tfidf.transform([text])
            if svd is not None:
                X_svd = svd.transform(X_tfidf)
            else:
                X_svd = X_tfidf.toarray()

            # Scalar features must match training order in prepare_features():
            # [skills_count, experience_years, education_encoded]
            n_skills = ctx.get("skills_count", 0)
            exp_years = ctx.get("experience_years", 0)
            edu_int = ctx.get("education_int", 1)

            scalars = np.array([[n_skills, exp_years, edu_int]])
            X = np.hstack([X_svd, scalars])

            if scaler is not None:
                X = scaler.transform(X)

            with torch.no_grad():
                logits = model(torch.tensor(X, dtype=torch.float32))
                probs = torch.softmax(logits, dim=1).numpy()[0]

            pred_idx = int(np.argmax(probs))
            confidence = float(probs[pred_idx])
            prediction = le.inverse_transform([pred_idx])[0]

            return EngineResult(
                engine="neural",
                prediction=prediction,
                confidence=confidence,
                metadata={"type": "dnn"},
            )
        except Exception as e:
            logger.debug("Neural inference error: %s", e)
            return None

    def _infer_nlp(self, text: str, **ctx) -> Optional[EngineResult]:
        nlp_data = self.engines.get("nlp")
        if not nlp_data or "classifier" not in nlp_data:
            return None
        try:
            clf = nlp_data["classifier"]
            vec = nlp_data["vectorizer"]

            X = vec.transform([text])
            pred = clf.predict(X)[0]

            try:
                proba = clf.predict_proba(X)[0]
                confidence = float(np.max(proba))
            except Exception:
                confidence = 0.4

            return EngineResult(
                engine="nlp",
                prediction=pred,
                confidence=confidence,
                metadata={},
            )
        except Exception as e:
            logger.debug("NLP inference error: %s", e)
            return None

    def _infer_fuzzy(self, **ctx) -> Optional[EngineResult]:
        fz = self.engines.get("fuzzy")
        if not fz:
            return None
        try:
            exp_years = ctx.get("experience_years", 0)
            n_skills = ctx.get("skills_count", 0)

            score = _fuzzy_score(fz, exp_years, n_skills)
            confidence = min(0.9, 0.4 + abs(score - 50) / 100)

            if score >= 70:
                label = "Excellent"
            elif score >= 45:
                label = "Good"
            else:
                label = "Developing"

            return EngineResult(
                engine="fuzzy",
                prediction=label,
                confidence=confidence,
                metadata={"raw_score": round(score, 2)},
            )
        except Exception as e:
            logger.debug("Fuzzy inference error: %s", e)
            return None

    def _infer_expert(self, **ctx) -> Optional[EngineResult]:
        es = self.engines.get("expert_system")
        if not es:
            return None
        try:
            career_rules = es["career_rules"]
            skill_matcher = es["skill_matcher"]

            rules_ctx = {
                "target_role": ctx.get("job_title", ""),
                "years_experience": ctx.get("experience_years", 0),
                "career_pivot": False,
                "has_relevant_certifications": False,
                "skills": ctx.get("skills", []),
            }
            rules_result = career_rules.evaluate(rules_ctx)

            user_skills = ctx.get("skills", [])
            if user_skills:
                match_result = skill_matcher.score(
                    user_skills=user_skills,
                    role_requirements=user_skills[:5],
                    experience_years=ctx.get("experience_years", 0),
                )
                match_score = match_result.get("overall_score", 0.5)
                grade = match_result.get("grade", "Unknown")
            else:
                match_score = 0.3
                grade = "Unknown"

            confidence_adj = rules_result.get("confidence_adjustment", 0)
            base_confidence = 0.5 + match_score * 0.3 + confidence_adj

            return EngineResult(
                engine="expert_system",
                prediction=grade,
                confidence=max(0.1, min(0.95, base_confidence)),
                metadata={
                    "match_score": round(match_score, 3),
                    "rules_triggered": len(rules_result.get("triggered_rules", [])),
                    "recommendations": rules_result.get("recommendations", []),
                    "warnings": rules_result.get("warnings", []),
                },
            )
        except Exception as e:
            logger.debug("Expert System inference error: %s", e)
            return None

    def _infer_statistical(self, text: str, **ctx) -> Optional[EngineResult]:
        """C-2 FIX: Infer using statistical analysis models.

        Uses kmeans/PCA cluster assignment + logistic regression if available.
        Falls back to heuristic scoring from the pre-computed analysis JSON.
        """
        stat = self.engines.get("statistical")
        if not stat:
            return None
        try:
            import joblib

            # Try trained logistic regression model first
            logreg = stat.get("logistic_regression")
            pca = stat.get("pca_model")
            kmeans = stat.get("kmeans_clusterer")
            analysis = stat.get("analysis", {})

            exp_years = ctx.get("experience_years", 0)
            n_skills = ctx.get("skills_count", 0)
            edu_int = ctx.get("education_int", 1)
            text_len = min(len(text) / 10000, 1.0)

            features = np.array([[exp_years, n_skills, edu_int, text_len]])

            prediction = "Unknown"
            confidence = 0.35

            # Route 1: logistic regression classifier
            if logreg is not None:
                try:
                    pred = logreg.predict(features)[0]
                    try:
                        proba = logreg.predict_proba(features)[0]
                        confidence = float(np.max(proba))
                    except Exception:
                        confidence = 0.45
                    prediction = str(pred)
                except Exception:
                    pass

            # Route 2: k-means cluster label
            elif kmeans is not None:
                try:
                    cluster = int(kmeans.predict(features)[0])
                    # Map cluster to a suitability label
                    n_clusters = getattr(kmeans, "n_clusters", 3)
                    # Use centroid distance as confidence proxy
                    dists = kmeans.transform(features)[0]
                    min_dist = float(np.min(dists))
                    max_dist = float(np.max(dists))
                    confidence = max(0.3, 1.0 - min_dist / max(max_dist, 1e-9))
                    prediction = f"Cluster-{cluster}"
                except Exception:
                    pass

            # Route 3: heuristic from pre-computed analysis JSON
            else:
                stat_analysis = analysis.get("statistical_analysis", analysis)
                corr = stat_analysis.get("correlation", {})
                significant_pairs = corr.get("correlations", [])
                # Use correlation insights as a scoring heuristic
                if exp_years >= 6 and n_skills >= 8:
                    prediction = "Strong"
                    confidence = 0.55
                elif exp_years >= 3 or n_skills >= 5:
                    prediction = "Moderate"
                    confidence = 0.45
                else:
                    prediction = "Developing"
                    confidence = 0.35

            return EngineResult(
                engine="statistical",
                prediction=prediction,
                confidence=confidence,
                metadata={
                    "method": "logreg" if logreg else ("kmeans" if kmeans else "heuristic"),
                    "features": {"exp": exp_years, "skills": n_skills, "edu": edu_int},
                },
            )
        except Exception as e:
            logger.debug("Statistical inference error: %s", e)
            return None

    # ── Adaptive Weight Computation ──────────────────────────────────────

    def _compute_adaptive_weights(
        self, results: Dict[str, EngineResult]
    ) -> Dict[str, float]:
        """Replace hardcoded 70/30 blend with confidence-adaptive weights.

        Each engine's weight is its default weight × its confidence output.
        Engines that didn't fire get weight 0. The result is normalised to
        sum to 1.0 so downstream aggregation is scale-invariant.
        """
        raw: Dict[str, float] = {}
        for name, er in results.items():
            base = self.weights.get(name, 0.1)
            raw[name] = base * er.confidence

        total = sum(raw.values())
        if total < 1e-9:
            # Fallback: equal weight across firing engines
            n = max(len(raw), 1)
            return {k: 1.0 / n for k in raw}

        return {k: v / total for k, v in raw.items()}

    # ── Dimension Scoring ────────────────────────────────────────────────

    @staticmethod
    def _compute_dimension_scores(
        results: Dict[str, EngineResult],
        adaptive_w: Dict[str, float],
        experience_years: int,
        skills_count: int,
        education_int: int,
    ) -> Dict[str, float]:
        """Compute per-dimension 0-100 scores.

        Dimensions:
          - industry_fit:   weighted industry prediction confidence
          - experience:     normalised years (cap 20)
          - skills_breadth: normalised skill count (cap 30)
          - education:      normalised education level
          - ai_confidence:  mean weighted confidence across engines
          - match_quality:  expert system match score (if available)
        """
        dim: Dict[str, float] = {}

        # 1. Industry fit — confidence of the winning industry prediction
        industry_confs = []
        for name, er in results.items():
            if name != "fuzzy":
                industry_confs.append(er.confidence * adaptive_w.get(name, 0.1))
        dim["industry_fit"] = min(100.0, sum(industry_confs) * 100) if industry_confs else 0.0

        # 2. Experience — capped at 20 yrs = 100
        dim["experience"] = min(100.0, (experience_years / 20.0) * 100)

        # 3. Skills breadth — capped at 30 skills = 100
        dim["skills_breadth"] = min(100.0, (skills_count / 30.0) * 100)

        # 4. Education — ordinal 0-5 → 0-100
        dim["education"] = min(100.0, (education_int / 5.0) * 100)

        # 5. AI confidence — mean confidence weighted by adaptive weights
        if results:
            conf_sum = sum(
                er.confidence * adaptive_w.get(name, 0.1) for name, er in results.items()
            )
            weight_sum = sum(adaptive_w.get(name, 0.1) for name in results)
            dim["ai_confidence"] = min(100.0, (conf_sum / max(weight_sum, 1e-9)) * 100)
        else:
            dim["ai_confidence"] = 0.0

        # 6. Match quality — expert system score if available
        expert = results.get("expert_system")
        if expert:
            dim["match_quality"] = expert.metadata.get("match_score", 0.0) * 100
        else:
            dim["match_quality"] = 0.0

        return dim

    @staticmethod
    def _compute_quality_tier(match_score: float, confidence: float) -> str:
        """Map overall match_score + confidence to a quality tier label."""
        composite = match_score * 0.7 + confidence * 100 * 0.3
        if composite >= 85:
            return "Elite"
        elif composite >= 70:
            return "Strong"
        elif composite >= 50:
            return "Competent"
        elif composite >= 30:
            return "Developing"
        return "Entry"

    # ── Aggregation ──────────────────────────────────────────────────────

    def _aggregate_industry(
        self, results: Dict[str, EngineResult], adaptive_w: Dict[str, float]
    ) -> Tuple[str, float]:
        votes: Dict[str, float] = {}
        total_weight = 0.0

        for name, er in results.items():
            if name in ("fuzzy",):
                continue
            w = adaptive_w.get(name, 0.1)
            pred = str(er.prediction)
            votes[pred] = votes.get(pred, 0.0) + w
            total_weight += w

        if not votes:
            return "Unknown", 0.0

        winner = max(votes, key=votes.get)
        confidence = votes[winner] / max(total_weight, 1e-9)
        return winner, min(confidence, 0.99)

    def _aggregate_match_score(
        self, results: Dict[str, EngineResult], adaptive_w: Dict[str, float]
    ) -> float:
        scores = []
        weights = []

        for name, er in results.items():
            w = adaptive_w.get(name, 0.1)
            if name == "fuzzy":
                raw = er.metadata.get("raw_score", 50)
            elif name == "expert_system":
                raw = er.metadata.get("match_score", 0.5) * 100
            else:
                raw = er.confidence * 100
            scores.append(raw)
            weights.append(w)

        if not scores:
            return 0.0

        weights_arr = np.array(weights)
        scores_arr = np.array(scores)
        return float(np.average(scores_arr, weights=weights_arr))

    # ── Public scoring API ───────────────────────────────────────────────

    def score_candidate(
        self,
        text: str,
        skills: Optional[List[str]] = None,
        experience_years: int = 0,
        education: str = "Unknown",
        industry_hint: str = "",
        job_title: str = "",
    ) -> EnsembleResult:
        import time
        t0 = time.perf_counter()

        if not self._loaded:
            self.load_all_engines()

        skills = skills or []
        edu_int = _education_to_int(education)

        ctx = {
            "experience_years": experience_years,
            "skills_count": len(skills),
            "skills": skills,
            "education": education,
            "education_int": edu_int,
            "industry_hint": industry_hint,
            "job_title": job_title,
        }

        engine_results: Dict[str, EngineResult] = {}

        bay_result = self._infer_bayesian(text, **ctx)
        if bay_result:
            engine_results["bayesian"] = bay_result

        nn_result = self._infer_neural(text, **ctx)
        if nn_result:
            engine_results["neural"] = nn_result

        nlp_result = self._infer_nlp(text, **ctx)
        if nlp_result:
            engine_results["nlp"] = nlp_result

        fuzzy_result = self._infer_fuzzy(**ctx)
        if fuzzy_result:
            engine_results["fuzzy"] = fuzzy_result

        expert_result = self._infer_expert(**ctx)
        if expert_result:
            engine_results["expert_system"] = expert_result

        # C-2 FIX: statistical engine was loaded but never called
        stat_result = self._infer_statistical(text, **ctx)
        if stat_result:
            engine_results["statistical"] = stat_result

        # Adaptive confidence-weighted blending (replaces hardcoded 70/30)
        adaptive_w = self._compute_adaptive_weights(engine_results)

        predicted_industry, agg_confidence = self._aggregate_industry(engine_results, adaptive_w)
        match_score = self._aggregate_match_score(engine_results, adaptive_w)
        seniority = _infer_seniority(experience_years, len(skills))

        # C-3 FIX: compute per-dimension scores and quality tier
        dimension_scores = self._compute_dimension_scores(
            engine_results, adaptive_w, experience_years, len(skills), edu_int,
        )
        quality_tier = self._compute_quality_tier(match_score, agg_confidence)

        recommendations = []
        warnings = []
        if expert_result:
            recommendations = expert_result.metadata.get("recommendations", [])
            warnings = expert_result.metadata.get("warnings", [])

        reasoning_parts = []
        for name, er in engine_results.items():
            reasoning_parts.append(
                f"{name.replace('_', ' ').title()}: {er.prediction} ({er.confidence:.0%})"
            )
        reasoning = "Engines: " + " | ".join(reasoning_parts) if reasoning_parts else "No engines available"

        elapsed_ms = (time.perf_counter() - t0) * 1000

        result = EnsembleResult(
            predicted_industry=predicted_industry,
            predicted_seniority=seniority,
            match_score=match_score,
            confidence=agg_confidence,
            dimension_scores=dimension_scores,
            quality_tier=quality_tier,
            engine_results=engine_results,
            engines_used=len(engine_results),
            engines_available=len(self.engines),
            adaptive_weights=adaptive_w,
            recommendations=recommendations,
            warnings=warnings,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat(),
            scoring_ms=elapsed_ms,
        )

        logger.info(
            "Scored candidate: industry=%s conf=%.2f score=%.1f engines=%d/%d (%.0fms)",
            predicted_industry, agg_confidence, match_score,
            len(engine_results), len(self.engines), elapsed_ms,
        )
        return result

    def quick_score(self, text: str) -> Dict[str, Any]:
        """Lightweight scoring for the on-login hook."""
        from services.ai_engine.schema_adapter import (
            _extract_experience_years,
            _extract_education_level,
            _extract_skills_from_text,
            _infer_industry,
        )

        skills = _extract_skills_from_text(text)
        experience_years = _extract_experience_years(text)
        education = _extract_education_level(text)
        industry = _infer_industry(text)

        result = self.score_candidate(
            text=text,
            skills=skills,
            experience_years=experience_years,
            education=education,
            industry_hint=industry,
        )
        return result.to_dict()

    def print_status(self):
        if not self._loaded:
            self.load_all_engines()
        print("\n" + "=" * 70)
        print("UNIFIED AI ENGINE STATUS - MULTI-ENGINE AGGREGATOR")
        print("=" * 70)
        print(f"\nEngines loaded: {len(self.engines)} / {len(self.DEFAULT_WEIGHTS)}")
        for name, weight in self.DEFAULT_WEIGHTS.items():
            loaded = "OK" if name in self.engines else "MISSING"
            print(f"  [{loaded:7s}] {name:20s}  weight={weight:.2f}")
        print("=" * 70 + "\n")

    def test_all_engines(self) -> bool:
        if not self._loaded:
            self.load_all_engines()
        test_text = (
            "Senior Python Developer with 8 years of experience in software engineering. "
            "Expert in Django, FastAPI, microservices architecture. "
            "Experience with AWS, Docker, Kubernetes. "
            "Master's degree in Computer Science. "
            "Led a team of 12 engineers delivering cloud-native solutions."
        )
        print("\nSMOKE TEST - Multi-Engine Aggregator")
        print(f"   Test text: {test_text[:80]}...")

        result = self.score_candidate(
            text=test_text,
            skills=["Python", "Django", "FastAPI", "AWS", "Docker", "Kubernetes"],
            experience_years=8,
            education="Master",
            job_title="Senior Python Developer",
        )
        print(f"   Industry:    {result.predicted_industry}")
        print(f"   Seniority:   {result.predicted_seniority}")
        print(f"   Match Score: {result.match_score:.1f}")
        print(f"   Confidence:  {result.confidence:.1%}")
        print(f"   Engines:     {result.engines_used}/{result.engines_available}")
        print(f"   Time:        {result.scoring_ms:.0f}ms")
        for name, er in result.engine_results.items():
            print(f"      {name:20s}: {er.prediction} ({er.confidence:.1%})")
        print()
        return result.engines_used > 0


# ══════════════════════════════════════════════════════════════════════════
# Module-level singleton
# ══════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[UnifiedAIEngine] = None


def get_engine() -> UnifiedAIEngine:
    """Get or create the singleton UnifiedAIEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = UnifiedAIEngine()
        _engine_instance.load_all_engines()
    return _engine_instance


def main():
    import sys
    engine = get_engine()
    engine.print_status()
    if "--test" in sys.argv:
        success = engine.test_all_engines()
        return 0 if success else 1
    return 0


if __name__ == "__main__":
    exit(main())
