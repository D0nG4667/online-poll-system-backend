from typing import Any
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

from apps.core.authentication import MultiAuthenticationBackend

User = get_user_model()


class TestMultiAuthenticationBackend:
    @pytest.fixture
    def backend(self) -> MultiAuthenticationBackend:
        return MultiAuthenticationBackend()

    @pytest.fixture
    def rf(self) -> Any:
        from rest_framework.test import APIRequestFactory

        return APIRequestFactory()

    def test_session_auth_success(self, backend: MultiAuthenticationBackend, rf: Any) -> None:
        """Test successful session authentication."""
        request = rf.get("/")
        user = User(email="test@example.com")

        with patch("rest_framework.authentication.SessionAuthentication.authenticate") as mock_auth:
            mock_auth.return_value = (user, None)
            result = backend.authenticate(request)
            assert result == (user, None)

    def test_session_auth_failure_logs_debug(
        self, backend: MultiAuthenticationBackend, rf: Any
    ) -> None:
        """Test that session auth failure logs debug message and continues."""
        request = rf.get("/")
        with (
            patch(
                "rest_framework.authentication.SessionAuthentication.authenticate",
                side_effect=AuthenticationFailed(),
            ),
            patch(
                "allauth.headless.contrib.rest_framework.authentication.XSessionTokenAuthentication.authenticate",
                return_value=None,
            ),
            patch("apps.core.authentication.logger") as mock_logger,
        ):
            result = backend.authenticate(request)
            assert result is None
            mock_logger.debug.assert_any_call("Session authentication failed.")

    def test_x_session_auth_success(self, backend: MultiAuthenticationBackend, rf: Any) -> None:
        """Test successful X-Session-Token authentication."""
        request = rf.get("/")
        user = User(email="xsession@example.com")

        with (
            patch(
                "rest_framework.authentication.SessionAuthentication.authenticate",
                return_value=None,
            ),
            patch(
                "allauth.headless.contrib.rest_framework.authentication.XSessionTokenAuthentication.authenticate",
                return_value=(user, None),
            ),
        ):
            result = backend.authenticate(request)
            assert result == (user, None)

    def test_x_session_auth_failure_logs_debug(
        self, backend: MultiAuthenticationBackend, rf: Any
    ) -> None:
        """Test that X-Session auth failure logs debug message and continues."""
        request = rf.get("/")
        with (
            patch(
                "rest_framework.authentication.SessionAuthentication.authenticate",
                return_value=None,
            ),
            patch(
                "allauth.headless.contrib.rest_framework.authentication.XSessionTokenAuthentication.authenticate",
                side_effect=AuthenticationFailed(),
            ),
            patch("apps.core.authentication.logger") as mock_logger,
        ):
            result = backend.authenticate(request)
            assert result is None
            mock_logger.debug.assert_any_call("X-Session-Token authentication failed.")

    def test_jwt_auth_success(self, backend: MultiAuthenticationBackend) -> None:
        """Test successful JWT authentication."""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid_token"}
        user = User(email="jwt@example.com", id="123e4567-e89b-12d3-a456-426614174000")

        with (
            patch(
                "rest_framework.authentication.SessionAuthentication.authenticate",
                return_value=None,
            ),
            patch(
                "allauth.headless.contrib.rest_framework.authentication.XSessionTokenAuthentication.authenticate",
                return_value=None,
            ),
            patch("jwt.decode", return_value={"user_id": 1}),
            patch("django.contrib.auth.get_user_model") as mock_get_user_model,
            patch(
                "cryptography.hazmat.primitives.serialization.load_pem_private_key"
            ) as mock_load_key,
        ):
            # Ensure DoesNotExist is a valid exception class on the mock
            mock_get_user_model.return_value.DoesNotExist = User.DoesNotExist

            mock_objects = MagicMock()
            mock_objects.get.return_value = user
            mock_get_user_model.return_value.objects = mock_objects

            mock_key = MagicMock()
            mock_key.public_key.return_value.public_bytes.return_value = b"public_key"
            mock_load_key.return_value = mock_key

            result = backend.authenticate(mock_request)
            assert result == (user, None)

    def test_jwt_auth_failure_decode_error(self, backend: MultiAuthenticationBackend) -> None:
        """Test JWT decode error (hits exception block 1)."""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer invalid_token"}

        with (
            patch(
                "rest_framework.authentication.SessionAuthentication.authenticate",
                return_value=None,
            ),
            patch(
                "allauth.headless.contrib.rest_framework.authentication.XSessionTokenAuthentication.authenticate",
                return_value=None,
            ),
            patch("cryptography.hazmat.primitives.serialization.load_pem_private_key"),
            patch("django.contrib.auth.get_user_model") as mock_get_user_model,
            patch("apps.core.authentication.logger") as mock_logger,
        ):
            # Ensure DoesNotExist is a valid exception class on the mock
            mock_get_user_model.return_value.DoesNotExist = User.DoesNotExist

            with patch("jwt.decode", side_effect=jwt.DecodeError("Fail")):
                result = backend.authenticate(mock_request)
                assert result is None
                mock_logger.warning.assert_called()

    def test_jwt_auth_failure_user_not_found(self, backend: MultiAuthenticationBackend) -> None:
        """Test User.DoesNotExist error (hits exception block 1)."""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid_token"}

        with (
            patch(
                "rest_framework.authentication.SessionAuthentication.authenticate",
                return_value=None,
            ),
            patch(
                "allauth.headless.contrib.rest_framework.authentication.XSessionTokenAuthentication.authenticate",
                return_value=None,
            ),
            patch("cryptography.hazmat.primitives.serialization.load_pem_private_key"),
            patch("jwt.decode", return_value={"user_id": 1}),
            patch("django.contrib.auth.get_user_model") as mock_get_user_model,
        ):
            # Ensure DoesNotExist is a valid exception class on the mock
            mock_get_user_model.return_value.DoesNotExist = User.DoesNotExist
            mock_get_user_model.return_value.objects.get.side_effect = User.DoesNotExist

            result = backend.authenticate(mock_request)
            assert result is None

    def test_jwt_auth_failure_generic_exception(self, backend: MultiAuthenticationBackend) -> None:
        """Test generic exception during JWT auth (hits exception block 2)."""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer token"}

        with (
            patch(
                "rest_framework.authentication.SessionAuthentication.authenticate",
                return_value=None,
            ),
            patch(
                "allauth.headless.contrib.rest_framework.authentication.XSessionTokenAuthentication.authenticate",
                return_value=None,
            ),
            patch("django.contrib.auth.get_user_model") as mock_get_user_model,
            patch(
                "cryptography.hazmat.primitives.serialization.load_pem_private_key",
                side_effect=Exception("Unexpected Error"),
            ),
            patch("apps.core.authentication.logger") as mock_logger,
        ):
            # Ensure DoesNotExist is a valid exception class on the mock
            mock_get_user_model.return_value.DoesNotExist = User.DoesNotExist

            result = backend.authenticate(mock_request)
            assert result is None
            mock_logger.warning.call_args[0][0].startswith("JWT token lookup failed")
