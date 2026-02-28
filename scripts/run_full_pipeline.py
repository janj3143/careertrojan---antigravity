"""
CareerTrojan Full Pipeline Runner
=================================

Executes the complete ingestion → parsing → collocation → training pipeline.

Stages:
  1. Smoke Test      - Verify paths and data availability
  2. Parser          - Parse raw files from automated_parser/
  3. Collocations    - Build n-gram/PMI collocation glossary
  4. Training        - Train all AI models on processed data

Usage:
    python scripts/run_full_pipeline.py                 # Full pipeline
    python scripts/run_full_pipeline.py --stage parser  # Single stage
    python scripts/run_full_pipeline.py --max-parse 500 # Limit parser files
    python scripts/run_full_pipeline.py --skip-parser   # Skip parsing, run rest
"""

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# ── Project setup ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "services" / "ai_engine"))

from services.shared.paths import CareerTrojanPaths

# ── Logging ────────────────────────────────────────────────────────────────
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            PROJECT_ROOT / "logs" / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log",
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger("pipeline")


def banner(title: str) -> None:
    log.info("=" * 70)
    log.info(f"  {title}")
    log.info("=" * 70)


# ── Stage 1: Smoke Test ───────────────────────────────────────────────────
def run_smoke_test(paths: CareerTrojanPaths) -> dict:
    """Verify all required paths and data availability."""
    banner("STAGE 1: SMOKE TEST")
    results = {"pass": [], "fail": [], "warn": []}

    checks = [
        ("data_root", paths.data_root),
        ("ai_data_final", paths.ai_data_final),
        ("parser_root", paths.parser_root),
        ("user_data", paths.user_data),
        ("interactions", paths.interactions),
        ("trained_models", paths.trained_models),
    ]

    for name, p in checks:
        if p.exists():
            results["pass"].append(name)
            log.info(f"  [PASS] {name}: {p}")
        else:
            # trained_models may be on J: drive, create if missing
            if name == "trained_models":
                p.mkdir(parents=True, exist_ok=True)
                results["pass"].append(name)
                log.info(f"  [PASS] {name}: {p}  (created)")
            else:
                results["fail"].append(name)
                log.error(f"  [FAIL] {name}: {p}")

    # Check critical data files
    core_db = paths.ai_data_final / "core_databases"
    merged = core_db / "Candidate_database_merged.json"
    if merged.exists():
        size_mb = merged.stat().st_size / (1024 * 1024)
        results["pass"].append("core_database")
        log.info(f"  [PASS] core_database: {size_mb:.1f} MB")
    else:
        results["warn"].append("core_database_missing")
        log.warning("  [WARN] Candidate_database_merged.json not found")

    # Count AI data files
    json_count = 0
    for _ in paths.ai_data_final.rglob("*.json"):
        json_count += 1
        if json_count > 500_000:
            break
    log.info(f"  AI data JSON files: {json_count:,}+")

    if results["fail"]:
        log.error(f"  SMOKE TEST FAILED: {results['fail']}")
        return results

    log.info("  SMOKE TEST PASSED")
    return results


# ── Stage 2: Automated Parser ─────────────────────────────────────────────
def run_parser(paths: CareerTrojanPaths, max_files: int = None) -> dict:
    """Run the automated parser on raw files in automated_parser/."""
    banner("STAGE 2: AUTOMATED PARSER")

    parser_root = paths.parser_root
    output_root = paths.ai_data_final / "parsed_from_automated"
    output_root.mkdir(parents=True, exist_ok=True)

    log.info(f"  Parser root:  {parser_root}")
    log.info(f"  Output root:  {output_root}")

    # Import parser engine
    parser_engine_path = (
        PROJECT_ROOT
        / "services"
        / "workers"
        / "ai"
        / "ai-workers"
        / "parser"
    )
    sys.path.insert(0, str(parser_engine_path))

    from automated_parser_engine import AutomatedParserEngine

    engine = AutomatedParserEngine(
        parser_root=str(parser_root),
        output_root=str(output_root),
    )

    results = engine.run(max_files=max_files)

    log.info(f"  Parser complete: {results['processed']}/{results['total_files']} files processed")
    if results["errors"]:
        log.warning(f"  Parser errors: {len(results['errors'])}")

    return results


