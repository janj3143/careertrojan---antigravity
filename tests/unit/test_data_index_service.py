"""
Unit tests for the AI Data Index Service
"""

import pytest
import json
import tempfile
from pathlib import Path
from dataclasses import asdict
from unittest.mock import patch, MagicMock

from services.backend_api.services.ai_data_index_service import (
    AIDataIndexService,
    AIDataIndexSummary,
    ParserIndexSummary,
    ParserRunRecord,
    CategoryStats,
    _as_list,
    _extract_skills,
    _extract_industries,
    _extract_locations,
    _safe_read_json,
    _file_hash,
)


class TestFieldExtraction:
    """Test field extraction utilities."""

    def test_as_list_none(self):
        assert _as_list(None) == []

    def test_as_list_string(self):
        result = _as_list("Python, Java, Go")
        assert result == ["Python", "Java", "Go"]

    def test_as_list_string_with_semicolons(self):
        result = _as_list("Python; Java; Go")
        assert result == ["Python", "Java", "Go"]

    def test_as_list_string_with_pipes(self):
        result = _as_list("Python | Java | Go")
        assert result == ["Python", "Java", "Go"]

    def test_as_list_list(self):
        result = _as_list(["Python", "Java", "Go"])
        assert result == ["Python", "Java", "Go"]

    def test_as_list_list_with_empty(self):
        result = _as_list(["Python", "", "Java", "  ", "Go"])
        assert result == ["Python", "Java", "Go"]

    def test_extract_skills_simple(self):
        obj = {"skills": ["Python", "Machine Learning", "SQL"]}
        result = _extract_skills(obj)
        assert "Python" in result
        assert "Machine Learning" in result
        assert "SQL" in result

    def test_extract_skills_multiple_fields(self):
        obj = {
            "skills": ["Python"],
            "technical_skills": ["AWS"],
            "soft_skills": ["Leadership"],
        }
        result = _extract_skills(obj)
        assert "Python" in result
        assert "AWS" in result
        assert "Leadership" in result

    def test_extract_skills_nested_experience(self):
        obj = {
            "skills": ["Python"],
            "experience": [
                {"company": "Acme", "skills": ["Django", "Flask"]},
                {"company": "BigCorp", "skills": ["FastAPI"]},
            ],
        }
        result = _extract_skills(obj)
        assert "Python" in result
        assert "Django" in result
        assert "Flask" in result
        assert "FastAPI" in result

    def test_extract_industries(self):
        obj = {"industry": "Technology", "sector": "FinTech"}
        result = _extract_industries(obj)
        assert "Technology" in result
        assert "FinTech" in result

    def test_extract_locations(self):
        obj = {"location": "London", "city": "Manchester", "country": "UK"}
        result = _extract_locations(obj)
        assert "London" in result
        assert "Manchester" in result
        assert "UK" in result


