import json
from pathlib import Path


def main() -> None:
    output_root = Path(r"L:\Codec - Antigravity Data set\ai_data_final\parsed_from_automated")
    index_file = output_root / "_processed_sources.txt"

    seen = set()
    if index_file.exists():
        seen = {
            line.strip()
            for line in index_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip()
        }

    count_added = 0
    files_scanned = 0

    for json_file in output_root.glob("*.json"):
        if json_file.name == "parsing_report.json":
            continue
        files_scanned += 1
        try:
            data = json.loads(json_file.read_text(encoding="utf-8", errors="ignore"))
            source_path = data.get("source_path")
            if source_path and source_path not in seen:
                seen.add(source_path)
                count_added += 1
        except Exception:
            continue

    index_file.write_text("\n".join(sorted(seen)) + ("\n" if seen else ""), encoding="utf-8")

    print(f"FILES_SCANNED={files_scanned}")
    print(f"INDEX_TOTAL={len(seen)}")
    print(f"INDEX_ADDED={count_added}")
    print(f"INDEX_FILE={index_file}")


if __name__ == "__main__":
    main()
