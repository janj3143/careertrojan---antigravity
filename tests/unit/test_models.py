"""
Unit tests — DB models instantiation (no real DB needed).
"""

import sys
import os
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")


@pytest.mark.unit
class TestModels:

    def test_user_model_fields(self):
        from services.backend_api.db.models import User
        u = User(email="a@b.com", hashed_password="xxx", full_name="Test")
        assert u.email == "a@b.com"
        # Column defaults are server-side; verify column has default defined
        assert User.__table__.c.role.default.arg == "user"
        assert User.__table__.c.is_active.default.arg is True

    def test_job_model_fields(self):
        from services.backend_api.db.models import Job
        j = Job(title="Engineer", company="ACME", description="Build stuff")
        assert j.title == "Engineer"
        assert j.company == "ACME"

    def test_resume_model_fields(self):
        from services.backend_api.db.models import Resume
        r = Resume(user_id=1, file_path="/cv/test.pdf")
        assert r.file_path == "/cv/test.pdf"
        # Column defaults are server-side; verify column has default defined
        assert Resume.__table__.c.version.default.arg == 1
        assert Resume.__table__.c.is_primary.default.arg is False

    def test_mentor_model_fields(self):
        from services.backend_api.db.models import Mentor
        m = Mentor(user_id=1, specialty="Tech", hourly_rate=50.0)
        assert m.specialty == "Tech"
        assert m.hourly_rate == 50.0

    def test_base_has_metadata(self):
        from services.backend_api.db.models import Base
        tables = Base.metadata.tables
        assert "users" in tables
        assert "jobs" in tables
        assert "resumes" in tables
        assert "mentors" in tables
        assert "mentorships" in tables
