from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.distribution.models import DistributionAnalytics, DistributionEvent
from apps.polls.models import Poll

User = get_user_model()


@pytest.mark.django_db
class TestDistributionViews:
    @pytest.fixture
    def user(self) -> Any:
        return User.objects.create_user(
            email="testuser@example.com",
            password="password",  # pragma: allowlist secret  # noqa: S106
        )

    @pytest.fixture
    def poll(self, user: Any) -> Poll:
        return Poll.objects.create(
            title="Test Poll", created_by=user, slug="testpoll", is_active=True
        )

    @pytest.fixture
    def api_client(self) -> Any:
        from rest_framework.test import APIClient

        return APIClient()

    def test_public_poll_page_view(self, poll: Poll, api_client: Any) -> None:
        url = reverse("distribution:public-poll-page", kwargs={"slug": poll.slug})
        response = api_client.get(url)
        assert response.status_code == 200
        # Check that the event was actually logged to the DB (integration test style)
        assert DistributionAnalytics.objects.filter(
            poll=poll, event_type=DistributionEvent.LINK_OPEN
        ).exists()

    @patch("apps.distribution.views.log_distribution_event_task")
    def test_public_poll_detail_view(
        self, mock_task: MagicMock, poll: Poll, api_client: Any
    ) -> None:
        url = reverse("distribution:public-poll", kwargs={"slug": poll.slug})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["title"] == poll.title
        mock_task.delay.assert_called_once_with(
            poll.id,
            DistributionEvent.LINK_OPEN,
            ip_address=ANY,
            user_agent=ANY,
            referrer=ANY,
        )

    @patch("apps.distribution.views.DistributionService.generate_qr_code")
    @patch("apps.distribution.views.log_distribution_event_task")
    def test_poll_qr_code_view(
        self,
        mock_task: MagicMock,
        mock_generate: MagicMock,
        poll: Poll,
        api_client: Any,
    ) -> None:
        mock_generate.return_value = b"fake_qr_png"
        url = reverse("distribution:poll-qr", kwargs={"slug": poll.slug})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.content == b"fake_qr_png"
        assert response["Content-Type"] == "image/png"
        mock_task.delay.assert_called_once_with(
            poll.id,
            DistributionEvent.QR_SCAN,
            ip_address=ANY,
            user_agent=ANY,
            referrer=ANY,
        )

    @patch("apps.distribution.views.log_distribution_event_task")
    def test_poll_embed_view(self, mock_task: MagicMock, poll: Poll, api_client: Any) -> None:
        url = reverse("distribution:poll-embed", kwargs={"slug": poll.slug})
        response = api_client.get(url)
        assert response.status_code == 200
        assert "embed_code" in response.data
        assert "public_url" in response.data
        mock_task.delay.assert_called_once_with(
            poll.id,
            DistributionEvent.EMBED_LOAD,
            ip_address=ANY,
            user_agent=ANY,
            referrer=ANY,
        )

    def test_poll_distribution_analytics_view_owner(
        self, poll: Poll, api_client: Any, user: Any
    ) -> None:
        # Create some analytics data
        DistributionAnalytics.objects.create(
            poll=poll, event_type=DistributionEvent.LINK_OPEN, ip_address="127.0.0.1"
        )

        api_client.force_authenticate(user=user)
        url = reverse("distribution:poll-analytics", kwargs={"slug": poll.slug})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["summary"]["total_link_opens"] == 1
        assert response.data["summary"]["total_qr_scans"] == 0

    def test_poll_distribution_analytics_view_unauthorized(
        self, poll: Poll, api_client: Any
    ) -> None:
        # No auth
        url = reverse("distribution:poll-analytics", kwargs={"slug": poll.slug})
        response = api_client.get(url)
        assert response.status_code == 403

    def test_poll_distribution_analytics_view_forbidden(self, poll: Poll, api_client: Any) -> None:
        # Wrong user
        other_user = User.objects.create_user(
            email="other@example.com",
            password="password",  # noqa: S106 # pragma: allowlist secret
        )
        api_client.force_authenticate(user=other_user)
        url = reverse("distribution:poll-analytics", kwargs={"slug": poll.slug})
        response = api_client.get(url)
        assert response.status_code == 404  # get_object_or_404 filters by created_by
