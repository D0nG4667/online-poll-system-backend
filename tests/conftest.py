# mypy: ignore-errors
import json
from collections.abc import Callable
from typing import Any

import pytest
from allauth.headless.tokens.strategies.jwt.internal import create_access_token
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    """
    Standard DRF APIClient.
    """
    return APIClient()


@pytest.fixture
def user_factory(db: Any) -> Callable[..., Any]:
    """
    Factory to create users for testing.
    """

    def create_user(
        email: str = "test@example.com",
        password: str | None = None,
        **kwargs: Any,
    ) -> Any:
        if password is None:
            password = "password123"  # noqa: S106
        return User.objects.create_user(email=email, password=password, **kwargs)

    return create_user


@pytest.fixture
def test_user(user_factory: Callable[..., Any]) -> Any:
    """
    A default test user.
    """
    return user_factory()


@pytest.fixture
def auth_client(api_client: APIClient, test_user: Any) -> APIClient:
    """
    An APIClient authenticated with session/force_authenticate.
    """
    api_client.force_login(user=test_user)
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def jwt_auth_client(api_client: APIClient, test_user: Any) -> APIClient:
    """
    An APIClient pre-configured with a JWT Bearer token.
    """
    from django.contrib.sessions.backends.db import SessionStore

    session = SessionStore()
    session.create()

    # Generate a valid RSA private key for testing
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Patch the setting just for this test client
    from django.conf import settings

    settings.JWT_PRIVATE_KEY = pem.decode("utf-8")

    # create_access_token returns just the token string
    access_token = create_access_token(user=test_user, session=session, claims={})
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def graphql_client(api_client: APIClient) -> Callable[..., Any]:
    """
    Client for GraphQL testing.
    """

    def _query(query: str, variables: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return api_client.post(
            "/graphql/",
            data={"query": query, "variables": variables or {}},
            format="json",
            **kwargs,
        )

    return _query


@pytest.fixture
def graphql_auth_client(auth_client: APIClient) -> Callable[..., Any]:
    """
    Authenticated client for GraphQL testing.
    """

    def _query(query: str, variables: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return auth_client.post(
            "/graphql/",
            data={"query": query, "variables": variables or {}},
            format="json",
            **kwargs,
        )

    return _query


# ============================================================================
# AI Testing Fixtures
# ============================================================================


@pytest.fixture
def poll_with_data(db: Any, test_user: Any) -> Any:
    """
    Create a complete poll with questions, options, and votes for AI testing.
    """
    from apps.polls.models import Option, Poll, Question, Vote

    poll = Poll.objects.create(
        title="Climate Change Survey",
        description="Survey about climate change awareness",
        created_by=test_user,
        is_active=True,
    )

    # Question 1: Multiple choice
    q1 = Question.objects.create(
        poll=poll,
        text="How concerned are you about climate change?",
        question_type="single",
        order=1,
    )
    opt1_1 = Option.objects.create(question=q1, text="Very concerned", order=1)
    opt1_2 = Option.objects.create(question=q1, text="Somewhat concerned", order=2)
    Option.objects.create(question=q1, text="Not concerned", order=3)  # opt1_3 unused

    # Question 2: Yes/No
    q2 = Question.objects.create(
        poll=poll,
        text="Do you believe human activity contributes to climate change?",
        question_type="single",
        order=2,
    )
    opt2_1 = Option.objects.create(question=q2, text="Yes", order=1)
    Option.objects.create(question=q2, text="No", order=2)  # opt2_2 unused

    # Add some votes
    user2 = User.objects.create_user(email="voter1@example.com", password="pass")  # noqa: S106
    user3 = User.objects.create_user(email="voter2@example.com", password="pass")  # noqa: S106

    Vote.objects.create(user=test_user, question=q1, option=opt1_1)
    Vote.objects.create(user=user2, question=q1, option=opt1_1)
    Vote.objects.create(user=user3, question=q1, option=opt1_2)

    Vote.objects.create(user=test_user, question=q2, option=opt2_1)
    Vote.objects.create(user=user2, question=q2, option=opt2_1)
    Vote.objects.create(user=user3, question=q2, option=opt2_1)

    return poll


@pytest.fixture
def mock_ai_service(mocker: Any) -> dict[str, str | dict[str, Any]]:
    """
    A unified mock for AI services (Poll and Insight generation).
    """
    poll_response = {
        "title": "Employee Satisfaction Survey",
        "description": "A survey to gauge employee satisfaction levels",
        "questions": [
            {
                "text": "How satisfied are you with your current role?",
                "type": "single",
                "options": ["Satisfied", "Neutral", "Dissatisfied"],
            },
            {
                "text": "Would you recommend this company?",
                "type": "single",
                "options": ["Yes", "No"],
            },
        ],
    }
    insight_response = (
        "Based on the poll data, users show high awareness of issues including climate change."
    )

    def mock_invoke(messages: Any, **kwargs: Any) -> Any:
        # Check messages to decide what to return
        prompt = str(messages)
        mock_msg = mocker.Mock()
        if "poll structure" in prompt.lower() or "generate a poll" in prompt.lower():
            mock_msg.content = json.dumps(poll_response)
        else:
            mock_msg.content = insight_response
        return mock_msg

    mock_llm = mocker.Mock()
    mock_llm.invoke.side_effect = mock_invoke

    mocker.patch("apps.ai.services.RAGService.get_llm", return_value=mock_llm)
    # Ensure RAGService sees an OpenAI key so provider is "openai"
    mocker.patch("django.conf.settings.OPENAI_API_KEY", "test-key")
    return {"poll": poll_response, "insight": insight_response}


@pytest.fixture
def mock_openai_poll_generation(mock_ai_service: dict[str, Any]) -> Any:
    return mock_ai_service["poll"]


@pytest.fixture
def mock_openai_insight_generation(mock_ai_service: dict[str, Any]) -> Any:
    return mock_ai_service["insight"]


@pytest.fixture
def mock_pgvector(mocker: Any) -> Any:
    """
    Mock PGVector for RAG ingestion testing.
    """
    mock_vector_store = mocker.Mock()
    mock_vector_store.add_documents.return_value = None

    mocker.patch("apps.ai.services.PGVector.from_documents", return_value=mock_vector_store)
    mocker.patch("apps.ai.services.PGVector.from_existing_index", return_value=mock_vector_store)

    return mock_vector_store


@pytest.fixture
def mock_openai_error(mocker: Any) -> Any:
    """
    Mock OpenAI API error for testing error handling.
    """
    mock_llm = mocker.Mock()
    mock_llm.invoke.side_effect = Exception("OpenAI API rate limit exceeded")

    mocker.patch("apps.ai.services.RAGService.get_llm", return_value=mock_llm)
    return mock_llm


# ============================================================================
# Polls Data Fixtures
# ============================================================================


@pytest.fixture
def poll(db: Any, test_user: Any) -> Any:
    """
    A simple poll created by the test user.
    """
    from apps.polls.models import Poll

    return Poll.objects.create(
        title="Sample Poll",
        description="A sample poll for testing",
        created_by=test_user,
    )


@pytest.fixture
def other_user(user_factory: Callable[..., Any]) -> Any:
    """
    Another test user.
    """
    return user_factory(email="other@example.com")


@pytest.fixture
def other_user_auth_client(api_client: APIClient, other_user: Any) -> APIClient:
    """
    An APIClient authenticated with 'other_user'.
    """
    api_client.force_login(user=other_user)
    api_client.force_authenticate(user=other_user)
    return api_client


@pytest.fixture
def question(db: Any, poll: Any) -> Any:
    """
    A sample question for a poll.
    """
    from apps.polls.models import Question

    return Question.objects.create(
        poll=poll, text="What is your favorite color?", question_type="single"
    )


@pytest.fixture
def option(db: Any, question: Any) -> Any:
    """
    A sample option for a question.
    """
    from apps.polls.models import Option

    return Option.objects.create(question=question, text="Blue")