# ── Stage 3: Collocation Glossary ──────────────────────────────────────────
def run_collocations(paths: CareerTrojanPaths) -> dict:
    """Build n-gram / PMI collocation glossary from all data sources."""
    banner("STAGE 3: COLLOCATION GLOSSARY")

    from scripts.build_collocation_glossary import (
        scan_json_file,
        scan_text_file,
        tokenize,
    )
    from collections import Counter
    import math

    NEAR_WINDOW = 5  # token distance window for NEAR pairs
    NEAR_TOKEN_CAP = 50_000_000  # higher cap to allow full run on large corpus
    NEGATION_TOKENS = {"not", "nor", "no", "without", "never"}

    # Collect tokens from all JSON data sources
    all_tokens = []
    sources_scanned = 0
    max_tokens_per_file = 50_000

    # Ordered by value: high-quality sources first.  We sample up to
    # max_files_per_dir from each to keep runtime reasonable.
    scan_dirs = [
        paths.ai_data_final / "parsed_resumes",
        paths.ai_data_final / "parsed_job_descriptions",
        paths.ai_data_final / "parsed_from_automated",
        paths.ai_data_final / "job_titles",
        paths.ai_data_final / "profiles",
        paths.ai_data_final / "contacts",
        paths.ai_data_final / "normalized",
        paths.ai_data_final / "cv_files",
        paths.ai_data_final / "journal_entries",
        paths.ai_data_final / "notes",
    ]
    max_files_per_dir = 5_000  # sample cap per directory

    # Also scan text-based gazetteer files
    gazetteer_dirs = [
        paths.ai_data_final / "glossary",
        paths.ai_data_final / "gazetteers",
        paths.ai_data_final / "industry_terms",
    ]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            log.info(f"  Skipping (not found): {scan_dir.name}")
            continue

        file_count = 0
        for json_path in scan_dir.rglob("*.json"):
            tokens = scan_json_file(json_path, max_tokens_per_file)
            all_tokens.extend(tokens)
            file_count += 1
            sources_scanned += 1

            # Progress reporting
            if file_count % 2000 == 0:
                log.info(f"    {scan_dir.name}: {file_count} files scanned...")

            # Per-dir cap
            if file_count >= max_files_per_dir:
                log.info(f"    {scan_dir.name}: hit sample cap ({max_files_per_dir})")
                break

            # Safety limit: don't exceed 50M tokens in memory
            if len(all_tokens) > 50_000_000:
                log.warning("  Token limit reached (50M), stopping scan")
                break

        log.info(f"  {scan_dir.name}: {file_count} JSON files scanned")

        if len(all_tokens) > 50_000_000:
            break

    # Scan text files in gazetteer dirs
    for gaz_dir in gazetteer_dirs:
        if not gaz_dir.exists():
            continue
        for txt_path in gaz_dir.rglob("*.txt"):
            tokens = scan_text_file(txt_path, max_tokens_per_file)
            all_tokens.extend(tokens)
            sources_scanned += 1
        for json_path in gaz_dir.rglob("*.json"):
            tokens = scan_json_file(json_path, max_tokens_per_file)
            all_tokens.extend(tokens)
            sources_scanned += 1

    log.info(f"  Total tokens collected: {len(all_tokens):,}")
    log.info(f"  Sources scanned: {sources_scanned:,}")

    if not all_tokens:
        log.warning("  No tokens found — skipping collocation build")
        return {"status": "skipped", "reason": "no_tokens"}

    # Build unigram and bigram counts
    log.info("  Computing unigram frequencies...")
    unigram_counts = Counter(all_tokens)

    log.info("  Computing bigram frequencies...")
    bigrams = [
        f"{all_tokens[i]} {all_tokens[i + 1]}"
        for i in range(len(all_tokens) - 1)
    ]
    bigram_counts = Counter(bigrams)

    # Compute NEAR pairs (ordered) within a limited window to avoid blow-up
    near_pairs = Counter()
    if len(all_tokens) <= NEAR_TOKEN_CAP:
        log.info(f"  Computing NEAR pairs with window={NEAR_WINDOW} (tokens={len(all_tokens):,})")
        for idx, tok in enumerate(all_tokens):
            upper = min(len(all_tokens), idx + NEAR_WINDOW + 1)
            for j in range(idx + 1, upper):
                pair = f"{tok} {all_tokens[j]}"
                near_pairs[pair] += 1
    else:
        log.warning(f"  Skipping NEAR computation (tokens {len(all_tokens):,} > cap {NEAR_TOKEN_CAP:,})")

    # Track negated terms (token immediately following a negation token)
    negated_terms = Counter()
    for idx, tok in enumerate(all_tokens[:-1]):
        if tok in NEGATION_TOKENS:
            negated_terms[all_tokens[idx + 1]] += 1

    # Compute PMI for top bigrams
    log.info("  Computing PMI scores...")
    total = len(all_tokens)
    pmi_scores = {}

    for bigram, count in bigram_counts.most_common(20_000):
        if count < 3:
            continue
        w1, w2 = bigram.split(" ", 1)
        p_bigram = count / total
        p_w1 = unigram_counts[w1] / total
        p_w2 = unigram_counts[w2] / total
        denom = p_w1 * p_w2
        if denom > 0:
            pmi = math.log2(p_bigram / denom)
            if pmi > 2.0:  # Only keep meaningful collocations
                pmi_scores[bigram] = round(pmi, 4)

    # Sort by PMI
    sorted_collocations = sorted(pmi_scores.items(), key=lambda x: -x[1])

    # Build output
    glossary = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_tokens": len(all_tokens),
            "sources_scanned": sources_scanned,
            "total_collocations": len(sorted_collocations),
            "near_window": NEAR_WINDOW,
            "near_tokens_processed": len(all_tokens) if near_pairs else 0,
        },
        "top_unigrams": [
            {"term": term, "count": count}
            for term, count in unigram_counts.most_common(500)
        ],
        "collocations": [
            {"bigram": bigram, "pmi": pmi, "frequency": bigram_counts[bigram]}
            for bigram, pmi in sorted_collocations[:5000]
        ],
        "near_pairs": [
            {"pair": pair, "count": cnt}
            for pair, cnt in near_pairs.most_common(500)
        ],
        "negated_terms": [
            {"term": term, "count": cnt}
            for term, cnt in negated_terms.most_common(200)
        ],
    }

    # Save
    output_path = paths.ai_data_final / "collocations_glossary.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(glossary, f, indent=2, ensure_ascii=False)

    log.info(f"  Saved {len(sorted_collocations):,} collocations to {output_path}")

    return {
        "status": "complete",
        "tokens": len(all_tokens),
        "collocations": len(sorted_collocations),
        "output": str(output_path),
    }


