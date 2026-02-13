from celery import shared_task
from django.apps import apps

from apps.distribution.models import DistributionAnalytics


@shared_task  # type: ignore[untyped-decorator]
def log_distribution_event_task(
    poll_id: int,
    event_type: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    referrer: str | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Background task to log a distribution event to the database.
    """
    Poll = apps.get_model("polls", "Poll")
    try:
        poll = Poll.objects.get(id=poll_id)
        DistributionAnalytics.objects.create(
            poll=poll,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent or "",
            referrer=referrer or "",
            metadata=metadata or {},
        )
    except Poll.DoesNotExist:
        pass
