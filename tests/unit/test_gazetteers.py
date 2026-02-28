"""
Gazetteer data integrity tests.
Validates every gazetteer JSON file for structure, content quality,
uniqueness, and completeness.

Marked @pytest.mark.slow — skipped in the default test run.
Run explicitly:  pytest -m slow tests/unit/test_gazetteers.py
"""
import json, pathlib, pytest

pytestmark = pytest.mark.slow          # skip unless `pytest -m slow`

GAZ_DIR = pathlib.Path(r"L:\antigravity_version_ai_data_final\ai_data_final\gazetteers")
GAZ_LOCAL = pathlib.Path(r"C:\careertrojan\data\ai_data_final\gazetteers")

# Only include proper gazetteer files — exclude backups (.bak*), temp, etc.
def _gazetteer_files():
    """Return sorted list of real gazetteer JSON files (no backups)."""
    if not GAZ_DIR.exists():
        return []
    return sorted(
        p for p in GAZ_DIR.glob("*.json")
        if ".bak" not in p.name and not p.name.startswith("_")
    )

EXPECTED_FILES = [
    "abbreviations.json", "biotech_pharma.json", "certifications.json",
    "cloud_platforms.json", "databases_architecture.json", "devops.json",
    "engineering.json", "financial_services.json", "hr_recruitment.json",
    "industrial_automation.json", "industry_terms.json", "job_titles.json",
    "manufacturing.json", "marketing.json", "methodologies.json",
    "oil_gas.json", "science_fundamentals.json", "soft_skills.json",
    "tech_skills.json",
]


class TestGazetteerStructure:
    """Validate JSON structure of each gazetteer."""

    @pytest.fixture(params=_gazetteer_files(), ids=lambda p: p.name)
    def gaz_file(self, request):
        return request.param

    def test_valid_json(self, gaz_file):
        data = json.loads(gaz_file.read_text("utf-8"))
        assert isinstance(data, dict), f"{gaz_file.name}: root must be a dict"

    def test_has_terms_or_abbreviations(self, gaz_file):
        data = json.loads(gaz_file.read_text("utf-8"))
        if gaz_file.name in ("learned_collocations.json", "term_evolution.json"):
            pytest.skip("special-purpose file")
        has_terms = "terms" in data or "abbreviations" in data
        assert has_terms, f"{gaz_file.name}: must have 'terms' or 'abbreviations' key"

    def test_terms_is_list_of_strings(self, gaz_file):
        data = json.loads(gaz_file.read_text("utf-8"))
        if "terms" not in data:
            pytest.skip("no terms key")
        assert isinstance(data["terms"], list)
        for t in data["terms"]:
            assert isinstance(t, str), f"non-string term: {t!r}"

    def test_no_empty_terms(self, gaz_file):
        data = json.loads(gaz_file.read_text("utf-8"))
        for t in data.get("terms", []):
            assert t.strip(), f"empty term in {gaz_file.name}"

    def test_terms_are_sorted(self, gaz_file):
        data = json.loads(gaz_file.read_text("utf-8"))
        terms = data.get("terms", [])
        if terms:
            assert terms == sorted(terms), f"{gaz_file.name}: terms not sorted"

    def test_no_duplicate_terms(self, gaz_file):
        data = json.loads(gaz_file.read_text("utf-8"))
        terms = data.get("terms", [])
        normalized = [" ".join(t.lower().split()) for t in terms]
        dupes = [t for t in normalized if normalized.count(t) > 1]
        assert not dupes, f"{gaz_file.name}: duplicates: {set(dupes)}"


class TestGazetteerCompleteness:
    """Validate all expected files exist and sync is correct."""

    def test_all_expected_files_exist(self):
        missing = [f for f in EXPECTED_FILES if not (GAZ_DIR / f).exists()]
        assert not missing, f"Missing gazetteers: {missing}"

    def test_minimum_term_counts(self):
        minimums = {
            "tech_skills.json": 200,
            "job_titles.json": 300,
            "engineering.json": 300,
            "financial_services.json": 400,
            "oil_gas.json": 250,
            "manufacturing.json": 150,
        }
        for fname, expected_min in minimums.items():
            fpath = GAZ_DIR / fname
            if fpath.exists():
                data = json.loads(fpath.read_text("utf-8"))
                count = len(data.get("terms", []))
                assert count >= expected_min, \
                    f"{fname}: only {count} terms, expected >= {expected_min}"

    def test_local_sync_matches_source(self):
        """L: and C: gazetteers should be identical."""
        if not GAZ_LOCAL.exists():
            pytest.skip("local mirror not available")
        for f in GAZ_DIR.glob("*.json"):
            local = GAZ_LOCAL / f.name
            if local.exists():
                src = json.loads(f.read_text("utf-8"))
                dst = json.loads(local.read_text("utf-8"))
                assert src == dst, f"{f.name}: L: and C: differ"

    def test_total_terms_above_threshold(self):
        total = 0
        for f in GAZ_DIR.glob("*.json"):
            data = json.loads(f.read_text("utf-8"))
            total += len(data.get("terms", []))
            total += len(data.get("abbreviations", {}))
        assert total >= 3000, f"Total terms {total} < 3000 minimum"