# ── Stage 4: AI Model Training ────────────────────────────────────────────
def run_training(paths: CareerTrojanPaths) -> dict:
    """Run the complete AI model training pipeline."""
    banner("STAGE 4: AI MODEL TRAINING")

    ai_data_dir = str(paths.ai_data_final)
    models_dir = str(paths.trained_models)

    log.info(f"  Training data: {ai_data_dir}")
    log.info(f"  Models output: {models_dir}")

    # Ensure trained_models directory exists
    paths.trained_models.mkdir(parents=True, exist_ok=True)

    # Import training components
    ai_engine_path = PROJECT_ROOT / "services" / "ai_engine"
    sys.path.insert(0, str(ai_engine_path))

    try:
        from train_all_models import IntelliCVModelTrainer

        # Override the trainer's models_dir to point to our trained_models
        trainer = IntelliCVModelTrainer(data_dir=ai_data_dir)
        trainer.models_dir = Path(models_dir)
        trainer.models_dir.mkdir(parents=True, exist_ok=True)

        # Load data
        log.info("  Loading training data...")
        df = trainer.load_cv_data()

        if df is None or len(df) == 0:
            log.error("  Failed to load training data")
            return {"status": "failed", "reason": "no_data"}

        log.info(f"  Loaded {len(df):,} records")

        # Train models
        results = {"models_trained": [], "models_failed": [], "metrics": {}}

        # 1. Bayesian Classifier + TF-IDF
        try:
            log.info("  Training Bayesian Classifier + TF-IDF...")
            model, vectorizer = trainer.train_bayesian_classifier(df)
            results["models_trained"].append("bayesian_classifier")
            results["models_trained"].append("tfidf_vectorizer")
            results["metrics"]["bayesian_classifier"] = trainer.training_report[
                "model_performance"
            ].get("bayesian_classifier", {})
            log.info("    Bayesian Classifier complete")
        except Exception as e:
            log.error(f"    Bayesian Classifier failed: {e}")
            results["models_failed"].append("bayesian_classifier")

        # 2. Sentence Embeddings
        try:
            log.info("  Setting up Sentence-BERT Embeddings...")
            model = trainer.setup_sentence_embeddings()
            if model:
                results["models_trained"].append("sentence_embeddings")
                log.info("    Sentence-BERT Embeddings complete")
            else:
                results["models_failed"].append("sentence_embeddings")
                log.warning("    Sentence-BERT not available")
        except Exception as e:
            log.error(f"    Sentence Embeddings failed: {e}")
            results["models_failed"].append("sentence_embeddings")

        # 3. spaCy NER
        try:
            log.info("  Setting up spaCy NER model...")
            nlp = trainer.setup_spacy_model()
            if nlp:
                results["models_trained"].append("spacy_ner")
                log.info("    spaCy NER complete")
            else:
                results["models_failed"].append("spacy_ner")
                log.warning("    spaCy not available")
        except Exception as e:
            log.error(f"    spaCy NER failed: {e}")
            results["models_failed"].append("spacy_ner")

        # 4. Statistical Models
        try:
            log.info("  Training Statistical Models...")
            model = trainer.train_statistical_models(df)
            if model:
                results["models_trained"].append("statistical_models")
                results["metrics"]["statistical"] = trainer.training_report[
                    "model_performance"
                ].get("salary_predictor", {})
                log.info("    Statistical Models complete")
            else:
                log.warning("    Insufficient data for statistical models")
                results["models_failed"].append("statistical_models")
        except Exception as e:
            log.error(f"    Statistical Models failed: {e}")
            results["models_failed"].append("statistical_models")

        # Save training report
        report_path = Path(models_dir) / "training_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "data_dir": ai_data_dir,
                    "models_dir": models_dir,
                    "records_loaded": len(df),
                    "models_trained": results["models_trained"],
                    "models_failed": results["models_failed"],
                    "metrics": results["metrics"],
                    "trainer_report": trainer.training_report,
                },
                f,
                indent=2,
                default=str,
            )
        log.info(f"  Training report saved: {report_path}")

        results["status"] = "complete"
        return results

    except ImportError as e:
        log.error(f"  Training import error: {e}")
        log.error("  Ensure sklearn, pandas, numpy are installed")
        return {"status": "failed", "reason": str(e)}
    except Exception as e:
        log.error(f"  Training failed: {e}")
        traceback.print_exc()
        return {"status": "failed", "reason": str(e)}


