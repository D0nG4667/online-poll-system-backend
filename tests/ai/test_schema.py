from typing import Any

import pytest


@pytest.mark.django_db
class TestAISchema:
    def test_ingest_poll_data_mutation(
        self, graphql_auth_client: Any, poll_with_data: Any, mocker: Any
    ) -> None:
        # Mock RAGService
        mock_rag = mocker.patch("apps.ai.schema.RAGService")
        mock_instance = mock_rag.return_value
        mock_instance.ingest_poll_data.return_value = None

        mutation = """
            mutation IngestPollData($pollSlug: String!) {
                ingestPollData(pollSlug: $pollSlug)
            }
        """
        variables = {"pollSlug": poll_with_data.slug}

        response = graphql_auth_client(mutation, variables=variables)
        content = response.json()

        assert "errors" not in content
        expected = f"Successfully ingested poll {poll_with_data.slug} data into vector store"
        assert content["data"]["ingestPollData"] == expected
        mock_instance.ingest_poll_data.assert_called_once_with(poll_with_data.slug)

    def test_generate_poll_insight_mutation(
        self, graphql_auth_client: Any, poll_with_data: Any, mocker: Any
    ) -> None:
        # Mock RAGService
        mock_rag = mocker.patch("apps.ai.schema.RAGService")
        mock_instance = mock_rag.return_value
        mock_instance.generate_insight.return_value = "AI Generated Insight"
        mock_instance.openai_key = "fake-key"

        mutation = """
            mutation GenerateInsight($pollSlug: String!, $query: String!) {
                generatePollInsight(pollSlug: $pollSlug, query: $query) {
                    query
                    insight
                    provider
                }
            }
        """
        variables = {"pollSlug": poll_with_data.slug, "query": "What are the trends?"}

        response = graphql_auth_client(mutation, variables=variables)
        content = response.json()

        assert "errors" not in content
        data = content["data"]["generatePollInsight"]
        assert data["query"] == "What are the trends?"
        assert data["insight"] == "AI Generated Insight"
        assert data["provider"] == "openai"

    def test_generate_poll_from_prompt_mutation(
        self, graphql_auth_client: Any, mocker: Any
    ) -> None:
        # Mock RAGService
        mock_rag = mocker.patch("apps.ai.schema.RAGService")
        mock_instance = mock_rag.return_value
        mock_instance.generate_poll_structure.return_value = {
            "title": "Generated Poll",
            "description": "Description",
            "questions": [{"text": "Q1", "type": "single_choice", "options": ["A", "B"]}],
        }
        mock_instance.openai_key = "fake-key"

        mutation = """
            mutation GeneratePoll($prompt: String!) {
                generatePollFromPrompt(prompt: $prompt) {
                    title
                    description
                    questions
                    provider
                }
            }
        """
        variables = {"prompt": "Create a poll"}

        response = graphql_auth_client(mutation, variables=variables)
        content = response.json()

        assert "errors" not in content
        data = content["data"]["generatePollFromPrompt"]
        assert data["title"] == "Generated Poll"
        assert len(data["questions"]) == 1
        assert data["provider"] == "openai"

    def test_poll_insight_history_query(
        self, graphql_auth_client: Any, poll_with_data: Any, test_user: Any
    ) -> None:
        from apps.ai.models import AnalysisRequest

        AnalysisRequest.objects.create(
            user=test_user,
            poll=poll_with_data,
            query="Query 1",
            response="Response 1",
            provider_used="openai",
        )

        query = """
            query InsightHistory($pollSlug: String!) {
                pollInsightHistory(pollSlug: $pollSlug) {
                    query
                    response
                    providerUsed
                }
            }
        """
        variables = {"pollSlug": poll_with_data.slug}

        response = graphql_auth_client(query, variables=variables)
        content = response.json()

        assert "errors" not in content
        history = content["data"]["pollInsightHistory"]
        assert len(history) == 1
        assert history[0]["query"] == "Query 1"
        assert history[0]["response"] == "Response 1"

    def test_unauthorized_access(self, graphql_client: Any, poll_with_data: Any) -> None:
        mutation = """
            mutation IngestPollData($pollSlug: String!) {
                ingestPollData(pollSlug: $pollSlug)
            }
        """
        variables = {"pollSlug": poll_with_data.slug}
        response = graphql_client(mutation, variables=variables)
        content = response.json()

        assert "errors" in content
        assert content["errors"][0]["message"] == "Authentication required"
