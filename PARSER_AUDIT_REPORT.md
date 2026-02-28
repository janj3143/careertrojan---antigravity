# CareerTrojan Automated Parser System — Deep-Dive Audit Report
**Date:** 2026-02-24  
**Scope:** All parser files in `services/backend_api/services/`, `services/ai_engine/`, `utils/`, and `L:\antigravity_version_ai_data_final\automated_parser\`

---

## 1. Parser File Inventory

| # | File | Lines | Status |
|---|------|------:|--------|
| 1 | `services/backend_api/services/email_parser.py` | 163 | **GOOD** — Complete, working |
| 2 | `services/backend_api/services/resume_parser.py` | 1,273 | **GOOD** — Most comprehensive parser |
| 3 | `services/backend_api/services/resume_universal_parser.py` | 261 | **WARNING** — Depends on `enrichment.ats_scorer` + `frontend.utils.resume_nlp` |
| 4 | `services/backend_api/services/email_contact_parser.py` | 73 | **WARNING** — Enrichment stub |
| 5 | `services/backend_api/services/data_parser_service.py` | 315 | **GOOD** — Metrics/quality service |
| 6 | `services/backend_api/services/education_parser.py` | 43 | **WARNING** — Thin wrapper, enrichment stub |
| 7 | `services/backend_api/services/experience_parser.py` | 25 | **WARNING** — Thin wrapper, enrichment stub |
| 8 | `services/backend_api/services/company_parser.py` | 18 | **WARNING** — Ultra-thin wrapper |
| 9 | `services/backend_api/services/job_description_parser.py` | 76 | **GOOD** — Real extraction + web enrichment |
| 10 | `services/backend_api/services/job_title_parser.py` | 19 | **WARNING** — Thin wrapper |
| 11 | `services/backend_api/services/salary_parser.py` | 21 | **WARNING** — Text-only, no PDF/DOCX salary scan |
| 12 | `services/backend_api/services/company_intelligence_parser.py` | 359 | **GOOD** — Full web enrichment + SQLite |
| 13 | `services/backend_api/services/keyword_extractor.py` | 83 | **GOOD** — spaCy NLP + TF-IDF |
| 14 | `services/backend_api/utils/file_parser.py` | 153 | **GOOD** — Robust multi-format text extraction |
| 15 | `services/ai_engine/collocation_engine.py` | 1,573 | **GOOD** — Full self-learning NLP engine |

**Total lines across parser system: ~4,455**

---

## 2. Per-File Findings

### 2.1 `email_parser.py` (163 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **GOOD** | Fully functional — extract, parse, save CSV/JSON/stats |
| Email regex | **GOOD** | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` — tested, works for standard emails incl. `+tag`, subdomains. No false positives on tested inputs. |
| Phone regex | **WARNING** | `\b(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}\b` — works for UK/US phones BUT: (a) drops the leading `+` in captures (`+44` → `44`); (b) drops leading `(` in grouped numbers (`(212) 555-1234` → `212) 555-1234`). No `_validate_phones()` here unlike `resume_parser.py`. |
| Name regex | **WARNING** | `Name[:\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)*)` — only works if text literally contains `"Name: John Smith"`. Will NOT match names from CV headers, email signatures, or unstructured text. |
| Error handling | **GOOD** | Every extraction wrapped in try/except, graceful empty-string fallback |
| Dead code | **GOOD** | None found |
| Imports | **GOOD** | All valid, optional imports guarded |
| Exclude domain | **GOOD** | Correctly excludes `@johnston-vere.co.uk` (internal emails) |
| CRITICAL | Phone regex false positives on dates are NOT filtered here (no `_validate_phones`) |

