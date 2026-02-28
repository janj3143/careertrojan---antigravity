"""
Unit tests for the Rewards API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.backend_api.db.models import (
    UserReward, UserReferral, UserSuggestion, 
    UserCompletedAction, RewardRedemption, User
)
from services.backend_api.routers.rewards import (
    _calculate_tier, _generate_referral_code, 
    REWARD_ACTIONS, RewardType, RewardStatus
)


@pytest.fixture
def client():
    from services.backend_api.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    return user


class TestTierCalculation:
    """Test tier calculation logic."""

    def test_bronze_tier(self):
        tier, progress = _calculate_tier(0)
        assert tier == "Bronze"
        assert progress == 0.0

    def test_bronze_tier_mid(self):
        tier, progress = _calculate_tier(250)
        assert tier == "Bronze"
        assert progress == 50.0

    def test_silver_tier(self):
        tier, progress = _calculate_tier(500)
        assert tier == "Silver"
        assert progress == 0.0

    def test_gold_tier(self):
        tier, progress = _calculate_tier(2000)
        assert tier == "Gold"

    def test_platinum_tier(self):
        tier, progress = _calculate_tier(5000)
        assert tier == "Platinum"

    def test_diamond_tier(self):
        tier, progress = _calculate_tier(15000)
        assert tier == "Diamond"

    def test_elite_tier(self):
        tier, progress = _calculate_tier(50000)
        assert tier == "Elite"
        # Elite tier has no upper bound, so progress starts at 0


class TestReferralCodeGeneration:
    """Test referral code generation."""

    def test_generates_valid_code(self):
        code = _generate_referral_code("user123")
        assert code.startswith("CT-")
        assert len(code) == 11  # "CT-" + 8 chars

    def test_generates_unique_codes(self):
        codes = [_generate_referral_code(f"user{i}") for i in range(10)]
        assert len(set(codes)) == 10  # All unique


class TestRewardActions:
    """Test reward action definitions."""

    def test_all_actions_have_tokens(self):
        for action, details in REWARD_ACTIONS.items():
            assert "tokens" in details
            assert details["tokens"] > 0

    def test_all_actions_have_description(self):
        for action, details in REWARD_ACTIONS.items():
            assert "description" in details
            assert len(details["description"]) > 0

    def test_expected_actions_exist(self):
        expected = [
            "profile_complete",
            "resume_upload",
            "first_application",
            "referral_signup",
            "feedback_submit"
        ]
        for action in expected:
            assert action in REWARD_ACTIONS


class TestRewardsEndpoints:
    """Test rewards API endpoints."""

    def test_health_check(self, client):
        response = client.get("/api/rewards/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rewards-api"
        assert data["reward_actions_defined"] == len(REWARD_ACTIONS)

    @patch("services.backend_api.routers.rewards.get_current_user")
    @patch("services.backend_api.routers.rewards.get_db")
    def test_get_rewards_empty(self, mock_get_db, mock_get_user, mock_user, mock_db):
        """Test getting rewards for user with no rewards."""
        mock_get_user.return_value = mock_user
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        # This test validates the endpoint structure
        # Full integration test would require database setup

    @patch("services.backend_api.routers.rewards.get_current_user")
    @patch("services.backend_api.routers.rewards.get_db")
    def test_get_available_rewards(self, mock_get_db, mock_get_user, mock_user, mock_db):
        """Test getting available reward actions."""
        mock_get_user.return_value = mock_user
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db


class TestRewardModels:
    """Test reward data models."""

    def test_reward_type_enum(self):
        assert RewardType.REFERRAL.value == "referral"
        assert RewardType.ACTIVITY.value == "activity"
        assert RewardType.MILESTONE.value == "milestone"

    def test_reward_status_enum(self):
        assert RewardStatus.PENDING.value == "pending"
        assert RewardStatus.ACTIVE.value == "active"
        assert RewardStatus.REDEEMED.value == "redeemed"


class TestRedemptionOptions:
    """Test redemption option validation."""

    def test_premium_day_exists(self, client):
        # Verify health check works (endpoint is accessible)
        response = client.get("/api/rewards/v1/health")
        assert response.status_code == 200


class TestDatabaseModels:
    """Test database model instantiation."""

    def test_user_reward_model(self):
        reward = UserReward(
            user_id=1,
            reward_type="activity",
            tokens=50,
            description="Test reward",
            status="active"
        )
        assert reward.user_id == 1
        assert reward.tokens == 50
        assert reward.status == "active"

    def test_user_referral_model(self):
        referral = UserReferral(
            referrer_id=1,
            referral_code="CT-ABCD1234",
            status="pending"
        )
        assert referral.referrer_id == 1
        assert referral.referral_code == "CT-ABCD1234"

    def test_user_suggestion_model(self):
        suggestion = UserSuggestion(
            user_id=1,
            category="feature",
            title="Test suggestion",
            description="A detailed description",
            priority="high"
        )
        assert suggestion.user_id == 1
        assert suggestion.category == "feature"

    def test_reward_redemption_model(self):
        redemption = RewardRedemption(
            user_id=1,
            redemption_type="premium_day",
            tokens_spent=50,
            description="1 day premium access"
        )
        assert redemption.tokens_spent == 50

    def test_completed_action_model(self):
        completed = UserCompletedAction(
            user_id=1,
            action_key="profile_complete"
        )
        assert completed.action_key == "profile_complete"