class TestSafeReadJson:
    """Test JSON reading utility."""

    def test_read_valid_json(self, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test", "skills": ["Python"]}')

        result = _safe_read_json(json_file)
        assert result["name"] == "test"
        assert result["skills"] == ["Python"]

    def test_read_nonexistent_file(self, tmp_path):
        json_file = tmp_path / "nonexistent.json"
        result = _safe_read_json(json_file)
        assert result == {}

    def test_read_invalid_json(self, tmp_path):
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json {")

        result = _safe_read_json(json_file)
        assert result == {}


class TestFileHash:
    """Test file hashing utility."""

    def test_hash_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        result = _file_hash(test_file)
        assert len(result) == 32  # MD5 hex length
        assert result != ""

    def test_hash_nonexistent_file(self, tmp_path):
        test_file = tmp_path / "nonexistent.txt"
        result = _file_hash(test_file)
        assert result == ""

    def test_hash_same_content(self, tmp_path):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("same content")
        file2.write_text("same content")

        assert _file_hash(file1) == _file_hash(file2)


class TestAIDataIndexService:
    """Test the main index service."""

    @pytest.fixture
    def mock_paths(self, tmp_path):
        """Create mock paths structure."""
        ai_data_final = tmp_path / "ai_data_final"
        parser_root = tmp_path / "automated_parser"

        ai_data_final.mkdir(parents=True)
        parser_root.mkdir(parents=True)

        # Create some test categories
        profiles_dir = ai_data_final / "profiles"
        profiles_dir.mkdir()

        # Create test profile files
        for i in range(3):
            profile = {
                "name": f"Test User {i}",
                "skills": ["Python", "SQL", f"Skill{i}"],
                "industry": "Technology",
                "location": "London",
            }
            (profiles_dir / f"profile_{i}.json").write_text(json.dumps(profile))

        # Create test parser source files
        (parser_root / "resume1.pdf").write_text("fake pdf")
        (parser_root / "resume2.docx").write_text("fake docx")
        (parser_root / "data.csv").write_text("a,b,c")

        mock = MagicMock()
        mock.ai_data_final = ai_data_final
        mock.parser_root = parser_root
        return mock

    def test_index_ai_data(self, mock_paths):
        service = AIDataIndexService(paths=mock_paths)
        summary = service.index_ai_data()

        assert isinstance(summary, AIDataIndexSummary)
        assert summary.total_files == 3
        assert summary.unique_skills > 0
        assert "Python" in summary.top_skills
        assert "SQL" in summary.top_skills

    def test_index_parser_sources(self, mock_paths):
        service = AIDataIndexService(paths=mock_paths)
        summary = service.index_parser_sources()

        assert isinstance(summary, ParserIndexSummary)
        assert summary.total_sources == 3
        assert ".pdf" in summary.file_type_distribution
        assert ".docx" in summary.file_type_distribution
        assert ".csv" in summary.file_type_distribution

    def test_full_index(self, mock_paths):
        service = AIDataIndexService(paths=mock_paths)
        state = service.full_index()

        assert state.ai_data_summary is not None
        assert state.parser_summary is not None
        assert state.last_full_index is not None

    def test_record_parser_run(self, mock_paths):
        service = AIDataIndexService(paths=mock_paths)

        record = service.record_parser_run(
            run_id="test-run-001",
            started_at="2026-02-26T10:00:00Z",
            completed_at="2026-02-26T10:05:00Z",
            total_files=100,
            processed=95,
            skipped=3,
            errors=2,
            duration_seconds=300.0,
            file_types={".pdf": 50, ".docx": 45, ".csv": 5},
        )

        assert isinstance(record, ParserRunRecord)
        assert record.run_id == "test-run-001"
        assert record.total_files == 100
        assert record.processed == 95

    def test_get_parser_run_history(self, mock_paths):
        service = AIDataIndexService(paths=mock_paths)

        # Record a few runs
        for i in range(3):
            service.record_parser_run(
                run_id=f"run-{i}",
                started_at=f"2026-02-26T1{i}:00:00Z",
                completed_at=f"2026-02-26T1{i}:05:00Z",
                total_files=10 + i,
                processed=10 + i,
                skipped=0,
                errors=0,
                duration_seconds=300.0,
                file_types={},
            )

        history = service.get_parser_run_history(limit=10)
        assert len(history) == 3

    def test_search_skills(self, mock_paths):
        service = AIDataIndexService(paths=mock_paths)
        service.index_ai_data()

        results = service.search_skills("python", limit=10)
        assert len(results) > 0
        assert any(r["skill"].lower() == "python" for r in results)

    def test_search_industries(self, mock_paths):
        service = AIDataIndexService(paths=mock_paths)
        service.index_ai_data()

        results = service.search_industries("tech", limit=10)
        assert len(results) > 0

    def test_search_locations(self, mock_paths):
        service = AIDataIndexService(paths=mock_paths)
        service.index_ai_data()

        results = service.search_locations("london", limit=10)
        assert len(results) > 0

    def test_state_persistence(self, mock_paths):
        # First service indexes data
        service1 = AIDataIndexService(paths=mock_paths)
        service1.full_index()

        # Second service loads persisted state
        service2 = AIDataIndexService(paths=mock_paths)
        state = service2.get_state()

        assert state.ai_data_summary is not None
        assert state.last_full_index is not None


class TestCategoryStats:
    """Test CategoryStats dataclass."""

    def test_category_stats_creation(self):
        stats = CategoryStats(
            category="profiles",
            folder="profiles",
            file_count=100,
            total_size_bytes=1024000,
            oldest_file="2026-01-01T00:00:00",
            newest_file="2026-02-26T00:00:00",
        )

        assert stats.category == "profiles"
        assert stats.file_count == 100
        assert stats.total_size_bytes == 1024000

    def test_category_stats_asdict(self):
        stats = CategoryStats(
            category="profiles",
            folder="profiles",
            file_count=100,
            total_size_bytes=1024000,
        )

        result = asdict(stats)
        assert result["category"] == "profiles"
        assert result["file_count"] == 100


class TestParserRunRecord:
    """Test ParserRunRecord dataclass."""

    def test_parser_run_record_creation(self):
        record = ParserRunRecord(
            run_id="test-001",
            started_at="2026-02-26T10:00:00Z",
            completed_at="2026-02-26T10:05:00Z",
            total_files=100,
            processed=95,
            skipped=3,
            errors=2,
            duration_seconds=300.0,
            file_types={".pdf": 50, ".docx": 50},
        )

        assert record.run_id == "test-001"
        assert record.total_files == 100
        assert record.file_types[".pdf"] == 50


class TestDependencyDetection:
    """Test optional dependency detection."""

    def test_detect_optional_dependencies(self, tmp_path):
        mock_paths = MagicMock()
        mock_paths.ai_data_final = tmp_path / "ai_data_final"
        mock_paths.parser_root = tmp_path / "parser"
        mock_paths.ai_data_final.mkdir()
        mock_paths.parser_root.mkdir()

        service = AIDataIndexService(paths=mock_paths)
        deps = service._detect_optional_dependencies()

        # Should return a dict with expected keys
        assert "xlrd" in deps
        assert "extract_msg" in deps
        assert "openpyxl" in deps
        assert "python_docx" in deps
        assert "pdfplumber" in deps
        assert "pypdf2" in deps

        # All values should be booleans
        for key, value in deps.items():
            assert isinstance(value, bool)
