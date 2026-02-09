"""
Incremental Data Ingestion & Training Pipeline
==============================================
Only processes NEW files that haven't been ingested yet
Then runs AI model training on all data
"""

import json
import logging
from pathlib import Path
from datetime import datetime
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_new_files():
    """Check how many new files need processing - INCLUDING ALL SUBFOLDERS"""
    parser_root = Path('automated_parser')
    progress_file = Path('ai_data_final/parsing_progress.json')

    # Load already processed files
    processed = set()
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            data = json.load(f)
            processed = set(data.get('processed_files', []))

    # Count files that need processing - RECURSIVE SEARCH OF ALL SUBFOLDERS
    extensions = {'.pdf', '.docx', '.doc', '.csv', '.xlsx', '.msg', '.txt', '.json', '.rtf'}
    ignored = {'incoming', 'completed', '__pycache__', '.git', '.venv', 'node_modules'}

    total_files = 0
    new_files = 0
    subfolder_count = 0

    # Recursively walk through ALL subfolders
    for file_path in parser_root.rglob('*'):
        if not file_path.is_file():
            continue
        if any(ig in file_path.parts for ig in ignored):
            continue
        if file_path.suffix.lower() not in extensions:
            continue

        total_files += 1
        file_str = str(file_path.relative_to(parser_root))

        # Track subfolder usage
        if '\\' in file_str or '/' in file_str:
            subfolder_count += 1

        if file_str not in processed:
            new_files += 1

    return {
        'total': total_files,
        'processed': len(processed),
        'new': new_files,
        'in_subfolders': subfolder_count
    }

def run_parser():
    """Run the batch parser for new files only"""
    logger.info("="*80)
    logger.info("🔄 RUNNING INCREMENTAL PARSER")
    logger.info("="*80)

    result = subprocess.run(
        [sys.executable, 'automated_parser_engine_batch.py', '--batch-size', '1000'],
        capture_output=False,
        text=True
    )

    return result.returncode == 0

def run_training():
    """Run AI model training"""
    logger.info("="*80)
    logger.info("🤖 RUNNING AI MODEL TRAINING")
    logger.info("="*80)

    result = subprocess.run(
        [sys.executable, 'ai_training_orchestrator.py'],
        capture_output=False,
        text=True
    )

    return result.returncode == 0

def main():
    start_time = datetime.now()

    logger.info("="*80)
    logger.info("🚀 INCREMENTAL INGESTION & TRAINING PIPELINE")
    logger.info("="*80)

    # Check file status
    logger.info("\n📊 Checking file status...")
    stats = check_new_files()

    logger.info(f"   Total files in automated_parser: {stats['total']:,}")
    logger.info(f"   Already processed: {stats['processed']:,}")
    logger.info(f"   New files to process: {stats['new']:,}")

    if stats['new'] == 0:
        logger.info("\n✅ No new files to process!")
        logger.info("   Skipping parser, proceeding to training...")
    else:
        logger.info(f"\n🔄 Processing {stats['new']:,} new files...")
        if not run_parser():
            logger.error("❌ Parser failed!")
            return 1
        logger.info("✅ Parser completed successfully!")

    # Run training
    logger.info("\n🤖 Starting AI model training...")
    if not run_training():
        logger.error("❌ Training failed!")
        return 1

    logger.info("✅ Training completed successfully!")

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "="*80)
    logger.info("✅ PIPELINE COMPLETE!")
    logger.info(f"   Total time: {duration:.2f} seconds ({duration/60:.1f} minutes)")
    logger.info(f"   Files processed: {stats['new']:,}")
    logger.info("="*80)

    return 0

if __name__ == "__main__":
    sys.exit(main())
