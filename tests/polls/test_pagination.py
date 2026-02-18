from django.contrib.auth import get_user_model  # noqa: I001
from django.test import TestCase
from rest_framework.test import APIClient

from apps.polls.models import Poll

User = get_user_model()


class PaginationTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password",  # noqa: S106
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create 25 polls (default page size is 20)
        for i in range(25):
            Poll.objects.create(
                title=f"Poll {i}",
                description="Test Description",
                created_by=self.user,
                is_active=True,
            )

    def test_graphql_pagination(self) -> None:
        query = """
        query {
            polls(first: 5) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                edges {
                    node {
                        title
                    }
                }
            }
        }
        """
        response = self.client.post(
            "/graphql", data={"query": query}, content_type="application/json"
        )
        data = response.json()

        assert "data" in data
        assert "polls" in data["data"]
        polls_data = data["data"]["polls"]

        assert "edges" in polls_data
        assert "pageInfo" in polls_data
        assert len(polls_data["edges"]) == 5
        assert polls_data["pageInfo"]["hasNextPage"]

    def test_rest_pagination(self) -> None:
        response = self.client.get("/api/v1/polls")
        assert response.status_code == 200
        data = response.json()

        assert "count" in data
        assert "next" in data
        assert "previous" in data
        assert "results" in data

        assert data["count"] == 25
        assert len(data["results"]) == 20
        assert data["next"] is not None
        assert data["previous"] is None

        # Test second page
        response = self.client.get(data["next"])
        assert response.status_code == 200
        data = response.json()

        assert len(data["results"]) == 5
        assert data["next"] is None
        assert data["previous"] is not None

    def test_rest_page_size(self) -> None:
        # Test custom page size
        response = self.client.get("/api/v1/polls?page_size=10")
        assert response.status_code == 200
        data = response.json()

        assert len(data["results"]) == 10
        assert data["count"] == 25
        assert data["next"] is not None