# ── Main Pipeline ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="CareerTrojan Full Pipeline")
    parser.add_argument(
        "--stage",
        choices=["smoke", "parser", "collocations", "training", "all"],
        default="all",
        help="Run a specific stage or all (default: all)",
    )
    parser.add_argument(
        "--max-parse",
        type=int,
        default=None,
        help="Limit parser to N files (for testing)",
    )
    parser.add_argument(
        "--skip-parser",
        action="store_true",
        help="Skip parser stage (use existing parsed data)",
    )
    args = parser.parse_args()

    banner("CAREERTROJAN FULL PIPELINE")
    start_time = time.time()

    # Resolve paths
    paths = CareerTrojanPaths()
    log.info(f"  Data root:     {paths.data_root}")
    log.info(f"  AI data:       {paths.ai_data_final}")
    log.info(f"  Parser root:   {paths.parser_root}")
    log.info(f"  Trained models:{paths.trained_models}")

    pipeline_results = {}

    try:
        # Stage 1: Smoke Test
        if args.stage in ("smoke", "all"):
            smoke = run_smoke_test(paths)
            pipeline_results["smoke_test"] = smoke
            if smoke["fail"]:
                log.error("Smoke test failed — aborting pipeline")
                sys.exit(1)

        # Stage 2: Parser
        if args.stage in ("parser", "all") and not args.skip_parser:
            parser_results = run_parser(paths, max_files=args.max_parse)
            pipeline_results["parser"] = {
                "total": parser_results["total_files"],
                "processed": parser_results["processed"],
                "errors": len(parser_results["errors"]),
            }

        # Stage 3: Collocations
        if args.stage in ("collocations", "all"):
            colloc_results = run_collocations(paths)
            pipeline_results["collocations"] = colloc_results

        # Stage 4: Training
        if args.stage in ("training", "all"):
            training_results = run_training(paths)
            pipeline_results["training"] = training_results

    except KeyboardInterrupt:
        log.warning("Pipeline interrupted by user")
        pipeline_results["status"] = "interrupted"
    except Exception as e:
        log.error(f"Pipeline error: {e}")
        traceback.print_exc()
        pipeline_results["status"] = "error"
        pipeline_results["error"] = str(e)

    # Final Summary
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)

    banner("PIPELINE COMPLETE")
    log.info(f"  Duration: {hours}h {minutes}m {seconds}s")

    for stage, result in pipeline_results.items():
        if isinstance(result, dict):
            status = result.get("status", "done")
            log.info(f"  {stage}: {status}")
        else:
            log.info(f"  {stage}: {result}")

    # Save pipeline report
    report_path = PROJECT_ROOT / "logs" / f"pipeline_report_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": elapsed,
                "stages": pipeline_results,
            },
            f,
            indent=2,
            default=str,
        )
    log.info(f"  Full report: {report_path}")


if __name__ == "__main__":
    main()
