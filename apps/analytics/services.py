import logging
from datetime import timedelta
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone

from apps.polls.models import Poll, PollView, Vote

logger = logging.getLogger(__name__)

User = get_user_model()


class AnalyticsService:
    """
    Service for calculating poll analytics, trends, and engagement metrics.
    Includes Redis caching for performance.
    """

    @staticmethod
    def get_period_delta(period: str) -> timedelta:
        periods = {
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
            "1y": timedelta(days=365),
        }
        return periods.get(period, timedelta(days=30))

    @classmethod
    def get_stats(cls, user: Any, period: str = "30d") -> dict[str, Any]:
        """
        Calculates total polls, responses, views, and response rate.
        Includes percentage change from the previous equivalent period.
        """
        cache_key = f"analytics:stats:{user.id}:{period}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cast(dict[str, Any], cached_data)

        now = timezone.now()
        delta = cls.get_period_delta(period)
        start_date = now - delta
        prev_start_date = start_date - delta

        # Current Period Data
        polls = Poll.objects.filter(created_by=user)
        current_polls_count = polls.filter(created_at__gte=start_date).count()

        # Responses (Votes)
        current_votes = Vote.objects.filter(
            question__poll__created_by=user, created_at__gte=start_date
        ).count()

        # Views
        current_views = PollView.objects.filter(
            poll__created_by=user, created_at__gte=start_date
        ).count()

        # Previous Period Data (for % change)
        prev_polls_count = polls.filter(created_at__range=(prev_start_date, start_date)).count()
        prev_votes = Vote.objects.filter(
            question__poll__created_by=user,
            created_at__range=(prev_start_date, start_date),
        ).count()
        prev_views = PollView.objects.filter(
            poll__created_by=user, created_at__range=(prev_start_date, start_date)
        ).count()

        def calc_change(current: int, prev: int) -> float:
            if prev == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - prev) / prev) * 100, 2)

        stats = {
            "total_polls": polls.count(),
            "polls_change": calc_change(current_polls_count, prev_polls_count),
            "total_responses": current_votes,
            "responses_change": calc_change(current_votes, prev_votes),
            "total_views": current_views,
            "views_change": calc_change(current_views, prev_views),
            "avg_response_rate": round((current_votes / current_views * 100), 2)
            if current_views > 0
            else 0.0,
            "response_rate_change": calc_change(
                int((current_votes / current_views * 100) if current_views > 0 else 0.0),
                int((prev_votes / prev_views * 100) if prev_views > 0 else 0.0),
            ),
        }

        cache.set(cache_key, stats, timeout=600)  # 10 minutes
        return cast(dict[str, Any], stats)

    @classmethod
    def get_trends(cls, user: Any, period: str = "30d") -> dict[str, list[dict[str, Any]]]:
        """
        Returns time-series data for poll creation and response rates.
        """
        cache_key = f"analytics:trends:{user.id}:{period}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cast(dict[str, list[dict[str, Any]]], cached_data)

        now = timezone.now()
        delta = cls.get_period_delta(period)
        start_date = now - delta

        # Decision: Use Day truncation for <= 30d, Month for > 30d
        trunc_func = TruncDay if delta.days <= 30 else TruncMonth

        # Poll Creation Trend
        poll_trends = (
            Poll.objects.filter(created_by=user, created_at__gte=start_date)
            .annotate(date=trunc_func("created_at"))
            .values("date")
            .annotate(value=Count("id"))
            .order_by("date")
        )

        # Vote Trend
        vote_trends = (
            Vote.objects.filter(question__poll__created_by=user, created_at__gte=start_date)
            .annotate(date=trunc_func("created_at"))
            .values("date")
            .annotate(value=Count("id"))
            .order_by("date")
        )

        trends = {
            "poll_creation": [
                {"date": str(t["date"]), "value": float(t["value"])} for t in poll_trends
            ],
            "response_rate": [
                {"date": str(t["date"]), "value": float(t["value"])} for t in vote_trends
            ],
        }

        cache.set(cache_key, trends, timeout=900)  # 15 minutes
        return cast(dict[str, list[dict[str, Any]]], trends)
