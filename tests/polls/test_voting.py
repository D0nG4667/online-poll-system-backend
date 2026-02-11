import pytest
from apps.polls.models import Poll, Question, Option, Vote
from django.utils import timezone


@pytest.fixture
def poll_data(test_user):
    poll = Poll.objects.create(
        title="Test Poll", created_by=test_user, description="Testing voting logic"
    )
    question = Question.objects.create(poll=poll, text="Which is best?")
    option_a = Option.objects.create(question=question, text="Option A")
    option_b = Option.objects.create(question=question, text="Option B")
    return poll, question, option_a, option_b


@pytest.mark.django_db
class TestVoting:
    def test_unique_vote_constraint(self, test_user, poll_data):
        """
        Verify that a user can only vote once per question.
        """
        _, question, option_a, option_b = poll_data

        # First vote
        Vote.objects.create(user=test_user, question=question, option=option_a)

        # Second vote attempt on same question should fail
        with pytest.raises(Exception):  # IntegrityError
            Vote.objects.create(user=test_user, question=question, option=option_b)

    def test_vote_count_aggregation(self, user_factory, poll_data):
        """
        Verify that votes count correctly (simulating aggregation logic).
        """
        _, question, option_a, _ = poll_data

        # Create 3 users and 3 votes
        for i in range(3):
            u = user_factory(email=f"user{i}@test.com")
            Vote.objects.create(user=u, question=question, option=option_a)

        assert Vote.objects.filter(option=option_a).count() == 3