### 2.2 `resume_parser.py` (1,273 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **GOOD** | Full pipeline: scan → categorize → extract → process → save |
| Email regex | **GOOD** | Same pattern — works well |
| Phone regex | **GOOD** | Has `_validate_phones()` static method that rejects <7 or >15 digit matches AND filters dates via `^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}$` pattern. This is the BEST phone validation in the system. |
| Skills extraction | **GOOD** | 40+ skill patterns with word-boundary regex, special handling for ambiguous tokens (`r`, `go`, `sap`, `git`, `vue`). Engineering-domain skills included (piping, commissioning, HSE, ISO). |
| Education extraction | **GOOD** | Regex patterns for Bachelor/Master/PhD with field capture |
| Experience extraction | **WARNING** | Simplistic — only matches literal job title strings ("software engineer", "developer", "analyst" etc). Does NOT parse company name, date ranges, or full work history sections. |
| Error handling | **GOOD** | `LoggingMixin` + `SafeOperationsMixin` from utils |
| Dead code | **GOOD** | None — all methods are called |
| Imports | **GOOD** | `LoggingMixin`, `SafeOperationsMixin`, `pandas` — all valid |
| L: drive scanner | **WARNING** | `_discover_data_directories()` requires env var `CAREERTROJAN_INCLUDE_ABSOLUTE_DATA_FALLBACK=true` to include L: drive. Defaults to OFF. |

### 2.3 `resume_universal_parser.py` (261 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **WARNING** | Depends on `enrichment.ats_scorer.ATSScorer` and `frontend.utils.resume_nlp.extract_profile_data_from_file` — if those imports fail, falls back to basic text read + regex. |
| Import risk | **CRITICAL** | `from enrichment.ats_scorer import ATSScorer` — will crash if the enrichment module isn't on Python path. No try/except guard on this import. |
| Smart enrichment | **GOOD** | ATSScorer integration for job-target scoring |
| Quality scoring | **GOOD** | 0-10 scale checking name, email, phone, skills count, experience count, word count |
| Seniority detection | **GOOD** | Keyword-based ("CEO" → Executive, "Director" → Director, etc.) |
| Industry detection | **GOOD** | Multi-domain keyword scoring (Tech, Finance, Healthcare, Marketing) |
| CLI interface | **GOOD** | `argparse` with `--in`, `--out`, `--job`, `--verbose` |

### 2.4 `email_contact_parser.py` (73 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **WARNING** | Working extraction + dedup, but `enrich_contacts()` is a **stub** (returns input unchanged) |
| Phone regex | Same as `email_parser.py` — no `_validate_phones()` |
| LINKEDIN_REGEX | **GOOD** | Extracts LinkedIn profile URLs |
| COMPANY_REGEX | **GOOD** | `Company[:\s]+([A-Za-z0-9 &.,-]+)` — only matches label-based text |
| File support | **WARNING** | `extract_contacts()` only handles `.txt` and `.json` — comment says "Add PDF, DOCX, CSV, XLSX support as needed" |
| Deduplication | **GOOD** | By (email + phone) composite key |

### 2.5 `data_parser_service.py` (315 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **GOOD** | Quality metrics service, not a parser itself |
| Purpose | Dashboard analytics — reprocessing candidates, unknown formats, performance metrics, data quality |
| Dependencies | `pandas` only — safe |
| Error handling | **GOOD** | Every method wrapped in try/except with defaults |

### 2.6 `education_parser.py` (43 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **WARNING** | Delegate to `ResumeParser._extract_education_from_text()` — thin wrapper |
| Enrichment | **STUB** | `enrich_education()` returns input unchanged. Comment: "to be implemented in enrichment/education_enricher.py" |
| `parse_all_education()` | **WARNING** | Only globs `*.pdf` — misses `.docx`, `.doc`, `.txt` |

### 2.7 `experience_parser.py` (25 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **WARNING** | Same thin-wrapper pattern as education_parser |
| Enrichment | **STUB** | `enrich_experience()` returns input unchanged |
| `parse_all_experience()` | **WARNING** | Only globs `*.pdf` |

### 2.8 `company_parser.py` (18 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **WARNING** | Ultra-thin wrapper — delegates everything to `ResumeParser._extract_company_data_from_file()` |
| `parse_all_companies()` | **WARNING** | Only globs `*.pdf` |

### 2.9 `job_description_parser.py` (76 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **GOOD** | Real section parsing — extracts title, description, requirements list |
| Title regex | **GOOD** | Matches `Job Title:`, `Position:`, `Role:` headers |
| Requirements parsing | **GOOD** | Reads bullet/dash/numbered list items until blank line |
| Web enrichment | **GOOD** | Optional `web_url` param for live scraping via `robust_get` |
| Enrichment | **STUB** | `enrich_job_descriptions()` returns input unchanged |

