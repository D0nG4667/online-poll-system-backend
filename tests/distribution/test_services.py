from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from apps.distribution.services import DistributionService
from apps.polls.models import Poll

User = get_user_model()


@pytest.mark.django_db
class TestDistributionService:
    @pytest.fixture
    def user(self) -> Any:
        return User.objects.create_user(
            email="testuser@example.com",
            password="password",  # pragma: allowlist secret  # noqa: S106
        )

    @pytest.fixture
    def poll(self, user: Any) -> Poll:
        return Poll.objects.create(title="Test Poll", created_by=user)

    def test_get_public_url(self, poll: Poll, settings: Any) -> None:
        settings.BASE_URL = "http://testserver"
        url = DistributionService.get_public_url(poll)
        assert url == f"http://testserver/polls/{poll.slug}/"

    @patch("apps.distribution.services.qrcode.make")
    @patch("apps.distribution.services.io.BytesIO")
    @patch("apps.distribution.services.cache")
    def test_generate_qr_code_png(
        self,
        mock_cache: MagicMock,
        mock_bytes_io: MagicMock,
        mock_make: MagicMock,
        poll: Poll,
    ) -> None:
        # Setup mocks
        mock_img = MagicMock()
        mock_make.return_value = mock_img

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"fake_png_content"
        mock_bytes_io.return_value = mock_buffer

        # Cache miss
        mock_cache.get.return_value = None

        # Execute
        content = DistributionService.generate_qr_code(poll, img_format="png")

        # Verify
        assert content == b"fake_png_content"
        mock_make.assert_called_once()
        mock_img.save.assert_called_once()
        mock_cache.set.assert_called_once()

    @patch("apps.distribution.services.qrcode.make")
    @patch("apps.distribution.services.io.BytesIO")
    @patch("apps.distribution.services.cache")
    def test_generate_qr_code_svg(
        self,
        mock_cache: MagicMock,
        mock_bytes_io: MagicMock,
        mock_make: MagicMock,
        poll: Poll,
    ) -> None:
        # Setup mocks
        mock_img = MagicMock()
        mock_make.return_value = mock_img

        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b"fake_svg_content"
        mock_bytes_io.return_value = mock_buffer

        # Cache miss
        mock_cache.get.return_value = None

        # Execute
        content = DistributionService.generate_qr_code(poll, img_format="svg")

        # Verify
        assert content == "fake_svg_content"  # decode() is called in service
        mock_make.assert_called_once()
        mock_img.save.assert_called_once()
        mock_cache.set.assert_called_once()

    @patch("apps.distribution.services.cache")
    def test_generate_qr_code_cached(self, mock_cache: MagicMock, poll: Poll) -> None:
        # Cache hit
        mock_cache.get.return_value = b"cached_content"

        content = DistributionService.generate_qr_code(poll, img_format="png")
        assert content == b"cached_content"

    def test_get_embed_code(self, poll: Poll, settings: Any) -> None:
        settings.BASE_URL = "http://testserver"
        embed_code = DistributionService.get_embed_code(poll)
        expected_url = f"http://testserver/polls/{poll.slug}/"
        assert f'src="{expected_url}"' in embed_code
        assert "<iframe" in embed_code
