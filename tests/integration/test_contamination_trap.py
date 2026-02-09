"""
Integration test — Sales vs Python Contamination Trap (Roadmap A6).

Feed a "Sales Person" profile to AI classification endpoints.
PASS: suggests "Account Executive", "Business Development", etc.
FAIL: suggests "Python Developer" (hardcoded data leaking into AI).
"""

import sys
import os
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


SALES_PROFILE = {
    "id": "contamination_trap_001",
    "role": "Sales Manager",
    "seniority": "Senior",
    "skills": [
        "B2B Sales", "Account Management", "CRM (Salesforce)",
        "Lead Generation", "Negotiation", "Pipeline Management",
        "Revenue Forecasting", "Client Relationship Management",
        "Presentation Skills", "Territory Planning"
    ],
    "experience_years": 12,
    "industry": "FMCG",
    "summary": (
        "Experienced Sales Manager with 12 years of B2B sales leadership. "
        "Managed £5M annual quota across UK and Ireland. Drove 30% YoY growth "
        "through strategic account development and team coaching."
    ),
    "experience": [
        {"title": "Regional Sales Manager", "company": "Unilever",
         "description": "Led team of 8 reps across Midlands region. Hit 115% of target."},
        {"title": "Account Executive", "company": "Diageo",
         "description": "Managed top 20 national accounts worth £12M combined revenue."},
    ],
}

# Keywords that SHOULD appear for a sales profile
GOOD_KEYWORDS = {
    "sales", "account", "business development", "revenue", "client",
    "commercial", "manager", "executive", "key account", "crm",
}

# Keywords that should NEVER appear
CONTAMINATION_KEYWORDS = {
    "python developer", "software engineer", "backend developer",
    "data scientist", "devops", "machine learning engineer", "react developer",
    "java developer", "full stack developer",
}


@pytest.mark.integration
class TestContaminationTrap:
    """Verify AIs don't suggest tech roles for a pure sales profile."""

    def test_skills_radar_no_tech_bias(self):
        """Radar endpoint should not over-weight Technical axis for a sales profile."""
        from services.backend_api.routers.insights import get_skills_radar

        # Create a mock loader that returns only our sales profile
        class MockLoader:
            def get_profiles(self):
                return [SALES_PROFILE]

        result = get_skills_radar(loader=MockLoader(), profile_id="contamination_trap_001")
        assert len(result["series"]) == 1
        series = result["series"][0]
        axes = result["axes"]

        # Find "Technical" axis index
        tech_idx = None
        for i, ax in enumerate(axes):
            if ax.lower() == "technical":
                tech_idx = i
                break

        # Find "Communication" or "Leadership" axis
        soft_indices = [i for i, ax in enumerate(axes)
                        if ax.lower() in ("communication", "leadership")]

        if tech_idx is not None and soft_indices:
            tech_val = series["values"][tech_idx]
            soft_max = max(series["values"][i] for i in soft_indices)
            # Technical should NOT dominate for a sales person
            assert tech_val <= soft_max + 30, (
                f"Technical ({tech_val}) shouldn't vastly exceed soft skills ({soft_max}) "
                f"for a pure sales profile. Possible data contamination."
            )

    def test_term_cloud_no_python(self):
        """Term cloud from sales-only data must not contain 'python' or 'react'."""
        from services.backend_api.routers.insights import get_term_cloud

        class MockLoader:
            def get_terms(self):
                freq = {}
                for s in SALES_PROFILE["skills"]:
                    freq[s.lower()] = 5
                return freq

        result = get_term_cloud(loader=MockLoader())
        terms_text = {t["text"].lower() for t in result["terms"]}

        for bad in CONTAMINATION_KEYWORDS:
            assert bad not in terms_text, (
                f"Contamination detected: '{bad}' appeared in term cloud "
                f"for a sales-only profile."
            )

    def test_graph_nodes_are_sales_skills(self):
        """Network graph from a sales profile should contain sales skills, not tech."""
        from services.backend_api.routers.insights import get_graph_data

        class MockLoader:
            def get_profiles(self):
                return [SALES_PROFILE]

        elements = get_graph_data(loader=MockLoader())
        # Elements is a list of nodes + edges
        labels = []
        for el in elements:
            data = el.get("data", {})
            if "label" in data:
                labels.append(data["label"].lower())

        labels_str = " ".join(labels)
        for bad in CONTAMINATION_KEYWORDS:
            assert bad not in labels_str, (
                f"Contamination: '{bad}' found in graph labels for sales profile."
            )

        # At least some sales skills should be present
        has_sales_skill = any(
            any(kw in lbl for kw in GOOD_KEYWORDS)
            for lbl in labels
        )
        assert has_sales_skill, (
            f"No sales-related skills in graph for a sales profile. Labels: {labels[:10]}"
        )