### 2.10 `job_title_parser.py` (19 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **WARNING** | Thin wrapper — delegates to `ResumeParser._extract_experience_from_text()` then extracts unique titles |
| `parse_all_job_titles()` | **WARNING** | Only globs `*.pdf` |

### 2.11 `salary_parser.py` (21 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **WARNING** | Only extracts salary from `.txt` files. All other formats return `None`. |
| Salary regex | **GOOD** | `[\$£€]\s*[\d,]+(?:\.\d{2})?(?:\s*[kK])?` — properly handles $120,000, £80k, €50,000.00 |
| No fabrication | **GOOD** | Returns `None` if nothing found — never fabricates |
| **MISSING** | No support for salary ranges ("$80,000 - $120,000"), "per annum"/"p.a.", or non-currency patterns ("120k") |

### 2.12 `company_intelligence_parser.py` (359 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **GOOD** | Full pipeline: DuckDuckGo search → website scraping → logo extraction → industry inference → SQLite storage |
| Robots.txt | **GOOD** | Checks robots.txt before every fetch |
| Rate limiting | **GOOD** | `polite_sleep` between requests, domain locks for concurrency |
| Industry heuristic | **GOOD** | 7-category keyword scoring (Technology, Finance, Healthcare, Energy, Manufacturing, Consulting, Retail) |
| Job linking | **GOOD** | `link_job_to_company()` + `get_jobs_for_company()` — bidirectional |
| **CRITICAL** | Top-of-file imports are broken: `from advanced_web_scraper import robust_get` (bare module import, not relative) and sidebar code runs at module import time |
| TODO | 1 TODO: "Add user-facing analytics to probe company/job history for career pathing and aspiration matching" |

### 2.13 `keyword_extractor.py` (83 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **GOOD** | spaCy noun chunks + named entities + TF-IDF similarity + acronym extraction |
| Dependencies | **WARNING** | `spacy.load("en_core_web_sm")` runs at module import time. If model isn't installed → crash |
| User profile hooks | **GOOD** | `attach_keywords_to_user_profile()`, `enrich_and_attach_keywords()` |

### 2.14 `file_parser.py` (153 lines)

| Check | Rating | Detail |
|-------|--------|--------|
| Code completeness | **GOOD** | Handles: txt, md, rtf, html, zip, pdf, docx, images (OCR via pytesseract) |
| Graceful degradation | **GOOD** | Every optional dependency (PyPDF2, docx, PIL, etc.) wrapped in try/except ImportError |
| Async | **NOTE** | `extract_text_from_upload()` is async — designed for FastAPI UploadFile |
| **MISSING** | No synchronous `extract_text(file_path)` function. The `job_description_parser.py` tries to import `from services.backend_api.utils.file_parser import extract_text` which doesn't exist. |
| ZIP handling | **GOOD** | Limits to 15 files, 200K chars — prevents zip bombs |

---

## 3. L: Drive `automated_parser` Directory Structure

```
L:\antigravity_version_ai_data_final\automated_parser\
├── 843 top-level files
│   ├── .pdf: 335   (CVs, resumes, job descriptions)
│   ├── .docx: 150  (CVs, templates, proposals)
│   ├── .doc: 119   (Legacy Word documents)
│   ├── .msg: 90    (Outlook emails with attachments)
│   ├── .csv: 49    (Candidate/Company/Contact data, LinkedIn exports)
│   ├── .xlsx: 38   (Spreadsheets, candidate records)
│   ├── .zip: 26    (Archives of projects, emails, invoices)
│   └── others: 36  (.xls, .lnk, .odt, .txt, .jpg, .pptx, .rtf, .gif, .dotx, .md, .png)
│
├── 41 subdirectories (key ones):
│   ├── Candidate/        → 155,195 files (!!!) — MASSIVE candidate database
│   ├── Holly back up/    → 29,205 files
│   ├── ai_data/          → 16,953 files
│   ├── David/            → 4,876 files
│   ├── Consultant docs/  → 3,672 files
│   ├── Companies/        → 2,158 files
│   ├── David & Sophie/   → 1,023 files
│   ├── Claire's Documents/ → 714 files
│   ├── Existing Candidates/ → 696 files
│   ├── Clients/          → 609 files
│   ├── 61200-61500/      → 508 files (numbered project folders)
│   └── ... and 30 more subdirectories
│
└── TOTAL: ~215,000+ files across all subdirectories
```

