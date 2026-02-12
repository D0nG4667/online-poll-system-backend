from typing import cast

import strawberry
import strawberry_django
from strawberry import auto
from strawberry.types import Info

from apps.distribution import models
from apps.distribution.services import DistributionService
from apps.polls.schema import PollType


@strawberry_django.type(models.DistributionAnalytics)
class DistributionAnalyticsType:
    event_type: auto
    timestamp: auto
    ip_address: auto
    user_agent: auto
    referrer: auto
    metadata: auto


@strawberry.type
class DistributionInfo:
    public_url: str
    qr_code_url: str
    embed_code: str


@strawberry.type
class PollDistributionSummary:
    total_link_opens: int
    total_qr_scans: int
    total_embed_loads: int
    recent_events: list[DistributionAnalyticsType]


@strawberry.type
class Query:
    @strawberry.field
    def public_poll(self, slug: str) -> PollType | None:
        from apps.polls.models import Poll

        try:
            return cast(PollType, Poll.objects.get(slug=slug, is_active=True))
        except Poll.DoesNotExist:
            return None

    @strawberry.field
    def poll_distribution_info(self, slug: str) -> DistributionInfo | None:
        from apps.polls.models import Poll

        try:
            poll = Poll.objects.get(slug=slug)
            return DistributionInfo(
                public_url=DistributionService.get_public_url(poll),
                qr_code_url=f"/api/v1/polls/{poll.slug}/qr/",
                embed_code=DistributionService.get_embed_code(poll),
            )
        except Poll.DoesNotExist:
            return None

    @strawberry.field
    def poll_distribution_analytics(
        self, info: Info, slug: str, limit: int = 50
    ) -> PollDistributionSummary | None:
        from apps.distribution.models import DistributionEvent
        from apps.polls.models import Poll

        user = info.context.request.user
        if not user.is_authenticated:
            return None

        try:
            poll = Poll.objects.get(slug=slug, created_by=user)
            analytics = models.DistributionAnalytics.objects.filter(poll=poll)

            return PollDistributionSummary(
                total_link_opens=analytics.filter(
                    event_type=DistributionEvent.LINK_OPEN
                ).count(),
                total_qr_scans=analytics.filter(
                    event_type=DistributionEvent.QR_SCAN
                ).count(),
                total_embed_loads=analytics.filter(
                    event_type=DistributionEvent.EMBED_LOAD
                ).count(),
                recent_events=cast(
                    list[DistributionAnalyticsType],
                    list(analytics.order_by("-timestamp")[:limit]),
                ),
            )
        except Poll.DoesNotExist:
            return None
