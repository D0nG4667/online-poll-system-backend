import strawberry
from django.db.models import Count
from strawberry.permission import BasePermission
from strawberry.types import Info

from apps.ai.services import RAGService
from apps.polls.models import Poll

from .services import AnalyticsService


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source, info: Info, **kwargs) -> bool:
        return info.context.request.user.is_authenticated


@strawberry.type
class AnalyticsStats:
    total_polls: int
    polls_change: float
    total_responses: int
    responses_change: float
    total_views: int
    views_change: float
    avg_response_rate: float


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
    votes_count: int
    views_count: int
    engagement_score: float


@strawberry.type
class AnalyticsQuery:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def analytics_stats(self, info: Info, period: str = "30d") -> AnalyticsStats:
        user = info.context.request.user
        stats_data = AnalyticsService.get_stats(user, period)
        return AnalyticsStats(**stats_data)

    @strawberry.field(permission_classes=[IsAuthenticated])
    def analytics_trends(self, info: Info, period: str = "30d") -> AnalyticsTrends:
        user = info.context.request.user
        trends_data = AnalyticsService.get_trends(user, period)
        return AnalyticsTrends(
            poll_creation=[TrendDataPoint(**p) for p in trends_data["poll_creation"]],
            response_rate=[TrendDataPoint(**r) for r in trends_data["response_rate"]],
        )

    @strawberry.field(permission_classes=[IsAuthenticated])
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

        return [
            TopPollNode(
                id=strawberry.ID(str(p.id)),
                title=p.title,
                votes_count=p.votes_count,
                views_count=p.views_count,
                engagement_score=round((p.votes_count / p.views_count * 100), 2)
                if p.views_count > 0
                else 0.0,
            )
            for p in polls
        ]


@strawberry.type
class AnalyticsMutation:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def generate_insight(self, info: Info, poll_id: int, query: str) -> str:
        rag_service = RAGService()
        if poll_id == 0:
            return rag_service.generate_insight(
                poll_id, f"Overall User Analytics Context: {query}"
            )

        return rag_service.generate_insight(poll_id, query)