**This is NOT a code directory.** It is a massive document corpus of real CVs, resumes, job descriptions, emails, company data, LinkedIn exports, and historical recruitment records spanning 2011-2025. No Python scripts found in this directory.

---

## 4. Critical & Warning Summary

### CRITICAL Issues

| # | Issue | File | Impact |
|---|-------|------|--------|
| C1 | `from enrichment.ats_scorer import ATSScorer` — unguarded import will crash if module not on path | `resume_universal_parser.py:20` | Module import failure |
| C2 | Top-of-file `from advanced_web_scraper import robust_get` and sidebar code runs at import time | `company_intelligence_parser.py:1-20` | Module import failure in non-Streamlit contexts |
| C3 | `from services.backend_api.utils.file_parser import extract_text` — function doesn't exist | `job_description_parser.py:33` | `ImportError` on `extract_text` — file_parser only has `extract_text_from_upload` (async) |
| C4 | Phone regex in `email_parser.py` and `email_contact_parser.py` lacks `_validate_phones()` — dates and short numbers can false-positive | `email_parser.py`, `email_contact_parser.py` | Polluted phone data |

### WARNING Issues

| # | Issue | Files |
|---|-------|-------|
| W1 | 5 enrichment functions are **stubs** returning input unchanged | `education_parser.py`, `experience_parser.py`, `email_contact_parser.py`, `job_description_parser.py`, `salary_parser.py` |
| W2 | 4 parser wrappers only glob `*.pdf` — miss `.docx`, `.doc`, `.txt` | `education_parser.py`, `experience_parser.py`, `company_parser.py`, `job_title_parser.py` |
| W3 | `salary_parser.py` only reads `.txt` files — cannot extract salary from PDF/DOCX | `salary_parser.py` |
| W4 | Name regex (`Name[:\s]+...`) only works with labeled data, not free-text CVs | `email_parser.py`, `email_contact_parser.py` |
| W5 | Experience extraction is simplistic — no company name, date range, or section parsing | `resume_parser.py:_extract_experience_from_text()` |
| W6 | `spacy.load("en_core_web_sm")` at import time with no fallback | `keyword_extractor.py` |
| W7 | `email_contact_parser.py` only supports `.txt` and `.json` for file extraction | `email_contact_parser.py` |

### MISSING Capabilities

| # | What's Missing | Where It Should Be |
|---|----------------|-------------------|
| M1 | `.msg` (Outlook) file parsing in individual parsers | All parsers — L: drive has 90 `.msg` files at top level + more in subdirs |
| M2 | `.doc` (legacy Word) text extraction | Only `file_parser.py` handles `.docx`, not `.doc` |
| M3 | Synchronous `extract_text(file_path: Path) -> str` utility | `file_parser.py` — only has async version |
| M4 | `.odt` file parsing in parsers | `file_parser.py` has import for `odf` but no handler in parsers |
| M5 | Salary range parsing ("$80K - $120K", "per annum") | `salary_parser.py` |
| M6 | Bulk `.msg` email+attachment extraction pipeline | Needed for the 90+ `.msg` files in automated_parser |

### GOOD Findings

