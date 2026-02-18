from django.urls import path

from apps.distribution.views import (
    PollDistributionAnalyticsView,
    PollEmbedView,
    PollQRCodeView,
    PublicPollDetailView,
    PublicPollPageView,
)

app_name = "distribution"

urlpatterns = [
    # Template-based public page for social sharing
    path("polls/<slug:slug>", PublicPollPageView.as_view(), name="public-poll-page"),
    # Distribution endpoints
    path("polls/<slug:slug>/public", PublicPollDetailView.as_view(), name="public-poll"),
    path("polls/<slug:slug>/qr", PollQRCodeView.as_view(), name="poll-qr"),
    path("polls/<slug:slug>/embed", PollEmbedView.as_view(), name="poll-embed"),
    path(
        "polls/<slug:slug>/distribution/analytics",
        PollDistributionAnalyticsView.as_view(),
        name="poll-analytics",
    ),
]
