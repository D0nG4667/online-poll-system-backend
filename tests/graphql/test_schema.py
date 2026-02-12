from typing import Any

import pytest


@pytest.mark.django_db
class TestGraphQLQueries:
    """
    Tests for GraphQL queries (Polls and AI history).
    """

    def test_query_polls_list(self, graphql_client: Any, poll: Any) -> None:
        """
        Test querying the list of polls.
        """
        query = """
            query TestPolls {
                polls {
                    edges {
                        node {
                            id
                            title
                            description
                            isActive
                        }
                    }
                }
            }
        """
        response = graphql_client(query)
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        assert len(data["data"]["polls"]["edges"]) >= 1
        assert data["data"]["polls"]["edges"][0]["node"]["title"] == poll.title

    def test_query_single_poll(self, graphql_client: Any, poll_with_data: Any) -> None:
        """
        Test querying a single poll with its questions and options.
        """
        query = """
            query TestPoll($pk: ID!) {
                poll(pk: $pk) {
                    id
                    title
                    questions {
                        id
                        text
                        options {
                            id
                            text
                            voteCount
                        }
                        totalVotes
                    }
                }
            }
        """
        variables = {"pk": str(poll_with_data.id)}
        response = graphql_client(query, variables)
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        poll_res = data["data"]["poll"]
        assert poll_res["title"] == poll_with_data.title
        assert len(poll_res["questions"]) >= 1
        assert len(poll_res["questions"][0]["options"]) >= 1

    def test_query_polls_filter(self, graphql_client: Any, test_user: Any) -> None:
        """
        Test filtering polls using GraphQL.
        """
        from apps.polls.models import Poll

        Poll.objects.create(title="Active Poll", created_by=test_user, is_active=True)
        Poll.objects.create(
            title="Inactive Poll", created_by=test_user, is_active=False
        )

        query = """
            query TestFilter($active: Boolean) {
                polls(filters: { isActive: { exact: $active } }) {
                    edges {
                        node {
                            title
                            isActive
                        }
                    }
                }
            }
        """
        # Test True
        response = graphql_client(query, {"active": True})
        data = response.json()
        titles = [p["node"]["title"] for p in data["data"]["polls"]["edges"]]
        assert "Active Poll" in titles
        assert "Inactive Poll" not in titles

    def test_poll_insight_history(
        self, graphql_auth_client: Any, poll: Any, test_user: Any
    ) -> None:
        """
        Test querying AI insight history for a poll.
        """
        from apps.ai.models import AnalysisRequest

        AnalysisRequest.objects.create(
            user=test_user,
            poll=poll,
            query="Test query",
            response="Test response",
            provider_used="openai",
        )

        query = """
            query TestHistory($pollId: Int!) {
                pollInsightHistory(pollId: $pollId) {
                    id
                    query
                    response
                    providerUsed
                }
            }
        """
        response = graphql_auth_client(query, {"pollId": poll.id})
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        history = data["data"]["pollInsightHistory"]
        assert len(history) == 1
        assert history[0]["query"] == "Test query"


@pytest.mark.django_db
class TestGraphQLMutations:
    """
    Tests for GraphQL mutations (AI features).
    """

    def test_generate_poll_from_prompt(
        self, graphql_auth_client: Any, mock_openai_poll_generation: Any
    ) -> None:
        """
        Test AI poll generation via GraphQL mutation.
        """
        query = """
            mutation TestGeneratePoll($prompt: String!) {
                generatePollFromPrompt(prompt: $prompt) {
                    title
                    description
                    questions
                    provider
                }
            }
        """
        variables = {"prompt": "Create a employee satisfaction survey"}
        response = graphql_auth_client(query, variables)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        gen_poll = data["data"]["generatePollFromPrompt"]
        assert gen_poll["title"] == mock_openai_poll_generation["title"]
        assert gen_poll["provider"] == "openai"

    def test_generate_poll_insight(
        self,
        graphql_auth_client: Any,
        poll_with_data: Any,
        mock_openai_insight_generation: Any,
    ) -> None:
        """
        Test AI insight generation via GraphQL mutation.
        """
        query = """
            mutation TestGenerateInsight($pollId: Int!, $query: String!) {
                generatePollInsight(pollId: $pollId, query: $query) {
                    query
                    insight
                    provider
                }
            }
        """
        variables = {"pollId": poll_with_data.id, "query": "Summary of consensus"}
        response = graphql_auth_client(query, variables)

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        insight = data["data"]["generatePollInsight"]
        assert insight["insight"] == mock_openai_insight_generation
        assert insight["provider"] == "openai"

    def test_ingest_poll_data(
        self, graphql_auth_client: Any, poll_with_data: Any, mocker: Any
    ) -> None:
        """
        Test RAG ingestion via GraphQL mutation.
        """
        # Mock vector store as in AI REST tests
        mock_vs = mocker.Mock()
        mock_vs.add_documents.return_value = None
        mocker.patch(
            "apps.ai.services.RAGService.get_vector_store", return_value=mock_vs
        )

        query = """
            mutation TestIngest($pollId: Int!) {
                ingestPollData(pollId: $pollId)
            }
        """
        response = graphql_auth_client(query, {"pollId": poll_with_data.id})

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        assert "Successfully ingested" in data["data"]["ingestPollData"]
        mock_vs.add_documents.assert_called_once()

    def test_mutation_requires_auth(
        self, graphql_client: Any, poll_with_data: Any
    ) -> None:
        """
        Test that mutations fail without authentication.
        """
        query = """
            mutation TestIngest($pollId: Int!) {
                ingestPollData(pollId: $pollId)
            }
        """
        response = graphql_client(query, {"pollId": poll_with_data.id})
        data = response.json()
        assert "errors" in data
        assert "Authentication required" in data["errors"][0]["message"]
