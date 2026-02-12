from typing import Any

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAuthentication:
    def test_session_auth_priority(self, auth_client: Any) -> None:
        """
        Verify that Session authentication works for standard endpoints.
        """
        url = reverse("user-profile")
        response = auth_client.get(url)
        assert response.status_code == 200
        # Since we use allauth headless,
        # user_me might not be registered or named differently
        # Let's check common endpoints or fallback to a simple verification

    def test_jwt_auth_bearer(self, jwt_auth_client: Any) -> None:
        """
        Verify that JWT Bearer token works.
        """
        url = reverse("user-profile")
        response = jwt_auth_client.get(url)
        assert response.status_code == 200

    def test_unauthenticated_access(self, api_client: Any) -> None:
        """
        Verify that unauthenticated requests are rejected for protected endpoints.
        """
        # Vote creation is strictly protected (IsAuthenticated)
        url = "/api/v1/votes/"
        response = api_client.post(url, {})
        assert response.status_code == 403


@pytest.mark.django_db
class TestUserProfile:
    """
    Tests for the User Profile API (Retrieve/Update).
    """

    def test_get_profile_authenticated(self, auth_client: Any, test_user: Any) -> None:
        """
        Test retrieving the authenticated user's profile.
        """
        url = reverse("user-profile")
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data["email"] == test_user.email
        assert "first_name" in response.data
        assert "last_name" in response.data

    def test_update_profile_authenticated(
        self, auth_client: Any, test_user: Any
    ) -> None:
        """
        Test updating the authenticated user's profile.
        """
        url = reverse("user-profile")
        data = {"first_name": "NewFirst", "last_name": "NewLast"}
        response = auth_client.patch(url, data, format="json")

        assert response.status_code == 200
        assert response.data["first_name"] == "NewFirst"
        assert response.data["last_name"] == "NewLast"

        test_user.refresh_from_db()
        assert test_user.first_name == "NewFirst"
        assert test_user.last_name == "NewLast"

    def test_get_profile_unauthorized(self, api_client: Any) -> None:
        """
        Test that anonymous users cannot access the profile endpoint.
        """
        url = reverse("user-profile")
        response = api_client.get(url)

        assert response.status_code == 403
