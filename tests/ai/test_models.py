import pytest
from django.contrib.auth import get_user_model

from apps.ai.models import AnalysisRequest
from apps.polls.models import Poll

User = get_user_model()


@pytest.mark.django_db
class TestAIModels:
    def test_analysis_request_str(self) -> None:
        user = User.objects.create(email="test@example.com")
        poll = Poll.objects.create(title="Test Poll", created_by=user)
        analysis = AnalysisRequest.objects.create(
            user=user, poll=poll, query="test query", response="test response"
        )
        assert str(analysis) == f"Analysis by {user} on Poll {poll.slug}"
