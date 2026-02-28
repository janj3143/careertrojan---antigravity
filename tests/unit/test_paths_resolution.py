"""
Unit tests — shared runtime path resolution.
"""

from pathlib import Path

import pytest

from services.shared.paths import CareerTrojanPaths


@pytest.fixture(autouse=True)
def _clear_path_env(monkeypatch):
    for key in [
        "CAREERTROJAN_DATA_ROOT",
        "CAREERTROJAN_AI_DATA",
        "CAREERTROJAN_PARSER_ROOT",
        "CAREERTROJAN_USER_DATA",
        "CAREERTROJAN_USER_DATA_MIRROR",
        "CAREERTROJAN_APP_ROOT",
        "CAREERTROJAN_WORKING_ROOT",
        "CAREERTROJAN_MODELS",
        "CAREERTROJAN_APP_LOGS",
    ]:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.unit
class TestCareerTrojanPaths:
    def test_parent_data_root_resolves_ai_data_child(self, tmp_path, monkeypatch):
        data_root = tmp_path / "dataset"
        ai_data_final = data_root / "ai_data_final"
        ai_data_final.mkdir(parents=True)

        monkeypatch.setenv("CAREERTROJAN_DATA_ROOT", str(data_root))
        resolved = CareerTrojanPaths()

        expected_user_dir = "USER DATA" if resolved.is_windows else "user_data"
        assert resolved.data_root == data_root
        assert resolved.ai_data_final == ai_data_final
        assert resolved.parser_root == data_root / "automated_parser"
        assert resolved.user_data == data_root / expected_user_dir

    def test_ai_data_root_value_is_normalized_to_parent(self, tmp_path, monkeypatch):
        ai_data_final = tmp_path / "dataset" / "ai_data_final"
        ai_data_final.mkdir(parents=True)

        monkeypatch.setenv("CAREERTROJAN_DATA_ROOT", str(ai_data_final))
        resolved = CareerTrojanPaths()

        assert resolved.data_root == ai_data_final.parent
        assert resolved.ai_data_final == ai_data_final
        assert resolved.parser_root == ai_data_final.parent / "automated_parser"

    def test_explicit_ai_data_env_override_is_honored(self, tmp_path, monkeypatch):
        data_root = tmp_path / "dataset"
        (data_root / "ai_data_final").mkdir(parents=True)

        explicit_ai_data = tmp_path / "custom" / "ai_data_final"
        explicit_ai_data.mkdir(parents=True)

        monkeypatch.setenv("CAREERTROJAN_DATA_ROOT", str(data_root))
        monkeypatch.setenv("CAREERTROJAN_AI_DATA", str(explicit_ai_data))
        resolved = CareerTrojanPaths()

        assert resolved.data_root == data_root
        assert resolved.ai_data_final == explicit_ai_data

    def test_explicit_constructor_data_root_is_normalized(self, tmp_path):
        ai_data_final = tmp_path / "dataset" / "ai_data_final"
        ai_data_final.mkdir(parents=True)

        resolved = CareerTrojanPaths(data_root=ai_data_final)

        assert resolved.data_root == ai_data_final.parent
        assert resolved.ai_data_final == ai_data_final
