import json  # noqa: I001
import pytest
from typing import Any
from django.urls import reverse

from apps.polls.models import Vote


@pytest.mark.django_db
class TestPollWorkflows:
    """
    Integration tests for complete user workflows.
    """

    def test_complete_poll_lifecycle(self, auth_client: Any, other_user_auth_client: Any) -> None:
        """
        Scenario: User creates a poll, adds questions/options, activates it,
        and another user votes.
        """
        # 1. Create Poll
        poll_url = reverse("polls:poll-list")
        poll_data = {
            "title": "Integration Test Poll",
            "description": "Testing full flow",
        }
        response = auth_client.post(poll_url, poll_data, format="json")
        assert response.status_code == 201
        assert response.status_code == 201
        poll_slug = response.data["slug"]

        # 2. Add Question
        q_url = reverse("polls:question-list")
        q_data = {
            "poll": poll_slug,
            "text": "Is integration testing fun?",
            "question_type": "single",
        }
        response = auth_client.post(q_url, q_data, format="json")
        assert response.status_code == 201
        q_id = response.data["id"]
        q_slug = response.data["slug"]

        # 3. Add Options
        opt_url = reverse("polls:option-list")
        opt_data_1 = {"question": q_slug, "text": "Yes", "order": 1}
        opt_data_2 = {"question": q_slug, "text": "No", "order": 2}
        auth_client.post(opt_url, opt_data_1, format="json")
        auth_client.post(opt_url, opt_data_2, format="json")

        # 4. Activate Poll
        detail_url = reverse("polls:poll-detail", kwargs={"slug": poll_slug})
        auth_client.patch(detail_url, {"is_active": True}, format="json")

        # Verify active
        response = auth_client.get(detail_url)
        assert response.data["is_active"] is True

        # 5. Vote as another user
        # Need to find the option ID first
        response = auth_client.get(opt_url)

        # Find the target option (Yes)
        target_option = None
        for opt in response.data["results"]:
            if opt["text"] == "Yes" and opt["question"] == q_slug:
                target_option = opt
                break

        assert target_option is not None
        option_id = target_option["id"]
        option_slug = target_option["slug"]

        vote_url = reverse("polls:vote-list")
        vote_data = {"question": q_slug, "option": option_slug}
        response = other_user_auth_client.post(vote_url, vote_data, format="json")
        assert response.status_code == 201

        # 6. Verify Vote in Poll Detail
        assert Vote.objects.filter(question_id=q_id, option_id=option_id).count() == 1

    def test_ai_poll_workflow(
        self,
        auth_client: Any,
        mock_openai_poll_generation: Any,
        mock_openai_insight_generation: Any,
    ) -> None:
        """
        Scenario: User generates a poll with AI, reviews it, publishes it,
        and then generates insights.
        """
        # 1. Generate Poll with AI via REST API
        ai_gen_url = reverse("ai:generate-poll-from-prompt")
        prompt = "Create a survey about remote work"
        response = auth_client.post(ai_gen_url, {"prompt": prompt}, format="json")
        assert response.status_code == 200
        ai_data = response.data

        # 2. Manual step simulated: User creates poll based on AI suggestions
        poll_url = reverse("polls:poll-list")
        poll_data = {"title": ai_data["title"], "description": ai_data["description"]}
        response = auth_client.post(poll_url, poll_data, format="json")
        poll_slug = response.data["slug"]

        # Create questions suggest by AI
        q_url = reverse("polls:question-list")
        opt_url = reverse("polls:option-list")

        for q_suggested in ai_data["questions"]:
            q_res = auth_client.post(
                q_url,
                {
                    "poll": poll_slug,
                    "text": q_suggested["text"],
                    "question_type": q_suggested["type"],
                },
                format="json",
            )
            q_slug = q_res.data["slug"]

            for opt_text in q_suggested["options"]:
                auth_client.post(opt_url, {"question": q_slug, "text": opt_text}, format="json")

        # 3. Generate Insights
        insight_url = reverse("ai:generate-insight")
        response = auth_client.post(
            insight_url,
            {
                "poll_slug": poll_slug,
                "query": "What do people think about remote work?",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["insight"] == mock_openai_insight_generation

    def test_rag_workflow(self, auth_client: Any, poll_with_data: Any, mocker: Any) -> None:
        """
        Scenario: Ingest poll data to vector store, then retrieve history.
        """
        # 1. Ingest
        # Mock vector store
        mock_vs = mocker.Mock()
        mock_vs.add_documents.return_value = None
        mocker.patch("apps.ai.services.RAGService.get_vector_store", return_value=mock_vs)

        ingest_url = reverse("ai:ingest-poll-data")
        response = auth_client.post(ingest_url, {"poll_slug": poll_with_data.slug}, format="json")
        assert response.status_code == 200
        mock_vs.add_documents.assert_called_once()

        # 2. Verify history via GraphQL Query
        graphql_url = "/graphql"
        query = """
            query TestHistory($pollSlug: String!) {
                pollInsightHistory(pollSlug: $pollSlug) {
                    query
                }
            }
        """
        # Ensure some history exists
        from apps.ai.models import AnalysisRequest

        AnalysisRequest.objects.create(
            user=poll_with_data.created_by,
            poll=poll_with_data,
            query="Workflow test",
            response="Fine",
            provider_used="openai",
        )

        payload = {"query": query, "variables": {"pollSlug": poll_with_data.slug}}
        response = auth_client.post(
            graphql_url, json.dumps(payload), content_type="application/json"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["pollInsightHistory"]) >= 1
