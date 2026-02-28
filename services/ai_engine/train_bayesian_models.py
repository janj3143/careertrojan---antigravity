"""
Bayesian Model Training Module
===================================
Trains all Bayesian inference models using the schema_adapter for
unified data loading from ai_data_final/:

  - Gaussian Naive Bayes
  - Multinomial Naive Bayes
  - Bernoulli Naive Bayes
  - Bayesian Network (DAG + conditional model)
  - Hierarchical Bayesian Model
  - MCMC Sampler (Metropolis-Hastings config + posterior approx.)

Data is loaded via ``schema_adapter.load_all_training_data()`` which
normalises profiles, CV files, parsed resumes, and the merged DB into a
single record format with: text, job_title, skills, experience_years,
education, industry, salary.

Features used for all classifiers:
  - TF-IDF on ``text`` field  (sparse, truncated SVD for dense models)
  - skills_count              (int)
  - experience_years          (int)
  - education_level_encoded   (ordinal int)
  - industry_encoded          (integer-coded category)

Target variable:
  ``industry`` (inferred from data).  ``job_title`` is too sparse /
  high-cardinality for a first-pass Bayesian classifier; industry gives
  a manageable number of classes.

Usage:
    # Standalone
    python train_bayesian_models.py

    # As module
    from services.ai_engine.train_bayesian_models import BayesianModelTrainer
    trainer = BayesianModelTrainer()
    results = trainer.train_all_bayesian()
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import schema_adapter — works both as a standalone script and as a package
# ---------------------------------------------------------------------------
try:
    from schema_adapter import load_all_training_data
except ImportError:
    from services.ai_engine.schema_adapter import load_all_training_data

# ---------------------------------------------------------------------------
# Education ordinal encoding (highest → largest int)
# ---------------------------------------------------------------------------
EDUCATION_ORDINAL: Dict[str, int] = {
    "Unknown":     0,
    "GCSE":        1,
    "A-Level":     2,
    "BTEC":        3,
    "NVQ":         4,
    "HNC":         5,
    "HND":         6,
    "Associate":   7,
    "Diploma":     8,
    "Bachelor":    9,
    "Master":      10,
    "PhD":         11,
}

# Minimum number of samples a class must have to be kept
MIN_CLASS_SAMPLES = 5


# ═══════════════════════════════════════════════════════════════════════════
class BayesianModelTrainer:
    """Trains all Bayesian model variants from unified training data."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent

        # Data root — env-configurable, defaults to L: drive
        data_root = Path(
            os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final")
        )
        self.ai_data_dir = data_root / "ai_data_final"

        # Output directory for trained models
        self.models_path = self.base_path / "trained_models" / "bayesian"
        self.models_path.mkdir(parents=True, exist_ok=True)

        # Stash for SVD reducer (persisted after feature engineering)
        self._last_svd = None

        logger.info("Bayesian Model Trainer initialised")
        logger.info("  Data dir   : %s", self.ai_data_dir)
        logger.info("  Models dir : %s", self.models_path)

    # ------------------------------------------------------------------
    # Data loading & feature engineering
    # ------------------------------------------------------------------
    def load_training_data(self) -> Optional[pd.DataFrame]:
        """Load all sources via schema_adapter and return a DataFrame."""
        logger.info("Loading training data via schema_adapter ...")
        records: List[Dict[str, Any]] = load_all_training_data(self.ai_data_dir)
        if not records:
            logger.error("No training data returned by schema_adapter")
            return None
        logger.info("Loaded %d unified records", len(records))

        df = pd.DataFrame(records)

        # Drop rows missing the target (industry) or text
        df = df[df["industry"].notna() & (df["industry"] != "") & (df["industry"] != "Unknown")]
        df = df[df["text"].notna() & (df["text"].str.len() >= 50)]
        df.reset_index(drop=True, inplace=True)

        # Remove classes with too few samples
        class_counts = df["industry"].value_counts()
        valid_classes = class_counts[class_counts >= MIN_CLASS_SAMPLES].index
        df = df[df["industry"].isin(valid_classes)].reset_index(drop=True)

        logger.info(
            "After filtering: %d records, %d industry classes: %s",
            len(df),
            df["industry"].nunique(),
            list(df["industry"].value_counts().to_dict().items()),
        )
        return df if len(df) > 0 else None

    def prepare_features(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, Any, np.ndarray, Any, Any, Any]:
        """
        Build feature matrix X and label vector y from the DataFrame.

        Returns
        -------
        X_dense : np.ndarray          — combined dense feature matrix
        X_tfidf_sparse : sparse array  — raw TF-IDF (for MultinomialNB)
        y : np.ndarray                 — integer-encoded industry labels
        tfidf : TfidfVectorizer
        label_enc : LabelEncoder       — for y
        industry_enc : LabelEncoder    — for the industry feature column
        """
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import LabelEncoder

        logger.info("Building features ...")

        # --- TF-IDF on text -------------------------------------------------
        tfidf = TfidfVectorizer(
            max_features=3000,
            stop_words="english",
            sublinear_tf=True,
            ngram_range=(1, 2),
        )
        X_tfidf_sparse = tfidf.fit_transform(df["text"].fillna(""))

        # Reduce TF-IDF to 50 dense components for Gaussian / Bernoulli NB
        n_components = min(50, X_tfidf_sparse.shape[1] - 1, X_tfidf_sparse.shape[0] - 1)
        if n_components < 1:
            n_components = 1
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        X_tfidf_dense = svd.fit_transform(X_tfidf_sparse)
        self._last_svd = svd  # stash for persistence in train_all_bayesian()
        logger.info(
            "TF-IDF: %d features → SVD %d components (explained var: %.2f%%)",
            X_tfidf_sparse.shape[1],
            n_components,
            svd.explained_variance_ratio_.sum() * 100,
        )

        # --- Scalar features ------------------------------------------------
        skills_count = (
            df["skills"]
            .apply(lambda s: len(s) if isinstance(s, list) else 0)
            .values.reshape(-1, 1)
        )
        experience_years = (
            df["experience_years"].fillna(0).astype(int).values.reshape(-1, 1)
        )
        education_encoded = (
            df["education"]
            .fillna("Unknown")
            .map(EDUCATION_ORDINAL)
            .fillna(0)
            .astype(int)
            .values.reshape(-1, 1)
        )

        # NOTE: industry_encoder is saved for metadata / label mapping but is
        # NOT included in X_dense because industry is the *target variable*.
        # Including it as an input feature leaks the answer to the model
        # (data leakage) making all accuracy metrics meaningless.
        industry_enc = LabelEncoder()
        industry_enc.fit(df["industry"].fillna("Unknown"))

        # --- Combine all dense features --------------------------------------
        # Scalar order: skills_count, experience_years, education_encoded
        # (3 features — NO industry, that is the target)
        X_dense = np.hstack([
            X_tfidf_dense,
            skills_count,
            experience_years,
            education_encoded,
        ])

        # --- Target label ----------------------------------------------------
        label_enc = LabelEncoder()
        y = label_enc.fit_transform(df["industry"])

        logger.info(
            "Feature matrix shape: %s  |  Classes: %d  |  TF-IDF vocab: %d",
            X_dense.shape,
            len(label_enc.classes_),
            len(tfidf.vocabulary_),
        )
        return X_dense, X_tfidf_sparse, y, tfidf, label_enc, industry_enc

    # ------------------------------------------------------------------
    # Model trainers
    # ------------------------------------------------------------------
    def train_naive_bayes(
        self,
        X_dense: np.ndarray,
        X_tfidf_sparse: Any,
        y: np.ndarray,
        label_enc: Any,
    ) -> Optional[Dict[str, Any]]:
        """Train Gaussian, Multinomial, and Bernoulli Naive Bayes with
        train/test split, classification reports, and cross-validation."""
        logger.info("=" * 50)
        logger.info("Training Naive Bayes Classifiers ...")
        logger.info("=" * 50)

        try:
            import joblib
            from sklearn.metrics import accuracy_score, classification_report
            from sklearn.model_selection import (
                StratifiedKFold,
                cross_val_score,
                train_test_split,
            )
            from sklearn.naive_bayes import BernoulliNB, GaussianNB, MultinomialNB

            target_names = list(label_enc.classes_)
            n_splits = min(5, min(np.bincount(y)))
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            results: Dict[str, Any] = {}

            # ── Gaussian NB (dense features) ─────────────────────────────────
            logger.info("--- Gaussian Naive Bayes ---")
            X_tr, X_te, y_tr, y_te = train_test_split(
                X_dense, y, test_size=0.2, random_state=42, stratify=y,
            )
            gnb = GaussianNB()
            gnb.fit(X_tr, y_tr)
            y_pred = gnb.predict(X_te)
            acc = float(accuracy_score(y_te, y_pred))
            report_gnb = classification_report(
                y_te, y_pred, target_names=target_names, zero_division=0,
            )
            cv_scores_gnb = cross_val_score(gnb, X_dense, y, cv=cv, scoring="accuracy")
            logger.info("Gaussian NB — Test Accuracy: %.4f", acc)
            logger.info("Gaussian NB — CV Accuracy:   %.4f (+/- %.4f)", cv_scores_gnb.mean(), cv_scores_gnb.std())
            logger.info("\n%s", report_gnb)
            joblib.dump(gnb, self.models_path / "gaussian_naive_bayes.pkl")
            results["gaussian"] = {
                "accuracy": acc,
                "cv_mean": float(cv_scores_gnb.mean()),
                "cv_std": float(cv_scores_gnb.std()),
                "report": report_gnb,
            }

            # ── Multinomial NB (raw TF-IDF, non-negative sparse) ─────────────
            logger.info("--- Multinomial Naive Bayes ---")
            Xm_tr, Xm_te, ym_tr, ym_te = train_test_split(
                X_tfidf_sparse, y, test_size=0.2, random_state=42, stratify=y,
            )
            mnb = MultinomialNB()
            mnb.fit(Xm_tr, ym_tr)
            y_pred_m = mnb.predict(Xm_te)
            acc_m = float(accuracy_score(ym_te, y_pred_m))
            report_mnb = classification_report(
                ym_te, y_pred_m, target_names=target_names, zero_division=0,
            )
            cv_scores_mnb = cross_val_score(mnb, X_tfidf_sparse, y, cv=cv, scoring="accuracy")
            logger.info("Multinomial NB — Test Accuracy: %.4f", acc_m)
            logger.info("Multinomial NB — CV Accuracy:   %.4f (+/- %.4f)", cv_scores_mnb.mean(), cv_scores_mnb.std())
            logger.info("\n%s", report_mnb)
            joblib.dump(mnb, self.models_path / "multinomial_naive_bayes.pkl")
            results["multinomial"] = {
                "accuracy": acc_m,
                "cv_mean": float(cv_scores_mnb.mean()),
                "cv_std": float(cv_scores_mnb.std()),
                "report": report_mnb,
            }

            # ── Bernoulli NB (dense features) ────────────────────────────────
            logger.info("--- Bernoulli Naive Bayes ---")
            bnb = BernoulliNB()
            bnb.fit(X_tr, y_tr)
            y_pred_b = bnb.predict(X_te)
            acc_b = float(accuracy_score(y_te, y_pred_b))
            report_bnb = classification_report(
                y_te, y_pred_b, target_names=target_names, zero_division=0,
            )
            cv_scores_bnb = cross_val_score(bnb, X_dense, y, cv=cv, scoring="accuracy")
            logger.info("Bernoulli NB — Test Accuracy: %.4f", acc_b)
            logger.info("Bernoulli NB — CV Accuracy:   %.4f (+/- %.4f)", cv_scores_bnb.mean(), cv_scores_bnb.std())
            logger.info("\n%s", report_bnb)
            joblib.dump(bnb, self.models_path / "bernoulli_naive_bayes.pkl")
            results["bernoulli"] = {
                "accuracy": acc_b,
                "cv_mean": float(cv_scores_bnb.mean()),
                "cv_std": float(cv_scores_bnb.std()),
                "report": report_bnb,
            }

            return results

        except Exception as e:
            logger.error("Naive Bayes training failed: %s", e, exc_info=True)
            return None

    def train_bayesian_network(
        self,
        X_dense: np.ndarray,
        y: np.ndarray,
        label_enc: Any,
    ) -> Optional[Dict[str, Any]]:
        """Build a DAG-based Bayesian Network and train a conditional model.

        The DAG encodes assumed causal relationships between feature
        groups and the industry target.  A GaussianNB is used as the
        conditional probability estimator within the network.
        """
        logger.info("=" * 50)
        logger.info("Building Bayesian Network ...")
        logger.info("=" * 50)

        try:
            import joblib
            import networkx as nx
            from sklearn.metrics import accuracy_score, classification_report
            from sklearn.model_selection import train_test_split
            from sklearn.naive_bayes import GaussianNB

            target_names = list(label_enc.classes_)

            # Define the DAG structure:
            #   tfidf_components ──┐
            #   skills_count ──────┤
            #   experience_years ──┼──▶ industry
            #   education_level ───┘
            network = nx.DiGraph()
            feature_nodes = [
                "tfidf_components",
                "skills_count",
                "experience_years",
                "education_level",
            ]
            for node in feature_nodes:
                network.add_edge(node, "industry")

            # Also encode inter-feature priors
            network.add_edge("experience_years", "education_level")
            network.add_edge("skills_count", "tfidf_components")

            logger.info(
                "DAG nodes: %s  |  edges: %s",
                list(network.nodes),
                list(network.edges),
            )
            assert nx.is_directed_acyclic_graph(network), "Network is not a valid DAG"

            # Train conditional model (GaussianNB as probability tables)
            X_tr, X_te, y_tr, y_te = train_test_split(
                X_dense, y, test_size=0.2, random_state=42, stratify=y,
            )
            model = GaussianNB()
            model.fit(X_tr, y_tr)
            y_pred = model.predict(X_te)
            acc = float(accuracy_score(y_te, y_pred))
            report = classification_report(
                y_te, y_pred, target_names=target_names, zero_division=0,
            )
            logger.info("Bayesian Network — Test Accuracy: %.4f", acc)
            logger.info("\n%s", report)

            # Persist structure + model
            structure_info = {
                "structure": nx.node_link_data(network),
                "model_type": "GaussianNB",
                "num_features": int(X_dense.shape[1]),
                "num_classes": int(len(np.unique(y))),
                "accuracy": acc,
                "dag_nodes": list(network.nodes),
                "dag_edges": [list(e) for e in network.edges],
                "created": datetime.utcnow().isoformat(),
            }
            with open(self.models_path / "bayesian_network_structure.json", "w") as f:
                json.dump(structure_info, f, indent=2)

            joblib.dump(model, self.models_path / "bayesian_network_model.pkl")
            logger.info("Bayesian Network model and structure saved")
            return {"status": "success", "accuracy": acc, "report": report}

        except Exception as e:
            logger.error("Bayesian Network training failed: %s", e, exc_info=True)
            return None

    def train_hierarchical_bayesian(
        self,
        X_dense: np.ndarray,
        y: np.ndarray,
        label_enc: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Train a Hierarchical Bayesian Model.

        Uses per-class Gaussian NB priors fitted within each stratified
        cross-validation fold, then aggregates as a simplified hierarchical
        approximation.  Final model is fitted on all data and saved.
        """
        logger.info("=" * 50)
        logger.info("Training Hierarchical Bayesian Model ...")
        logger.info("=" * 50)

        try:
            import joblib
            from sklearn.metrics import accuracy_score, classification_report
            from sklearn.model_selection import StratifiedKFold, cross_val_predict
            from sklearn.naive_bayes import GaussianNB

            target_names = list(label_enc.classes_)

            model = GaussianNB()

            # Stratified cross-validation
            n_splits = min(5, min(np.bincount(y)))
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

            # Collect per-fold class priors to approximate the hierarchy
            fold_priors: List[List[float]] = []
            fold_thetas: List[np.ndarray] = []
            fold_accuracies: List[float] = []

            for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X_dense, y)):
                fold_model = GaussianNB()
                fold_model.fit(X_dense[train_idx], y[train_idx])
                fold_pred = fold_model.predict(X_dense[val_idx])
                fold_acc = float(accuracy_score(y[val_idx], fold_pred))
                fold_accuracies.append(fold_acc)
                fold_priors.append(fold_model.class_prior_.tolist())
                fold_thetas.append(fold_model.theta_)
                logger.info(
                    "  Fold %d/%d — accuracy: %.4f",
                    fold_idx + 1, n_splits, fold_acc,
                )

            # Overall CV prediction
            y_pred_cv = cross_val_predict(model, X_dense, y, cv=cv)
            cv_acc = float(accuracy_score(y, y_pred_cv))
            report = classification_report(
                y, y_pred_cv, target_names=target_names, zero_division=0,
            )
            logger.info("Hierarchical Bayesian — CV Accuracy: %.4f", cv_acc)
            logger.info("\n%s", report)

            # Final fit on all data
            model.fit(X_dense, y)
            joblib.dump(model, self.models_path / "hierarchical_bayesian.pkl")

            # Save per-class priors and hierarchical info
            priors_info = {
                "class_prior": model.class_prior_.tolist(),
                "theta_means_shape": list(model.theta_.shape),
                "cv_accuracy": cv_acc,
                "fold_accuracies": fold_accuracies,
                "fold_priors": fold_priors,
                "n_folds": n_splits,
                "classes": target_names,
                "created": datetime.utcnow().isoformat(),
            }
            with open(self.models_path / "hierarchical_priors.json", "w") as f:
                json.dump(priors_info, f, indent=2)

            logger.info("Hierarchical Bayesian model and priors saved")
            return {"cv_accuracy": cv_acc, "fold_accuracies": fold_accuracies, "report": report}

        except Exception as e:
            logger.error("Hierarchical Bayesian training failed: %s", e, exc_info=True)
            return None

    def train_mcmc_sampler(
        self,
        X_dense: np.ndarray,
        y: np.ndarray,
        label_enc: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Configure and run a Metropolis-Hastings MCMC sampler.

        Computes class-conditional sufficient statistics (mean, std per
        feature per class), then runs an MH chain for each class to
        approximate the posterior distribution of the class centroid.
        Saves both the sampler configuration and the posterior samples.
        """
        logger.info("=" * 50)
        logger.info("Setting up MCMC Sampler (Metropolis-Hastings) ...")
        logger.info("=" * 50)

        try:
            target_names = list(label_enc.classes_)

            # ── Per-class sufficient statistics ──────────────────────────────
            class_stats: Dict[str, Any] = {}
            for cls_idx, cls_name in enumerate(target_names):
                mask = y == cls_idx
                X_cls = X_dense[mask]
                class_stats[cls_name] = {
                    "n_samples": int(mask.sum()),
                    "mean": X_cls.mean(axis=0).tolist(),
                    "std": X_cls.std(axis=0).tolist(),
                }
                logger.info(
                    "  Class '%s': %d samples, mean-norm=%.4f",
                    cls_name,
                    int(mask.sum()),
                    float(np.linalg.norm(X_cls.mean(axis=0))),
                )

            mcmc_config = {
                "method": "Metropolis-Hastings",
                "num_samples": 2000,
                "burn_in": 200,
                "thinning": 2,
                "proposal_scale": 0.1,
                "total_features": int(X_dense.shape[1]),
                "num_classes": len(target_names),
                "classes": target_names,
                "global_priors": {
                    "mean": X_dense.mean(axis=0).tolist(),
                    "std": X_dense.std(axis=0).tolist(),
                },
                "class_conditional": class_stats,
                "created": datetime.utcnow().isoformat(),
            }

            with open(self.models_path / "mcmc_sampler_config.json", "w") as f:
                json.dump(mcmc_config, f, indent=2)
            logger.info("MCMC config saved")

            # ── Metropolis-Hastings posterior approximation ───────────────────
            posterior_samples: Dict[str, list] = {c: [] for c in target_names}
            acceptance_rates: Dict[str, float] = {}
            rng = np.random.default_rng(42)

            total_steps = mcmc_config["num_samples"] + mcmc_config["burn_in"]
            proposal_scale = mcmc_config["proposal_scale"]

            for cls_idx, cls_name in enumerate(target_names):
                mu = np.array(class_stats[cls_name]["mean"])
                sigma = np.array(class_stats[cls_name]["std"]) + 1e-8

                current = mu.copy()
                accepted = 0

                for step in range(total_steps):
                    # Gaussian random-walk proposal
                    proposal = current + rng.normal(0, proposal_scale, size=current.shape) * sigma

                    # Log-likelihood ratio under Gaussian assumption
                    log_ratio = (
                        -0.5 * np.sum(((proposal - mu) / sigma) ** 2)
                        + 0.5 * np.sum(((current - mu) / sigma) ** 2)
                    )

                    # Accept / reject
                    if np.log(rng.uniform()) < log_ratio:
                        current = proposal
                        accepted += 1

                    # Keep sample after burn-in, with thinning
                    if step >= mcmc_config["burn_in"] and step % mcmc_config["thinning"] == 0:
                        posterior_samples[cls_name].append(current.tolist())

                rate = accepted / total_steps
                acceptance_rates[cls_name] = float(rate)
                logger.info(
                    "  MCMC [%s]: %d posterior samples, acceptance %.2f%%",
                    cls_name,
                    len(posterior_samples[cls_name]),
                    rate * 100,
                )

            # Save posterior samples
            with open(self.models_path / "mcmc_posterior_samples.json", "w") as f:
                json.dump(posterior_samples, f)

            mcmc_config["acceptance_rates"] = acceptance_rates
            mcmc_config["posterior_sample_counts"] = {
                c: len(s) for c, s in posterior_samples.items()
            }

            # Re-save config with acceptance rates included
            with open(self.models_path / "mcmc_sampler_config.json", "w") as f:
                json.dump(mcmc_config, f, indent=2)

            logger.info("MCMC posterior samples saved")
            return mcmc_config

        except Exception as e:
            logger.error("MCMC setup failed: %s", e, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------
    def train_all_bayesian(self) -> Dict[str, Any]:
        """Train all Bayesian models end-to-end and save a training report."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("BAYESIAN MODEL TRAINING — ALL VARIANTS")
        logger.info("=" * 60)

        # 1. Load unified data ------------------------------------------------
        df = self.load_training_data()
        if df is None or len(df) == 0:
            logger.error("No usable training data — aborting")
            return {}

        # 2. Build features ----------------------------------------------------
        (
            X_dense,
            X_tfidf_sparse,
            y,
            tfidf,
            label_enc,
            industry_enc,
        ) = self.prepare_features(df)

        # Persist the vectoriser and encoders (needed at inference time)
        import joblib

        joblib.dump(tfidf, self.models_path / "tfidf_vectorizer.pkl")
        joblib.dump(label_enc, self.models_path / "label_encoder.pkl")
        joblib.dump(industry_enc, self.models_path / "industry_encoder.pkl")

        # C-4 FIX: Persist the SVD reducer so inference can reconstruct
        # the same TF-IDF → dense projection used during training.
        svd = self._last_svd  # stashed during prepare_features()
        if svd is not None:
            joblib.dump(svd, self.models_path / "svd_reducer.pkl")
            logger.info("Saved svd_reducer.pkl (%d components)", svd.n_components)

        logger.info("Saved tfidf_vectorizer, label_encoder, industry_encoder")

        # 3. Train each model type ---------------------------------------------
        results: Dict[str, Any] = {}
        results["naive_bayes"] = self.train_naive_bayes(
            X_dense, X_tfidf_sparse, y, label_enc,
        )
        results["bayesian_network"] = self.train_bayesian_network(
            X_dense, y, label_enc,
        )
        results["hierarchical"] = self.train_hierarchical_bayesian(
            X_dense, y, label_enc,
        )
        results["mcmc"] = self.train_mcmc_sampler(
            X_dense, y, label_enc,
        )

        # 4. Summary report ----------------------------------------------------
        report: Dict[str, Any] = {
            "trained_at": datetime.utcnow().isoformat(),
            "data_dir": str(self.ai_data_dir),
            "total_records": int(len(df)),
            "num_features": int(X_dense.shape[1]),
            "num_classes": int(len(label_enc.classes_)),
            "classes": list(label_enc.classes_),
            "models": {},
        }

        logger.info("")
        logger.info("=" * 60)
        logger.info("BAYESIAN MODEL TRAINING COMPLETE")
        logger.info("=" * 60)

        for name, result in results.items():
            ok = result is not None
            status = "OK" if ok else "FAILED"
            logger.info("  [%s] %s", status, name.upper())

            if ok and isinstance(result, dict):
                # Strip long text reports from the JSON; keep metrics only
                model_entry: Dict[str, Any] = {
                    k: v for k, v in result.items() if k != "report"
                }
                # Normalise accuracy key for the report
                if "accuracy" in result:
                    model_entry["accuracy"] = result["accuracy"]
                elif "cv_accuracy" in result:
                    model_entry["accuracy"] = result["cv_accuracy"]
                report["models"][name] = model_entry

        report_path = self.models_path / "training_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("Report saved to %s", report_path)
        return results


# ═══════════════════════════════════════════════════════════════════════════
# Standalone entry point
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    trainer = BayesianModelTrainer(str(Path(__file__).parent))
    results = trainer.train_all_bayesian()

    # Print a quick summary to stdout
    if results:
        print("\n--- Training Summary ---")
        for model_name, model_result in results.items():
            if model_result is None:
                print(f"  {model_name}: FAILED")
            elif isinstance(model_result, dict):
                acc = model_result.get("accuracy") or model_result.get("cv_accuracy", "N/A")
                print(f"  {model_name}: {acc}")
    else:
        print("No models were trained (no data or fatal error).")
