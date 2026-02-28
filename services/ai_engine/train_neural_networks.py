"""
Neural Network Training Module
===================================
Trains all neural network architectures using PyTorch, with unified data
loading via ``schema_adapter.load_all_training_data()``:

  - DNN Classifier       (3-layer feedforward with dropout)
  - CNN Embedder          (1-D convolution on feature vectors)
  - LSTM Sequence Model   (for text embeddings via sentence chunks)
  - Autoencoder           (for dimensionality reduction)

Data is loaded via ``schema_adapter.load_all_training_data()`` which
normalises profiles, CV files, parsed resumes, and the merged DB into a
single record format with: text, job_title, skills, experience_years,
education, industry, salary.

Features used for all models:
  - TF-IDF on ``text`` field (max_features=5000, reduced via SVD to 50)
  - skills_count              (int)
  - experience_years          (int)
  - education_level_encoded   (ordinal int)
  - industry_encoded          (integer-coded category — used as feature
    only in the autoencoder; target label for classifiers)

Target variable:
  ``industry`` (real multi-class labels).

Usage:
    # Standalone
    python train_neural_networks.py

    # As module
    from services.ai_engine.train_neural_networks import NeuralNetworkTrainer
    trainer = NeuralNetworkTrainer()
    results = trainer.train_all_neural()
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
    "High School": 1,
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

# Minimum records required to proceed with training
MIN_RECORDS = 100

# Minimum number of samples a class must have to be kept
MIN_CLASS_SAMPLES = 2


# ═══════════════════════════════════════════════════════════════════════════
#  PyTorch model definitions
# ═══════════════════════════════════════════════════════════════════════════
import torch
import torch.nn as nn


class DNNClassifier(nn.Module):
    """3-layer feedforward classifier with dropout."""

    def __init__(self, input_dim: int, num_classes: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class CNNEmbedder(nn.Module):
    """1-D convolution on feature vectors for embedding extraction."""

    def __init__(self, input_dim: int, num_classes: int):
        super().__init__()
        # input: (batch, 1, input_dim)
        self.conv_block = nn.Sequential(
            nn.Conv1d(in_channels=1, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(output_size=max(1, input_dim // 2)),
            nn.Conv1d(in_channels=64, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(output_size=1),  # → (batch, 32, 1)
        )
        self.classifier = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, input_dim) → (batch, 1, input_dim)
        x = x.unsqueeze(1)
        x = self.conv_block(x)           # (batch, 32, 1)
        x = x.squeeze(-1)                # (batch, 32)
        return self.classifier(x)


class LSTMSequenceModel(nn.Module):
    """LSTM operating on chunked text embeddings."""

    def __init__(self, input_dim: int, num_classes: int, hidden_dim: int = 64):
        super().__init__()
        # We treat the feature vector as a sequence of length=input_dim, each
        # element being a 1-dim "token".  A projection layer lifts tokens to
        # a richer embedding before the LSTM processes them.
        self.embed_proj = nn.Linear(1, 16)
        self.lstm = nn.LSTM(
            input_size=16,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.2,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, input_dim) → (batch, input_dim, 1)
        x = x.unsqueeze(-1)
        x = self.embed_proj(x)           # (batch, seq_len, 16)
        out, (h_n, _) = self.lstm(x)     # h_n: (2, batch, hidden_dim)
        h_last = h_n[-1]                 # (batch, hidden_dim)
        return self.classifier(h_last)


class Autoencoder(nn.Module):
    """Symmetric autoencoder for dimensionality reduction."""

    def __init__(self, input_dim: int, encoding_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, encoding_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        return self.decoder(z)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


# ═══════════════════════════════════════════════════════════════════════════
#  Trainer
# ═══════════════════════════════════════════════════════════════════════════
class NeuralNetworkTrainer:
    """Trains all neural network model variants from unified training data."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent

        # Use centralised config for data paths
        try:
            from services.ai_engine.config import AI_DATA_DIR, models_path as _cfg_models
            self.ai_data_dir = AI_DATA_DIR
            self.models_path = _cfg_models / "neural"
        except ImportError:
            data_root = Path(
                os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final")
            )
            self.ai_data_dir = data_root / "ai_data_final"
            self.models_path = self.base_path / "trained_models" / "neural"

        self.models_path.mkdir(parents=True, exist_ok=True)

        # Device selection
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info("Neural Network Trainer initialised")
        logger.info("  Data dir   : %s", self.ai_data_dir)
        logger.info("  Models dir : %s", self.models_path)
        logger.info("  Device     : %s", self.device)

    # ------------------------------------------------------------------
    # Data loading
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

        if len(df) < MIN_RECORDS:
            logger.warning(
                "Only %d records after filtering (need >= %d) — skipping training",
                len(df),
                MIN_RECORDS,
            )
            return None

        return df

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------
    def prepare_features(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, Any, Any, Any, Any]:
        """
        Build feature matrix X and label vector y from the DataFrame.

        Returns
        -------
        X_dense   : np.ndarray       — combined dense feature matrix
        y         : np.ndarray        — integer-encoded industry labels
        tfidf     : TfidfVectorizer
        svd       : TruncatedSVD
        label_enc : LabelEncoder      — for y
        scaler    : StandardScaler    — fitted on X_dense
        """
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import LabelEncoder, StandardScaler

        logger.info("Building features ...")

        # --- TF-IDF on text -------------------------------------------------
        tfidf = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            sublinear_tf=True,
            ngram_range=(1, 2),
        )
        X_tfidf_sparse = tfidf.fit_transform(df["text"].fillna(""))

        # Reduce TF-IDF to 50 dense components via SVD
        n_components = min(50, X_tfidf_sparse.shape[1] - 1, X_tfidf_sparse.shape[0] - 1)
        n_components = max(n_components, 1)
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        X_tfidf_dense = svd.fit_transform(X_tfidf_sparse)
        logger.info(
            "TF-IDF: %d features -> SVD %d components (explained var: %.2f%%)",
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

        # Industry as an additional feature (for the autoencoder / embedder)
        industry_le_feature = LabelEncoder()
        industry_feature = industry_le_feature.fit_transform(
            df["industry"].fillna("Unknown")
        ).reshape(-1, 1)

        # --- Combine all dense features --------------------------------------
        X_dense = np.hstack([
            X_tfidf_dense,
            skills_count,
            experience_years,
            education_encoded,
            industry_feature,
        ])

        # --- Target label (same industry, separate encoder) ------------------
        label_enc = LabelEncoder()
        y = label_enc.fit_transform(df["industry"])

        # --- Scale features --------------------------------------------------
        scaler = StandardScaler()
        X_dense = scaler.fit_transform(X_dense)

        logger.info(
            "Feature matrix shape: %s  |  Classes: %d  |  TF-IDF vocab: %d",
            X_dense.shape,
            len(label_enc.classes_),
            len(tfidf.vocabulary_),
        )
        return X_dense, y, tfidf, svd, label_enc, scaler

    # ------------------------------------------------------------------
    # PyTorch training helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _make_loader(
        X: np.ndarray,
        y: Optional[np.ndarray],
        batch_size: int = 64,
        shuffle: bool = True,
    ) -> torch.utils.data.DataLoader:
        """Create a DataLoader from numpy arrays."""
        X_t = torch.tensor(X, dtype=torch.float32)
        if y is not None:
            y_t = torch.tensor(y, dtype=torch.long)
            ds = torch.utils.data.TensorDataset(X_t, y_t)
        else:
            ds = torch.utils.data.TensorDataset(X_t)
        return torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=shuffle)

    def _train_classifier(
        self,
        model: nn.Module,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        epochs: int = 50,
        lr: float = 1e-3,
        batch_size: int = 64,
    ) -> Dict[str, Any]:
        """Generic training loop for classification models (CrossEntropyLoss)."""
        model = model.to(self.device)
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", patience=5, factor=0.5,
        )

        train_loader = self._make_loader(X_train, y_train, batch_size=batch_size)
        history: Dict[str, list] = {"train_loss": [], "val_loss": [], "val_acc": []}

        for epoch in range(1, epochs + 1):
            # --- Train -------------------------------------------------------
            model.train()
            epoch_loss = 0.0
            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                optimizer.zero_grad()
                logits = model(batch_X)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * batch_X.size(0)
            epoch_loss /= len(train_loader.dataset)

            # --- Validate ----------------------------------------------------
            model.eval()
            with torch.no_grad():
                X_te_t = torch.tensor(X_test, dtype=torch.float32).to(self.device)
                y_te_t = torch.tensor(y_test, dtype=torch.long).to(self.device)
                val_logits = model(X_te_t)
                val_loss = criterion(val_logits, y_te_t).item()
                preds = val_logits.argmax(dim=1)
                val_acc = (preds == y_te_t).float().mean().item()

            scheduler.step(val_loss)
            history["train_loss"].append(epoch_loss)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)

            if epoch % 10 == 0 or epoch == 1:
                logger.info(
                    "  Epoch %3d/%d — train_loss: %.4f  val_loss: %.4f  val_acc: %.4f",
                    epoch, epochs, epoch_loss, val_loss, val_acc,
                )

        final_acc = history["val_acc"][-1]
        best_acc = max(history["val_acc"])
        return {
            "final_accuracy": float(final_acc),
            "best_accuracy": float(best_acc),
            "final_train_loss": float(history["train_loss"][-1]),
            "final_val_loss": float(history["val_loss"][-1]),
            "epochs": epochs,
        }

    # ------------------------------------------------------------------
    # Model trainers
    # ------------------------------------------------------------------
    def train_dnn_classifier(
        self,
        X_dense: np.ndarray,
        y: np.ndarray,
        label_enc: Any,
    ) -> Optional[Dict[str, Any]]:
        """Train a 3-layer feedforward DNN classifier."""
        logger.info("=" * 50)
        logger.info("Training DNN Classifier ...")
        logger.info("=" * 50)

        try:
            from sklearn.metrics import classification_report
            from sklearn.model_selection import train_test_split

            num_classes = len(label_enc.classes_)
            target_names = list(label_enc.classes_)

            X_tr, X_te, y_tr, y_te = train_test_split(
                X_dense, y, test_size=0.2, random_state=42, stratify=y,
            )

            model = DNNClassifier(input_dim=X_dense.shape[1], num_classes=num_classes)
            metrics = self._train_classifier(model, X_tr, y_tr, X_te, y_te, epochs=50)

            # Classification report
            model.eval()
            with torch.no_grad():
                X_te_t = torch.tensor(X_te, dtype=torch.float32).to(self.device)
                preds = model(X_te_t).argmax(dim=1).cpu().numpy()
            report = classification_report(
                y_te, preds, target_names=target_names, zero_division=0,
            )
            logger.info("DNN — Best Accuracy: %.4f", metrics["best_accuracy"])
            logger.info("\n%s", report)

            # Save
            torch.save(model.state_dict(), self.models_path / "dnn_classifier.pt")
            logger.info("Saved dnn_classifier.pt")

            metrics["report"] = report
            return metrics

        except Exception as e:
            logger.error("DNN training failed: %s", e, exc_info=True)
            return None

    def train_cnn_embedder(
        self,
        X_dense: np.ndarray,
        y: np.ndarray,
        label_enc: Any,
    ) -> Optional[Dict[str, Any]]:
        """Train a 1-D CNN embedder / classifier."""
        logger.info("=" * 50)
        logger.info("Training CNN Embedder ...")
        logger.info("=" * 50)

        try:
            from sklearn.metrics import classification_report
            from sklearn.model_selection import train_test_split

            num_classes = len(label_enc.classes_)
            target_names = list(label_enc.classes_)

            X_tr, X_te, y_tr, y_te = train_test_split(
                X_dense, y, test_size=0.2, random_state=42, stratify=y,
            )

            model = CNNEmbedder(input_dim=X_dense.shape[1], num_classes=num_classes)
            metrics = self._train_classifier(model, X_tr, y_tr, X_te, y_te, epochs=40)

            # Classification report
            model.eval()
            with torch.no_grad():
                X_te_t = torch.tensor(X_te, dtype=torch.float32).to(self.device)
                preds = model(X_te_t).argmax(dim=1).cpu().numpy()
            report = classification_report(
                y_te, preds, target_names=target_names, zero_division=0,
            )
            logger.info("CNN — Best Accuracy: %.4f", metrics["best_accuracy"])
            logger.info("\n%s", report)

            # Save
            torch.save(model.state_dict(), self.models_path / "cnn_embedder.pt")
            logger.info("Saved cnn_embedder.pt")

            metrics["report"] = report
            return metrics

        except Exception as e:
            logger.error("CNN training failed: %s", e, exc_info=True)
            return None

    def train_lstm_sequence(
        self,
        X_dense: np.ndarray,
        y: np.ndarray,
        label_enc: Any,
    ) -> Optional[Dict[str, Any]]:
        """Train an LSTM sequence model on feature vectors."""
        logger.info("=" * 50)
        logger.info("Training LSTM Sequence Model ...")
        logger.info("=" * 50)

        try:
            from sklearn.metrics import classification_report
            from sklearn.model_selection import train_test_split

            num_classes = len(label_enc.classes_)
            target_names = list(label_enc.classes_)

            X_tr, X_te, y_tr, y_te = train_test_split(
                X_dense, y, test_size=0.2, random_state=42, stratify=y,
            )

            model = LSTMSequenceModel(
                input_dim=X_dense.shape[1], num_classes=num_classes,
            )
            metrics = self._train_classifier(
                model, X_tr, y_tr, X_te, y_te, epochs=30, lr=5e-4,
            )

            # Classification report
            model.eval()
            with torch.no_grad():
                X_te_t = torch.tensor(X_te, dtype=torch.float32).to(self.device)
                preds = model(X_te_t).argmax(dim=1).cpu().numpy()
            report = classification_report(
                y_te, preds, target_names=target_names, zero_division=0,
            )
            logger.info("LSTM — Best Accuracy: %.4f", metrics["best_accuracy"])
            logger.info("\n%s", report)

            # Save
            torch.save(model.state_dict(), self.models_path / "lstm_sequence.pt")
            logger.info("Saved lstm_sequence.pt")

            metrics["report"] = report
            return metrics

        except Exception as e:
            logger.error("LSTM training failed: %s", e, exc_info=True)
            return None

    def train_autoencoder(
        self, X_dense: np.ndarray,
    ) -> Optional[Dict[str, Any]]:
        """Train an autoencoder for unsupervised dimensionality reduction."""
        logger.info("=" * 50)
        logger.info("Training Autoencoder ...")
        logger.info("=" * 50)

        try:
            encoding_dim = 16
            model = Autoencoder(
                input_dim=X_dense.shape[1], encoding_dim=encoding_dim,
            ).to(self.device)
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

            loader = self._make_loader(X_dense, y=None, batch_size=64, shuffle=True)

            best_loss = float("inf")
            for epoch in range(1, 61):
                model.train()
                epoch_loss = 0.0
                for (batch_X,) in loader:
                    batch_X = batch_X.to(self.device)
                    optimizer.zero_grad()
                    reconstructed = model(batch_X)
                    loss = criterion(reconstructed, batch_X)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item() * batch_X.size(0)
                epoch_loss /= len(loader.dataset)

                if epoch_loss < best_loss:
                    best_loss = epoch_loss

                if epoch % 10 == 0 or epoch == 1:
                    logger.info(
                        "  Epoch %3d/60 — recon_loss: %.6f", epoch, epoch_loss,
                    )

            # Save
            torch.save(model.state_dict(), self.models_path / "autoencoder.pt")
            logger.info("Saved autoencoder.pt")
            logger.info(
                "Autoencoder — final recon_loss: %.6f  best: %.6f",
                epoch_loss,
                best_loss,
            )

            return {
                "final_recon_loss": float(epoch_loss),
                "best_recon_loss": float(best_loss),
                "encoding_dim": encoding_dim,
                "epochs": 60,
            }

        except Exception as e:
            logger.error("Autoencoder training failed: %s", e, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------
    def train_all_neural(self) -> Dict[str, Any]:
        """Train all neural network models end-to-end and save a report."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("NEURAL NETWORK TRAINING — ALL ARCHITECTURES")
        logger.info("=" * 60)

        # 1. Load unified data ------------------------------------------------
        df = self.load_training_data()
        if df is None or len(df) == 0:
            logger.error("No usable training data — aborting")
            return {}

        # 2. Build features ----------------------------------------------------
        X_dense, y, tfidf, svd, label_enc, scaler = self.prepare_features(df)

        # Persist sklearn objects (needed at inference time)
        import joblib

        joblib.dump(tfidf, self.models_path / "tfidf_vectorizer.pkl")
        joblib.dump(svd, self.models_path / "svd_reducer.pkl")
        joblib.dump(label_enc, self.models_path / "label_encoder.pkl")
        joblib.dump(scaler, self.models_path / "feature_scaler.pkl")
        logger.info("Saved tfidf_vectorizer, svd_reducer, label_encoder, feature_scaler")

        # Also save model metadata for inference reconstruction
        meta = {
            "input_dim": int(X_dense.shape[1]),
            "num_classes": int(len(label_enc.classes_)),
            "classes": list(label_enc.classes_),
            "svd_components": int(svd.n_components),
            "tfidf_max_features": 5000,
            "education_ordinal": EDUCATION_ORDINAL,
        }
        with open(self.models_path / "dnn_metadata.json", "w") as f:
            json.dump(meta, f, indent=2)

        # 3. Train each architecture -------------------------------------------
        results: Dict[str, Any] = {}
        results["dnn"] = self.train_dnn_classifier(X_dense, y, label_enc)
        results["cnn"] = self.train_cnn_embedder(X_dense, y, label_enc)
        results["lstm"] = self.train_lstm_sequence(X_dense, y, label_enc)
        results["autoencoder"] = self.train_autoencoder(X_dense)

        # 4. Summary report ----------------------------------------------------
        report: Dict[str, Any] = {
            "trained_at": datetime.utcnow().isoformat(),
            "data_dir": str(self.ai_data_dir),
            "total_records": int(len(df)),
            "num_features": int(X_dense.shape[1]),
            "num_classes": int(len(label_enc.classes_)),
            "classes": list(label_enc.classes_),
            "device": str(self.device),
            "models": {},
        }

        logger.info("")
        logger.info("=" * 60)
        logger.info("NEURAL NETWORK TRAINING COMPLETE")
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
                if "best_accuracy" in result:
                    model_entry["accuracy"] = result["best_accuracy"]
                elif "final_accuracy" in result:
                    model_entry["accuracy"] = result["final_accuracy"]
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
    trainer = NeuralNetworkTrainer(str(Path(__file__).parent))
    results = trainer.train_all_neural()

    # Print a quick summary to stdout
    if results:
        print("\n--- Training Summary ---")
        for model_name, model_result in results.items():
            if model_result is None:
                print(f"  {model_name}: FAILED")
            elif isinstance(model_result, dict):
                acc = (
                    model_result.get("best_accuracy")
                    or model_result.get("final_accuracy")
                    or model_result.get("best_recon_loss", "N/A")
                )
                print(f"  {model_name}: {acc}")
    else:
        print("No models were trained (no data or fatal error).")