| # | What Works Well | File |
|---|----------------|------|
| G1 | Email regex is solid — handles subdomains, `+tag`, `.co.uk` etc. | All parser files |
| G2 | `resume_parser.py` has the best phone validation (`_validate_phones`) in the system | `resume_parser.py` |
| G3 | Internal email filtering (`@johnston-vere.co.uk`) prevents self-pollution | `email_parser.py` |
| G4 | Skills extraction is domain-aware — chemical engineering, piping, HSE, ISO covered | `resume_parser.py` |
| G5 | Company intelligence has full web enrichment pipeline with robots.txt respect | `company_intelligence_parser.py` |
| G6 | File parser has OCR capability for image-based CVs | `file_parser.py` |
| G7 | Keyword extractor uses NLP (spaCy) not just regex | `keyword_extractor.py` |
| G8 | `data_parser_service.py` provides real quality metrics for the admin dashboard | `data_parser_service.py` |
| G9 | Duplicate email deduplication in `email_parser.py` and `email_contact_parser.py` | Both files |

---

## 5. Parser ↔ Collocation Engine Integration Assessment

### Current State: **NO DIRECT INTEGRATION**

The collocation engine (`services/ai_engine/collocation_engine.py`, 1,573 lines) and the parser system operate as **completely independent pipelines**:

- **Collocation engine** reads gazetteers from `L:\antigravity_version_ai_data_final\ai_data_final\gazetteers\`, learns phrases from user interactions, and provides phrase-aware tokenization.
- **Parser system** reads raw documents from `L:\antigravity_version_ai_data_final\automated_parser\` and extracts contacts/skills/education.
- There is **zero import** of the collocation engine from any parser file.
- The only connection is a `TODO` comment in `routers/intelligence.py`: _"TODO: wire into CollocationEngine / NER pipeline for real extraction"_
- The backend `main.py` does bootstrap the collocation engine at startup, but no parser uses it.

### Integration Potential: **HIGH**

The collocation engine could dramatically improve parsing in several ways:

| Use Case | How | Impact |
|----------|-----|--------|
| **Email search in parsed docs** | Feed extracted text from PDF/DOCX through `collocation_engine.tokenize_with_phrases()` before email regex — the phrase-aware tokenizer would preserve multi-word terms while the email regex runs on the remainder | Slightly better recall for emails buried in dense text |
| **Skills extraction** | Replace the 40-pattern regex list in `resume_parser._extract_skills_from_text()` with the collocation engine's gazetteer-backed `PhraseMatcher` + `EntityRuler`. The gazetteers already contain 1000s of domain skills, certifications, tools. | **10x improvement** in skills coverage |
| **Job title normalization** | Use the collocation engine's learned phrases to normalize free-text job titles (e.g., "Senior Process Eng." → "Senior Process Engineer") | Better job matching |
| **Company name extraction** | The collocation engine's `PhraseSpan` with negation detection could identify company mentions more accurately than the current regex | Better company linking |
| **Continuous learning** | Feed parser output (extracted skills, titles, company names) back into `collocation_engine.enrichment_ingest()` so the engine learns from every parsed document | Self-improving system |

### Recommended Integration Architecture

```
Document Intake (L: drive automated_parser/)
    │
    ▼
file_parser.extract_text()  ← needs sync version (M3)
    │
    ▼
collocation_engine.tokenize_with_phrases(text)
    │
    ├─→ email_parser.EMAIL_REGEX on tokenized text
    ├─→ PhraseMatcher for skills (replaces regex list)
    ├─→ EntityRuler for job titles, certifications
    ├─→ resume_parser for education, experience
    │
    ▼
enrichment_ingest(extracted_terms)  ← feed back to engine
    │
    ▼
persist_learned_phrases()  ← grows gazetteers over time
```

---

## 6. Recommendations (Priority Order)

1. **FIX C1-C3** — Guard the unprotected imports in `resume_universal_parser.py`, `company_intelligence_parser.py`, and `job_description_parser.py`
2. **FIX C4** — Add `_validate_phones()` from `resume_parser.py` to `email_parser.py` and `email_contact_parser.py`
3. **Add sync `extract_text()`** to `file_parser.py` (M3) — most parsers need this
4. **Wire collocation engine into skills extraction** — highest-impact integration
5. **Expand file glob patterns** in thin wrapper parsers from `*.pdf` to include `.docx`, `.doc`, `.txt`
6. **Add `.msg` parsing** — 90+ Outlook emails in automated_parser are currently unparseable by parsers
7. **Implement enrichment stubs** — the 5 stub functions are ready for wiring

---

*End of audit report.*
