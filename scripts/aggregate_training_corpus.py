import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List


def extract_email(text: str) -> str:
    if not text:
        return ""
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    if not text:
        return ""
    match = re.search(r"\+?\d[\d\s().-]{7,}", text)
    return match.group(0).strip() if match else ""


def normalize_profile(profile: Dict) -> Dict:
    qualifications = profile.get("Qualifications") or ""
    career_summary = profile.get("Career Summary") or ""
    personal_details = profile.get("Personal Details") or ""

    skills = profile.get("skills") or []
    education = profile.get("education") or []
    work_experience = profile.get("work_experience") or []

    if qualifications:
        education.append(qualifications)
    if career_summary:
        work_experience.append(career_summary)

    email = profile.get("email") or extract_email(" ".join([personal_details, qualifications, career_summary]))
    phone = profile.get("phone") or extract_phone(" ".join([personal_details, qualifications, career_summary]))

    return {
        "skills": skills,
        "education": education,
        "work_experience": work_experience,
        "email": email,
        "phone": phone,
        "source": "profiles",
        "raw": profile,
    }


def normalize_parsed_resume(resume: Dict) -> Dict:
    skills = resume.get("skills") or []
    education = resume.get("education") or []
    work_experience = resume.get("experience") or resume.get("work_experience") or []
    raw_text = resume.get("raw_text") or ""
    email = resume.get("email") or extract_email(raw_text)
    phone = resume.get("phone") or extract_phone(raw_text)

    return {
        "skills": skills,
        "education": education,
        "work_experience": work_experience,
        "email": email,
        "phone": phone,
        "source": "parsed_resumes",
        "raw": resume,
    }


def iter_json_files(root: Path, limit: int = None) -> Iterable[Path]:
    count = 0
    for path in sorted(root.glob("*.json")):
        yield path
        count += 1
        if limit and count >= limit:
            break


def consolidate(ai_data_final: Path, output: Path, manifest: Path, limit: int = None) -> None:
    profiles_dir = ai_data_final / "profiles"
    parsed_resumes_dir = ai_data_final / "parsed_resumes"

    stats = {
        "profiles": 0,
        "parsed_resumes": 0,
        "written": 0,
        "errors": 0,
        "errors_detail": [],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as out_f:
        # Profiles
        if profiles_dir.exists():
            for path in iter_json_files(profiles_dir, limit):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    norm = normalize_profile(data)
                    out_f.write(json.dumps(norm, ensure_ascii=False) + "\n")
                    stats["profiles"] += 1
                    stats["written"] += 1
                except Exception as e:  # noqa: BLE001
                    stats["errors"] += 1
                    if len(stats["errors_detail"]) < 50:
                        stats["errors_detail"].append({"file": str(path.name), "error": str(e)})
        # Parsed resumes
        if parsed_resumes_dir.exists():
            for path in iter_json_files(parsed_resumes_dir, limit):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    norm = normalize_parsed_resume(data)
                    out_f.write(json.dumps(norm, ensure_ascii=False) + "\n")
                    stats["parsed_resumes"] += 1
                    stats["written"] += 1
                except Exception as e:  # noqa: BLE001
                    stats["errors"] += 1
                    if len(stats["errors_detail"]) < 50:
                        stats["errors_detail"].append({"file": str(path.name), "error": str(e)})

    manifest.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(stats, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate normalized training corpus")
    parser.add_argument("--ai-data-final", default="L:/Codec - Antigravity Data set/ai_data_final", help="Path to ai_data_final root")
    parser.add_argument("--output", default="L:/Codec - Antigravity Data set/ai_data_final/training_corpus.jsonl", help="Output NDJSON path")
    parser.add_argument("--manifest", default="L:/Codec - Antigravity Data set/ai_data_final/training_corpus_manifest.json", help="Manifest path")
    parser.add_argument("--limit", type=int, default=None, help="Optional cap per source")
    args = parser.parse_args()

    consolidate(Path(args.ai_data_final), Path(args.output), Path(args.manifest), args.limit)


if __name__ == "__main__":
    main()
