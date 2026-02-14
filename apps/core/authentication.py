"""
Custom authentication classes for supporting multiple auth methods.
"""

import logging
from typing import TYPE_CHECKING, Any

import sentry_sdk
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

if TYPE_CHECKING:
    from rest_framework.request import Request

logger = logging.getLogger(__name__)


class MultiAuthenticationBackend(BaseAuthentication):
    """
    Supports both Session and JWT authentication.
    Tries Session first, falls back to JWT.
    """

    def authenticate(self, request: "Request") -> Any:
        sentry_sdk.add_breadcrumb(category="auth", message="Authentication attempt", level="info")
        from allauth.headless.contrib.rest_framework.authentication import (
            XSessionTokenAuthentication,
        )
        from rest_framework.authentication import SessionAuthentication

        # Try session authentication first
        session_auth = SessionAuthentication()
        try:
            result = session_auth.authenticate(request)
            if result:
                sentry_sdk.add_breadcrumb(
                    category="auth", message="Session auth successful", level="info"
                )
                return result
        except exceptions.AuthenticationFailed:
            logger.debug("Session authentication failed.")
            pass

        # Try X-Session-Token (allauth headless)
        xsession_auth = XSessionTokenAuthentication()
        try:
            result = xsession_auth.authenticate(request)
            if result:
                sentry_sdk.add_breadcrumb(
                    category="auth",
                    message="X-Session-Token auth successful",
                    level="info",
                )
                return result
        except exceptions.AuthenticationFailed:
            logger.debug("X-Session-Token authentication failed.")
            pass

        # Try JWT token in Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                import jwt
                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import serialization
                from django.conf import settings
                from django.contrib.auth import get_user_model

                user_model = get_user_model()

                # Load the private key and extract the public key for verification
                private_key_bytes = settings.HEADLESS_JWT_PRIVATE_KEY.encode()
                private_key = serialization.load_pem_private_key(
                    private_key_bytes, password=None, backend=default_backend()
                )
                public_key = private_key.public_key()
                public_key_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )

                # Decode JWT token using the public key
                payload = jwt.decode(token, public_key_pem, algorithms=["RS256"])

                # Extract user ID from payload
                user_id = payload.get("user_id") or payload.get("sub")
                if user_id:
                    user = user_model.objects.get(pk=user_id)
                    sentry_sdk.add_breadcrumb(
                        category="auth", message="JWT auth successful", level="info"
                    )
                    return (user, None)
            except (
                jwt.DecodeError,
                jwt.ExpiredSignatureError,
                user_model.DoesNotExist,
            ) as e:
                logger.warning("JWT token lookup failed: %s", e)
                pass
            except Exception as e:
                logger.warning("JWT token lookup failed: %s", e)
                pass

        return None
