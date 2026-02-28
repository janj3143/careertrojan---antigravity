from services.backend_api.models.spider_covey import SpiderAxis, SpiderProfile
from services.backend_api.services.covey_builder import build_covey_action_lens, load_action_library_from_json


def test_covey_builder_returns_actions_for_matching_axes():
    spider = SpiderProfile(
        profile_id="spider-1",
        job_family="default",
        cohort_id="peer-a",
        axes=[
            SpiderAxis(
                key="evidence_strength",
                label="Evidence",
                score=38,
                confidence=0.8,
                peer_percentile=18,
                missing_evidence=["quantified outcomes"],
            ),
            SpiderAxis(
                key="ats_coverage",
                label="ATS Coverage",
                score=45,
                confidence=0.75,
                peer_percentile=24,
                missing_evidence=["target keywords"],
            ),
            SpiderAxis(
                key="clarity_structure",
                label="Clarity",
                score=52,
                confidence=0.7,
                peer_percentile=33,
                missing_evidence=["bullet focus"],
            ),
        ],
    )

    templates = load_action_library_from_json(
        "services/backend_api/data/action_library.json"
    )
    lens = build_covey_action_lens(spider=spider, action_templates=templates, top_n=10)

    assert lens.actions
    assert lens.spider_profile_id == "spider-1"
    assert all(action.axis_effects for action in lens.actions)
    assert all(action.because.gap_axis_keys for action in lens.actions)
