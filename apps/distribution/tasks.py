from celery import shared_task
from django.apps import apps

from apps.distribution.models import DistributionAnalytics


@shared_task
def log_distribution_event_task(
    poll_id, event_type, ip_address=None, user_agent=None, referrer=None, metadata=None
):
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
            user_agent=user_agent,
            referrer=referrer,
            metadata=metadata or {},
        )
    except Poll.DoesNotExist:
        pass
