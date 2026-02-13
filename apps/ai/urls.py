from django.urls import path

from apps.ai.views import (
    GeneratePollFromPromptView,
    GeneratePollInsightView,
    IngestPollDataView,
    PollInsightHistoryView,
)

app_name = "ai"

urlpatterns = [
    path(
        "generate-poll/",
        GeneratePollFromPromptView.as_view(),
        name="generate-poll-from-prompt",
    ),
    path(
        "insights/generate/",
        GeneratePollInsightView.as_view(),
        name="generate-insight",
    ),
    path("ingest/", IngestPollDataView.as_view(), name="ingest-poll-data"),
    path(
        "insights/history/<str:slug>/",
        PollInsightHistoryView.as_view(),
        name="insight-history",
    ),
]
