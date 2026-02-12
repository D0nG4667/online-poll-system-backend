import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.polls.models import Poll

User = get_user_model()


class PaginationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="password"
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

    def test_graphql_pagination(self):
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
            "/graphql/", data={"query": query}, content_type="application/json"
        )
        data = response.json()

        self.assertIn("data", data)
        self.assertIn("polls", data["data"])
        polls_data = data["data"]["polls"]

        self.assertIn("edges", polls_data)
        self.assertIn("pageInfo", polls_data)
        self.assertEqual(len(polls_data["edges"]), 5)
        self.assertTrue(polls_data["pageInfo"]["hasNextPage"])

    def test_rest_pagination(self):
        response = self.client.get("/api/v1/polls/")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("count", data)
        self.assertIn("next", data)
        self.assertIn("previous", data)
        self.assertIn("results", data)

        self.assertEqual(data["count"], 25)
        self.assertEqual(len(data["results"]), 20)
        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

        # Test second page
        response = self.client.get(data["next"])
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data["results"]), 5)
        self.assertIsNone(data["next"])
        self.assertIsNotNone(data["previous"])

    def test_rest_page_size(self):
        # Test custom page size
        response = self.client.get("/api/v1/polls/?page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data["results"]), 10)
        self.assertEqual(data["count"], 25)
        self.assertIsNotNone(data["next"])
