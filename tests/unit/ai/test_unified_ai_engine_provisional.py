import pytest


def _get_learning_table_class():
    try:
        from services.backend_api.services.ai.unified_ai_engine import AILearningTable
        return AILearningTable
    except Exception as exc:  # pragma: no cover - optional heavy AI stack variance
        pytest.skip(f"Unified AI engine optional deps unavailable: {exc}")


@pytest.mark.unit
def test_learning_table_terminology_learns_immediately(tmp_path):
    AILearningTable = _get_learning_table_class()
    db_path = tmp_path / "ai_learning_test.db"
    table = AILearningTable(db_path=str(db_path))

    should_learn = table.add_term("vector-store", "terminology", context="resume_parser")

    assert should_learn is True
    learned = table.get_learned_terms("terminology")
    assert "terminology:vector-store" in learned


@pytest.mark.unit
def test_learning_table_words_need_threshold(tmp_path):
    AILearningTable = _get_learning_table_class()
    db_path = tmp_path / "ai_learning_test.db"
    table = AILearningTable(db_path=str(db_path))

    should_learn = table.add_term("synergy", "words", context="profile")

    assert should_learn is False
    stats = table.get_stats()
    assert stats["categories"]["words"]["threshold"] == 5
