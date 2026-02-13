from django.conf import settings
from django.db import models

from apps.polls.models import Poll


class AnalysisRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    query = models.TextField()
    response = models.TextField()
    provider_used = models.CharField(max_length=50, default="openai")  # openai/gemini
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Analysis by {self.user} on Poll {self.poll_id}"
