from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.polls.models import Poll, Question, Vote, Option
from apps.analytics.services import AnalyticsService

User = get_user_model()


class AnalyticsServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="password"
        )
        self.poll = Poll.objects.create(
            title="Test Poll",
            description="Test Description",
            created_by=self.user,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            is_active=True,
        )
        self.question = Question.objects.create(
            poll=self.poll, text="Test Question?", question_type="single", order=1
        )
        self.option = Option.objects.create(
            question=self.question, text="Option 1", order=1
        )

    def test_get_trends(self):
        # Create a vote
        Vote.objects.create(user=self.user, question=self.question, option=self.option)

        trends = AnalyticsService.get_trends(self.user, period="30d")

        self.assertIn("poll_creation", trends)
        self.assertIn("response_rate", trends)
        self.assertTrue(len(trends["poll_creation"]) > 0)
        self.assertTrue(len(trends["response_rate"]) > 0)
        self.assertEqual(trends["poll_creation"][0]["value"], 1)
        self.assertEqual(trends["response_rate"][0]["value"], 1)
