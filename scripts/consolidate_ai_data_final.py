import argparse
import json
import sys
from pathlib import Path
from typing import Set


def consolidate(input_dir: Path, output_path: Path, manifest_path: Path) -> None:
    files = sorted(
        [p for p in input_dir.glob('*.json') if p.name != '_processed_sources.txt']
    )

    stats = {
        'total_files': 0,
        'records_written': 0,
        'duplicates_skipped': 0,
        'errors': 0,
        'missing_hash': 0,
    }
    errors = []
    seen: Set[str] = set()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as out_f:
        for idx, path in enumerate(files, start=1):
            stats['total_files'] += 1
            try:
                with path.open('r', encoding='utf-8') as f:
                    record = json.load(f)
            except Exception as e:  # noqa: BLE001
                stats['errors'] += 1
                if len(errors) < 50:
                    errors.append({'file': path.name, 'error': str(e)})
                continue

            if not isinstance(record, dict):
                stats['errors'] += 1
                if len(errors) < 50:
                    errors.append({'file': path.name, 'error': 'non-dict JSON payload'})
                continue

            dedup_key = record.get('file_hash') or record.get('source_path') or path.name
            if not record.get('file_hash'):
                stats['missing_hash'] += 1

            if dedup_key in seen:
                stats['duplicates_skipped'] += 1
                continue
            seen.add(dedup_key)

            out_f.write(json.dumps(record, ensure_ascii=False) + '\n')
            stats['records_written'] += 1

            if idx % 500 == 0:
                print(f"Processed {idx}/{len(files)} (written: {stats['records_written']}, dupes: {stats['duplicates_skipped']})")

    manifest = {**stats, 'errors_detail': errors}
    with manifest_path.open('w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)

    print("Consolidation complete")
    print(json.dumps(manifest, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description='Consolidate ai_data_final JSON outputs into a single NDJSON file')
    parser.add_argument('--input-dir', default='ai_data_final', help='Directory containing parser JSON outputs')
    parser.add_argument('--output', default='ai_data_final/consolidated_dataset.jsonl', help='Destination NDJSON file')
    parser.add_argument('--manifest', default='ai_data_final/consolidated_manifest.json', help='Manifest with stats/errors')
    args = parser.parse_args()

    consolidate(Path(args.input_dir), Path(args.output), Path(args.manifest))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
