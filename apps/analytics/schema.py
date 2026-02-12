from typing import Any

import strawberry
from django.db.models import Count
from strawberry.permission import BasePermission
from strawberry.types import Info

from apps.ai.services import RAGService
from apps.polls.models import Poll

from .services import AnalyticsService


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: Any, info: Info, **kwargs: Any) -> bool:
        return bool(info.context.request.user.is_authenticated)


@strawberry.type
class AnalyticsStats:
    total_polls: int
    polls_change: float
    total_responses: int
    responses_change: float
    total_views: int
    views_change: float
    avg_response_rate: float
    response_rate_change: float


@strawberry.type
class TrendDataPoint:
    date: str
    value: float


@strawberry.type
class AnalyticsTrends:
    poll_creation: list[TrendDataPoint]
    response_rate: list[TrendDataPoint]


@strawberry.type
class TopPollNode:
    id: strawberry.ID
    title: str
    slug: str
    votes_count: int
    views_count: int
    engagement_score: float
    responses: int
    views: int
    response_rate: float
    status: str
    created_at: str


@strawberry.type
class AnalyticsQuery:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    def analytics_stats(self, info: Info, period: str = "30d") -> AnalyticsStats:
        user = info.context.request.user
        stats_data = AnalyticsService.get_stats(user, period)
        return AnalyticsStats(**stats_data)

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    def analytics_trends(self, info: Info, period: str = "30d") -> AnalyticsTrends:
        user = info.context.request.user
        trends_data = AnalyticsService.get_trends(user, period)
        return AnalyticsTrends(
            poll_creation=[TrendDataPoint(**p) for p in trends_data["poll_creation"]],
            response_rate=[TrendDataPoint(**r) for r in trends_data["response_rate"]],
        )

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    def top_polls(
        self, info: Info, period: str = "30d", limit: int = 5
    ) -> list[TopPollNode]:
        user = info.context.request.user
        # Logic to find top polls based on engagement (votes + views)
        polls = (
            Poll.objects.filter(created_by=user)
            .annotate(votes_count=Count("questions__votes"), views_count=Count("views"))
            .order_by("-votes_count")[:limit]
        )

        def get_status(poll: Poll) -> str:
            if not poll.is_active:
                return "Closed"
            if poll.is_open:
                return "Active"
            # or Closed if end_date passed, is_open property handles logic
            return "Scheduled"

        return [
            TopPollNode(
                id=strawberry.ID(str(p.id)),
                title=p.title,
                slug=p.slug,
                votes_count=p.votes_count,
                views_count=p.views_count,
                engagement_score=round((p.votes_count / p.views_count * 100), 2)
                if p.views_count > 0
                else 0.0,
                responses=p.votes_count,
                views=p.views_count,
                response_rate=round((p.votes_count / p.views_count * 100), 2)
                if p.views_count > 0
                else 0.0,
                status="Active" if p.is_open else "Closed",
                created_at=str(p.created_at),
            )
            for p in polls
        ]


@strawberry.type
class AnalyticsMutation:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    def generate_insight(self, info: Info, poll_slug: str, query: str) -> str:
        rag_service = RAGService()
        return rag_service.generate_insight(poll_slug, query)
