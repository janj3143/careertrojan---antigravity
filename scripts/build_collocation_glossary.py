import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.shared.paths import CareerTrojanPaths

NEAR_WINDOW = 5
NEAR_TOKEN_CAP = 50_000_000
NEGATION_TOKENS = {"not", "nor", "no", "without", "never"}


def tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def iter_text_from_json(value) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_text_from_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_text_from_json(item)


def scan_json_file(path: Path, max_tokens: int) -> List[str]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    tokens: List[str] = []
    for text in iter_text_from_json(data):
        tokens.extend(tokenize(text))
        if len(tokens) >= max_tokens:
            break
    return tokens[:max_tokens]


def scan_text_file(path: Path, max_tokens: int) -> List[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    return tokenize(text)[:max_tokens]


def _clean_line(line: str) -> str:
    cleaned = line.strip()
    if not cleaned:
        return ""
    cleaned = cleaned.replace("\u2013", "-")
    cleaned = cleaned.replace("\u2014", "-")
    cleaned = cleaned.replace("\u2212", "-")
    cleaned = cleaned.replace("\u00a0", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _is_section_header(line: str) -> bool:
    if not line:
        return True
    lower = line.casefold()
    if lower.startswith("contents"):
        return True
    if lower in {"see also", "references", "external links", "article", "talk", "read", "edit", "view history"}:
        return True
    if re.fullmatch(r"[a-z]", lower):
        return True
    if lower.startswith("wikipedia"):
        return True
    if "glossary" in lower and "terms" in lower and "definitions" in lower:
        return True
    return False


def _extract_inline_definition(line: str) -> Tuple[str, str] | None:
    match = re.match(r"^([^:\-]{2,80})\s*[:\-]\s+(.*)$", line)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9 /&+.'-]{1,80})\s*\(([^)]+)\)\s+(.*)$", line)
    if match:
        term = match.group(1).strip()
        expansion = match.group(2).strip()
        rest = match.group(3).strip()
        definition = f"{expansion}. {rest}" if rest else expansion
        return term, definition
    if "\t" in line:
        left, right = line.split("\t", 1)
        if left.strip() and right.strip():
            return left.strip(), right.strip()
    return None


def _extract_glossary_terms(text: str, source_label: str) -> List[Dict[str, str]]:
    terms: List[Dict[str, str]] = []
    lines = [
        _clean_line(line)
        for line in text.splitlines()
    ]

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        idx += 1
        if not line or _is_section_header(line):
            continue

        inline = _extract_inline_definition(line)
        if inline:
            term, definition = inline
            if term and definition:
                terms.append({"term": term, "definition": definition, "source": source_label})
            continue

        if idx < len(lines):
            next_line = lines[idx]
            if next_line and not _is_section_header(next_line):
                if len(line) <= 120 and not line.endswith("."):
                    terms.append({"term": line, "definition": next_line, "source": source_label})
                    idx += 1

    return terms


def load_glossary_terms(paths: List[Path], max_terms: int = 20000) -> List[Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for path in paths:
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        extracted = _extract_glossary_terms(text, str(path))
        for item in extracted:
            term = item.get("term", "").strip()
            definition = item.get("definition", "").strip()
            if not term or not definition:
                continue
            key = term.casefold()
            if key not in index or len(definition) > len(index[key]["definition"]):
                index[key] = item
            if len(index) >= max_terms:
                break
        if len(index) >= max_terms:
            break

    return list(index.values())


def update_ngram_counts(
    tokens: List[str],
    unigram: Counter,
    bigram: Counter,
    trigram: Counter,
    near_pairs: Counter,
    negated_terms: Counter,
) -> None:
    unigram.update(tokens)
    bigram.update(zip(tokens, tokens[1:]))
    trigram.update(zip(tokens, tokens[1:], tokens[2:]))

    if len(tokens) <= NEAR_TOKEN_CAP:
        for idx, tok in enumerate(tokens):
            upper = min(len(tokens), idx + NEAR_WINDOW + 1)
            for j in range(idx + 1, upper):
                near_pairs[(tok, tokens[j])] += 1

    for idx, tok in enumerate(tokens[:-1]):
        if tok in NEGATION_TOKENS:
            negated_terms[tokens[idx + 1]] += 1


def compute_pmi(
    bigram_key: Tuple[str, str],
    bigram_count: int,
    unigram: Counter,
    total_tokens: int,
) -> float:
    if total_tokens < 2:
        return 0.0
    w1, w2 = bigram_key
    p_w1 = unigram[w1] / total_tokens
    p_w2 = unigram[w2] / total_tokens
    p_w1_w2 = bigram_count / (total_tokens - 1)
    if p_w1 == 0 or p_w2 == 0 or p_w1_w2 == 0:
        return 0.0
    return math.log2(p_w1_w2 / (p_w1 * p_w2))


def iter_json_files(root: Path, max_files: int) -> Iterable[Path]:
    if not root.exists():
        return []
    count = 0
    for path in root.rglob("*.json"):
        yield path
        count += 1
        if max_files and count >= max_files:
            break


def load_gazetteer_phrases(paths: List[Path]) -> List[str]:
    phrases: List[str] = []
    for path in paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if isinstance(payload, list):
            candidates = payload
        elif isinstance(payload, dict):
            candidates = payload.get("phrases", [])
        else:
            candidates = []

        for item in candidates:
            if isinstance(item, str):
                phrase = item.strip().lower()
            else:
                phrase = str(item).strip().lower()
            if phrase:
                phrases.append(phrase)

    return list(dict.fromkeys(phrases))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build collocation glossary from AI + user data.")
    parser.add_argument("--min-freq", type=int, default=5, help="Minimum n-gram frequency")
    parser.add_argument("--min-pmi", type=float, default=0.0, help="Minimum PMI for bigrams")
    parser.add_argument("--max-files", type=int, default=0, help="Max JSON files per source (0 = no limit)")
    parser.add_argument("--max-texts", type=int, default=0, help="Max text sources per run (0 = no limit)")
    parser.add_argument("--max-tokens", type=int, default=2000, help="Max tokens per text source")
    parser.add_argument("--top-bigrams", type=int, default=5000, help="Top bigrams to keep")
    parser.add_argument("--top-trigrams", type=int, default=3000, help="Top trigrams to keep")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    paths = CareerTrojanPaths()
    ai_root = paths.ai_data_final
    parser_root = paths.parser_root
    user_interactions = paths.interactions
    data_root = paths.data_root
    repo_root = PROJECT_ROOT

    unigram = Counter()
    bigram = Counter()
    trigram = Counter()
    near_pairs = Counter()
    negated_terms = Counter()

    sources_scanned = 0
    files_scanned = 0

    ai_sources = [
        ai_root / "parsed_resumes",
        ai_root / "parsed_job_descriptions",
        ai_root / "profiles",
        ai_root / "learning_library",
        ai_root / "job_titles",
        ai_root / "job_descriptions",
        ai_root / "enrichment_results",
        ai_root / "journal_entries",
        ai_root / "job_matching",
    ]

    for source in ai_sources:
        for json_path in iter_json_files(source, args.max_files):
            tokens = scan_json_file(json_path, args.max_tokens)
            if not tokens:
                continue
            update_ngram_counts(tokens, unigram, bigram, trigram, near_pairs, negated_terms)
            files_scanned += 1
            sources_scanned += 1
            if args.max_texts and sources_scanned >= args.max_texts:
                break
        if args.max_texts and sources_scanned >= args.max_texts:
            break

    if not args.max_texts or sources_scanned < args.max_texts:
        for json_path in iter_json_files(user_interactions, args.max_files):
            tokens = scan_json_file(json_path, args.max_tokens)
            if not tokens:
                continue
            update_ngram_counts(tokens, unigram, bigram, trigram, near_pairs, negated_terms)
            files_scanned += 1
            sources_scanned += 1
            if args.max_texts and sources_scanned >= args.max_texts:
                break

    collocation_txt = parser_root / "collocation data.txt"
    if collocation_txt.exists() and (not args.max_texts or sources_scanned < args.max_texts):
        tokens = scan_text_file(collocation_txt, args.max_tokens)
        if tokens:
            update_ngram_counts(tokens, unigram, bigram, trigram, near_pairs, negated_terms)
            sources_scanned += 1

    glossary_text_sources = [
        data_root / "lists to add to the glossrys.txt",
        data_root / "more data for glossary.txt",
        data_root / "more data 2.txt",
    ]
    for glossary_path in glossary_text_sources:
        if not glossary_path.exists():
            continue
        if args.max_texts and sources_scanned >= args.max_texts:
            break
        tokens = scan_text_file(glossary_path, args.max_tokens)
        if tokens:
            update_ngram_counts(tokens, unigram, bigram, trigram, near_pairs, negated_terms)
            sources_scanned += 1

    total_tokens = sum(unigram.values())

    bigram_entries = []
    for key, count in bigram.items():
        if count < args.min_freq:
            continue
        pmi = compute_pmi(key, count, unigram, total_tokens)
        if pmi < args.min_pmi:
            continue
        bigram_entries.append({
            "phrase": f"{key[0]} {key[1]}",
            "count": count,
            "pmi": round(pmi, 4),
        })

    trigram_entries = []
    for key, count in trigram.items():
        if count < args.min_freq:
            continue
        trigram_entries.append({
            "phrase": f"{key[0]} {key[1]} {key[2]}",
            "count": count,
        })

    gazetteer_paths = [
        ai_root / "collocations_gazetteer.json",
        repo_root / "data" / "collocations_gazetteer.json",
        repo_root / "data" / "gazetteer" / "collocations_gazetteer.json",
    ]
    gazetteer_phrases = load_gazetteer_phrases(gazetteer_paths)
    glossary_terms = load_glossary_terms(glossary_text_sources)

    bigram_index = {entry["phrase"]: entry for entry in bigram_entries}
    trigram_index = {entry["phrase"]: entry for entry in trigram_entries}

    for phrase in gazetteer_phrases:
        tokens = phrase.split()
        if len(tokens) == 2:
            if phrase not in bigram_index:
                bigram_index[phrase] = {
                    "phrase": phrase,
                    "count": args.min_freq,
                    "pmi": 0.0,
                    "source": "gazetteer",
                }
        elif len(tokens) == 3:
            if phrase not in trigram_index:
                trigram_index[phrase] = {
                    "phrase": phrase,
                    "count": args.min_freq,
                    "source": "gazetteer",
                }

    bigram_entries = list(bigram_index.values())
    trigram_entries = list(trigram_index.values())

    bigram_entries.sort(key=lambda x: (x.get("pmi", 0.0), x["count"]), reverse=True)
    trigram_entries.sort(key=lambda x: x["count"], reverse=True)

    if args.top_bigrams:
        bigram_entries = bigram_entries[: args.top_bigrams]
    if args.top_trigrams:
        trigram_entries = trigram_entries[: args.top_trigrams]

    output_path = Path(args.output) if args.output else ai_root / "collocations_glossary.json"
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_counts": {
            "sources_scanned": sources_scanned,
            "files_scanned": files_scanned,
            "total_tokens": total_tokens,
            "near_window": NEAR_WINDOW,
            "near_tokens_processed": total_tokens if total_tokens <= NEAR_TOKEN_CAP else 0,
        },
        "gazetteer": {
            "phrase_count": len(gazetteer_phrases),
            "paths": [str(p) for p in gazetteer_paths if p.exists()],
        },
        "glossary_terms": glossary_terms,
        "glossary_sources": [str(p) for p in glossary_text_sources if p.exists()],
        "bigrams": bigram_entries,
        "trigrams": trigram_entries,
        "near_pairs": [
            {"pair": f"{p[0]} {p[1]}", "count": cnt}
            for p, cnt in near_pairs.most_common(args.top_bigrams or 5000)
        ],
        "negated_terms": [
            {"term": term, "count": cnt}
            for term, cnt in negated_terms.most_common(200)
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("Collocation glossary written to:", output_path)
    print("Bigrams:", len(bigram_entries))
    print("Trigrams:", len(trigram_entries))


if __name__ == "__main__":
    main()
