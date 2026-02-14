from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.analytics.services import AnalyticsService
from apps.polls.models import Option, Poll, PollView, Question, Vote

User = get_user_model()


@pytest.mark.django_db
class TestAnalyticsService:
    @pytest.fixture(autouse=True)
    def mock_cache(self) -> Any:
        with mock.patch("apps.analytics.services.cache") as mock_cache:
            mock_cache.get.return_value = None
            yield mock_cache

    @pytest.fixture
    def user(self) -> Any:
        return User.objects.create_user(
            email="testuser@example.com",
            password="password",  # pragma: allowlist secret  # noqa: S106
        )

    @pytest.fixture
    def setup_data(self, user: Any) -> Poll:
        poll = Poll.objects.create(title="Test Poll", created_by=user)
        q = Question.objects.create(poll=poll, text="Q1", question_type="single")
        opt = Option.objects.create(question=q, text="O1")

        # Create some historical data
        now = timezone.now()
        # Create a poll from 10 days ago
        Poll.objects.create(title="Old Poll", created_by=user, created_at=now - timedelta(days=10))
        # Create a poll from 20 days ago
        Poll.objects.create(
            title="Older Poll", created_by=user, created_at=now - timedelta(days=20)
        )
        # Create a poll from 30 days ago
        Poll.objects.create(
            title="Oldest Poll", created_by=user, created_at=now - timedelta(days=30)
        )

        # Current period (today)
        Vote.objects.create(user=user, question=q, option=opt)
        PollView.objects.create(poll=poll)  # Removed ip_address

        return poll

    def test_get_period_delta(self) -> None:
        assert AnalyticsService.get_period_delta("7d") == timedelta(days=7)
        assert AnalyticsService.get_period_delta("unknown") == timedelta(days=30)

    def test_get_stats_empty(self, user: Any, mock_cache: Any) -> None:
        """Test stats when no data exists."""
        stats = AnalyticsService.get_stats(user)
        assert stats["total_polls"] == 0
        assert stats["total_responses"] == 0
        assert stats["avg_response_rate"] == 0.0

    def test_get_stats_with_data(self, user: Any, setup_data: Any, mock_cache: Any) -> None:
        """Test stats with data."""
        # Ensure cache is clear or mocked to return None (handled by fixture)

        stats = AnalyticsService.get_stats(user, period="30d")
        assert stats["total_polls"] == 1
        assert stats["total_responses"] == 1
        assert stats["total_views"] == 1
        assert stats["avg_response_rate"] == 100.0

        # Verify caching was called
        mock_cache.set.assert_called()

        # Test cache hit
        mock_cache.get.return_value = stats
        cached_stats = AnalyticsService.get_stats(user, period="30d")
        assert cached_stats == stats

    def test_get_trends(self, user: Any, setup_data: Any, mock_cache: Any) -> None:
        """Test trend data generation."""
        trends = AnalyticsService.get_trends(user, period="7d")
        assert "poll_creation" in trends
        assert "response_rate" in trends
        assert len(trends["poll_creation"]) >= 1

        # Verify result structure
        first_poll_trend = trends["poll_creation"][0]
        assert "date" in first_poll_trend
        assert "value" in first_poll_trend
