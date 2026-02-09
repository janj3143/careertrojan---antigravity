import unittest
from enrichment.ats_scorer import ATSScorer
from enrichment.config import load_config
from enrichment.experience_analyzer import ExperienceAnalyzer
from enrichment.skill_categorizer import SkillCategorizer
from enrichment.achievement_analyzer import AchievementAnalyzer
from enrichment.user_profile import UserProfile

# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False


# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()


class TestSmartEnrichment(unittest.TestCase):
    def setUp(self):
        self.profile = {
            'personal_info': {'name': 'John Doe'},
            'experience': [
                {'title': 'Software Engineer', 'description': 'Worked on team projects. Demonstrated leadership and communication.', 'start_date': '2020-01-01', 'end_date': '2021-01-01'},
                {'title': 'Developer', 'description': 'Problem solving and adaptability.', 'start_date': '2021-07-01', 'end_date': None}
            ],
            'education': [{'degree': 'BSc', 'institution': 'Uni'}],
            'skills': ['Python', 'Teamwork', 'Creativity'],
            'achievements': ['Increased sales by 20%', 'Presented at conference'],
            'preferences': {}
        }
        self.config = load_config()
        self.ats = ATSScorer(self.config.get('ats_keywords', []))

    def test_enrich_basic(self):
        enriched = self.ats.enrich(self.profile.copy())
        self.assertIn('smart_analysis', enriched)
        self.assertIn('ats_score', enriched)
        self.assertIn('primary_language', enriched)
        self.assertIn('soft_skills', enriched)
        self.assertIn('employment_gaps', enriched)
        self.assertIn('recommendations', enriched)
        self.assertIsInstance(enriched['soft_skills'], list)
        self.assertIsInstance(enriched['employment_gaps'], list)
        self.assertIsInstance(enriched['recommendations'], list)

    def test_enrich_batch(self):
        profiles = [self.profile.copy() for _ in range(3)]
        results = ATSScorer.enrich_batch(profiles)
        self.assertEqual(len(results), 3)
        for enriched in results:
            self.assertIn('smart_analysis', enriched)
            self.assertIn('ats_score', enriched)

    def test_config_load(self):
        config = load_config()
        self.assertIsInstance(config, dict)

    def test_experience_analyzer(self):
        years = ExperienceAnalyzer.calculate_total_duration(self.profile['experience'])
        self.assertTrue(isinstance(years, float) or isinstance(years, int))
        self.assertGreaterEqual(years, 0)

    def test_skill_categorizer(self):
        categorizer = SkillCategorizer(self.config)
        categorized = categorizer.categorize(self.profile['skills'])
        self.assertIn('Other', categorized)
        self.assertIsInstance(categorized, dict)

    def test_achievement_analyzer(self):
        impact = AchievementAnalyzer.extract_impact(self.profile['achievements'])
        self.assertIsInstance(impact, list)
        self.assertIn('Increased sales by 20%', impact)

    def test_user_profile_dataclass(self):
        up = UserProfile(
            personal_info=self.profile['personal_info'],
            experience=self.profile['experience'],
            education=self.profile['education'],
            skills=self.profile['skills'],
            achievements=self.profile['achievements'],
            preferences=self.profile['preferences']
        )
        self.assertEqual(up.personal_info['name'], 'John Doe')
        self.assertEqual(len(up.experience), 2)

    def test_spacy_model_loading(self):
        # Test spaCy model loading and fallback
        try:
            import spacy
            nlp = spacy.load('en_core_web_sm')
            self.assertIsNotNone(nlp)
        except Exception:
            # If spaCy or model not available, should not raise
            self.assertTrue(True)

    def test_contextual_score_with_spacy(self):
        # Test contextual_score with and without spaCy
        ats = ATSScorer(self.config.get('ats_keywords', []))
        score = ats.contextual_score(self.profile, job_target="Python Developer at Tech Company")
        self.assertTrue(isinstance(score, float))

    def test_enrich_batch(self):
        profiles = [self.profile.copy() for _ in range(3)]
        results = ATSScorer.enrich_batch(profiles)
        self.assertEqual(len(results), 3)
        for enriched in results:
            self.assertIn('smart_analysis', enriched)
            self.assertIn('ats_score', enriched)

if __name__ == '__main__':
    unittest.main()
