import secrets

from locust import HttpUser, between, task


class PollSystemUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self) -> None:
        """
        Setup: Login or obtain token if necessary.
        For simplicity in this basic load test, we'll hit public endpoints.
        """
        pass

    @task(3)
    def view_polls(self) -> None:
        """
        Simulate users browsing the poll list.
        """
        self.client.get("/api/v1/polls/")

    @task(2)
    def view_poll_detail(self) -> None:
        """
        Simulate users looking at a specific poll.
        """
        # We assume poll IDs 1-5 exist for the load test simulation
        poll_id = secrets.choice(range(1, 6))
        self.client.get(f"/api/v1/polls/{poll_id}/")

    @task(1)
    def query_graphql(self) -> None:
        """
        Simulate GraphQL query traffic.
        """
        query = """
        query {
          polls {
            id
            title
            questions {
              id
              text
            }
          }
        }
        """
        self.client.post("/graphql/", json={"query": query})

    @task(1)
    def view_user_me(self) -> None:
        """
        Simulate hitting the authenticated 'me' endpoint.
        Requires valid authentication headers in a real scenario.
        """
        # Note: In a real test, you would provide the Authorization header
        # obtained during on_start.
        self.client.get("/api/v1/users/me/")
