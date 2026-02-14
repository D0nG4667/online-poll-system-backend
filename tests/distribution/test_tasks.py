from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.distribution.models import DistributionAnalytics, DistributionEvent
from apps.distribution.tasks import log_distribution_event_task
from apps.polls.models import Poll

User = get_user_model()


@pytest.mark.django_db
class TestDistributionTasks:
    @pytest.fixture
    def user(self) -> Any:
        return User.objects.create_user(
            email="test@example.com",
            password="password",  # pragma: allowlist secret  # noqa: S106
        )

    @pytest.fixture
    def poll(self, user: Any) -> Poll:
        return Poll.objects.create(
            title="Test Poll", created_by=user, slug="testpoll", is_active=True
        )

    def test_log_distribution_event_task_success(self, poll: Poll) -> None:
        log_distribution_event_task(
            poll_id=poll.id,
            event_type=DistributionEvent.LINK_OPEN,
            ip_address="127.0.0.1",
            user_agent="TestAgent",
            referrer="http://example.com",
            metadata={"extra": "data"},
        )

        assert DistributionAnalytics.objects.count() == 1
        analytics = DistributionAnalytics.objects.first()
        assert analytics is not None
        assert analytics.poll == poll
        assert analytics.event_type == DistributionEvent.LINK_OPEN
        assert analytics.ip_address == "127.0.0.1"
        assert analytics.user_agent == "TestAgent"
        assert analytics.referrer == "http://example.com"
        assert analytics.metadata == {"extra": "data"}

    def test_log_distribution_event_task_poll_not_found(self) -> None:
        # Should not raise exception
        log_distribution_event_task(poll_id=99999, event_type=DistributionEvent.LINK_OPEN)
        assert DistributionAnalytics.objects.count() == 0
