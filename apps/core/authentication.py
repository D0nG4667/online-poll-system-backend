"""
Custom authentication classes for supporting multiple auth methods.
"""

from allauth.headless.tokens.strategies.base import AbstractTokenStrategy
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication


class MultiAuthenticationBackend(BaseAuthentication):
    """
    Supports both Session and JWT authentication.
    Tries Session first, falls back to JWT.
    """

    def authenticate(self, request):
        from allauth.headless.contrib.rest_framework.authentication import (
            XSessionTokenAuthentication,
        )
        from rest_framework.authentication import SessionAuthentication

        # Try session authentication first
        session_auth = SessionAuthentication()
        try:
            result = session_auth.authenticate(request)
            if result:
                return result
        except exceptions.AuthenticationFailed:
            pass

        # Try X-Session-Token (allauth headless)
        xsession_auth = XSessionTokenAuthentication()
        try:
            result = xsession_auth.authenticate(request)
            if result:
                return result
        except exceptions.AuthenticationFailed:
            pass

        # Try JWT token in Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            from allauth.headless.tokens import get_token_strategy

            strategy = get_token_strategy()
            if isinstance(strategy, AbstractTokenStrategy):
                try:
                    user = strategy.lookup_user_from_access_token(token)
                    if user:
                        return (user, None)
                except Exception:
                    pass

        return None
