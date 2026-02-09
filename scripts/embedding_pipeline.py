#!/usr/bin/env python3
"""
embedding_pipeline.py — CV upload → sentence-transformer embeddings
====================================================================

Purpose:
  Takes one or more CV/resume JSON files (output of the parser-worker),
  generates sentence-transformer embeddings for key text fields, and
  stores the resulting vectors alongside the profile data.

Workflow:
  1. Load profile JSON(s) from --input (file or directory)
  2. Extract embedding-worthy text (summary, experience, skills)
  3. Encode with sentence-transformers model (default: all-MiniLM-L6-v2)
  4. Save embeddings as .npy or append to profile JSON
  5. Optionally push to vector index (future: FAISS/Qdrant)

Usage:
  python scripts/embedding_pipeline.py --input data/profiles/
  python scripts/embedding_pipeline.py --input data/profiles/abc123.json --model all-MiniLM-L6-v2
  python scripts/embedding_pipeline.py --input data/profiles/ --output data/embeddings/ --batch-size 64
"""

import argparse
import json
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("embedding_pipeline")

# ── Lazy-load sentence-transformers to keep CLI responsive ────────

_model_cache: dict = {}


def get_model(model_name: str):
    """Load (and cache) a SentenceTransformer model."""
    if model_name not in _model_cache:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            sys.exit(1)
        logger.info(f"Loading model '{model_name}' …")
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


# ── Text extraction ──────────────────────────────────────────────

def extract_text_fields(profile: Dict[str, Any]) -> str:
    """
    Concatenate the most embedding-worthy fields from a parsed profile.
    Returns a single string ready for encoding.
    """
    parts: List[str] = []

    # Summary / objective
    summary = profile.get("summary") or profile.get("objective") or ""
    if summary:
        parts.append(summary)

    # Work experience entries
    for exp in profile.get("experience", []):
        title = exp.get("title", "")
        company = exp.get("company", "")
        desc = exp.get("description", "")
        parts.append(f"{title} at {company}. {desc}".strip())

    # Skills (join as one sentence)
    skills = profile.get("skills", [])
    if skills:
        parts.append("Skills: " + ", ".join(skills))

    # Education
    for edu in profile.get("education", []):
        degree = edu.get("degree", "")
        institution = edu.get("institution", "")
        parts.append(f"{degree} from {institution}".strip())

    return " ".join(parts).strip()


# ── Embedding logic ──────────────────────────────────────────────

def embed_profiles(
    profiles: List[Dict[str, Any]],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
) -> List[Dict[str, Any]]:
    """
    Generates embeddings for a list of profile dicts.
    Returns list of {id, embedding (list[float]), text_length}.
    """
    model = get_model(model_name)
    texts = [extract_text_fields(p) for p in profiles]
    ids = [p.get("id", p.get("filename", str(i))) for i, p in enumerate(profiles)]

    logger.info(f"Encoding {len(texts)} profiles (batch_size={batch_size}) …")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)

    results = []
    for pid, emb, txt in zip(ids, embeddings, texts):
        results.append({
            "id": pid,
            "embedding": emb.tolist(),
            "dim": len(emb),
            "text_length": len(txt),
        })
    return results


# ── I/O helpers ──────────────────────────────────────────────────

def load_profiles(input_path: Path) -> List[Dict[str, Any]]:
    profiles = []
    if input_path.is_file():
        with open(input_path, "r", encoding="utf-8") as f:
            profiles.append(json.load(f))
    elif input_path.is_dir():
        for fp in sorted(input_path.glob("*.json")):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data.setdefault("id", fp.stem)
                    profiles.append(data)
            except Exception as e:
                logger.warning(f"Skipping {fp.name}: {e}")
    else:
        logger.error(f"Input path does not exist: {input_path}")
    return profiles


def save_embeddings(results: List[dict], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save as individual .npy and a combined index JSON
    index = []
    for r in results:
        npy_path = output_dir / f"{r['id']}.npy"
        np.save(npy_path, np.array(r["embedding"], dtype=np.float32))
        index.append({"id": r["id"], "dim": r["dim"], "text_length": r["text_length"], "file": npy_path.name})

    index_path = output_dir / "embedding_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"model": "all-MiniLM-L6-v2", "count": len(index), "entries": index}, f, indent=2)
    logger.info(f"Saved {len(index)} embeddings → {output_dir}")


# ── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CV → sentence-transformer embedding pipeline")
    parser.add_argument("--input", required=True, help="Profile JSON file or directory")
    parser.add_argument("--output", default=None, help="Output directory for .npy embeddings (default: <input>/embeddings)")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    parser.add_argument("--batch-size", type=int, default=32, help="Encoding batch size")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else input_path.parent / "embeddings"

    t0 = time.time()
    profiles = load_profiles(input_path)
    if not profiles:
        logger.error("No profiles found — nothing to embed.")
        return 1

    results = embed_profiles(profiles, model_name=args.model, batch_size=args.batch_size)
    save_embeddings(results, output_dir)

    elapsed = round(time.time() - t0, 2)
    logger.info(f"✅ Pipeline complete — {len(results)} embeddings in {elapsed}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
