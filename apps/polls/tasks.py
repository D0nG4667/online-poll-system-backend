import logging

from celery import shared_task
from django.core.cache import cache
from django.db.models import Count

from .models import Poll

logger = logging.getLogger(__name__)

# Cache timeout in seconds (e.g., 5 minutes)
CACHE_TIMEOUT = 60 * 5


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def aggregate_votes(self, poll_id):
    """
    Recalculates and caches vote counts for a specific poll asynchronously.

    This task:
    1. Aggregates votes for all questions and options in the poll.
    2. Updates a Redis cache key with the results for high-performance read access.
    3. Handles potential race conditions or database locks gracefully via retry.

    Key Pattern: `poll_{id}_votes` -> { question_id: { option_id: count } }
    """
    try:
        poll = Poll.objects.get(id=poll_id)
        logger.info(f"Starting vote aggregation for Poll: {poll.title} ({poll.id})")

        # structure: { question_id: { option_id: count, 'total': count } }
        aggregation_result = {}
        total_poll_votes = 0

        # Prefetch relationships to minimize queries
        questions = poll.questions.prefetch_related("options").all()

        for question in questions:
            # Aggregate votes per option
            # Returns: <QuerySet [{'option': 1, 'count': 5}, ...]>
            vote_counts = question.votes.values("option").annotate(count=Count("id"))

            option_map = {item["option"]: item["count"] for item in vote_counts}
            question_total = sum(option_map.values())

            # Ensure all options are present, even with 0 votes
            for option in question.options.all():
                if option.id not in option_map:
                    option_map[option.id] = 0

            aggregation_result[question.id] = {
                "options": option_map,
                "total_votes": question_total,
            }
            total_poll_votes += question_total

        # Cache the result
        cache_key = f"poll_{poll.id}_votes"
        cache.set(cache_key, aggregation_result, timeout=CACHE_TIMEOUT)

        logger.info(
            f"Poll {poll.id} aggregation complete. "
            f"Total votes: {total_poll_votes}. Cached to {cache_key}"
        )
        return {"poll_id": poll.id, "total_votes": total_poll_votes, "status": "cached"}

    except Poll.DoesNotExist:
        logger.error(f"Poll with ID {poll_id} not found during aggregation.")
        return f"Poll {poll_id} not found."
    except Exception as exc:
        logger.error(f"Error aggregating votes for poll {poll_id}: {exc}")
        # Retry on transient errors (e.g., DB lock, connection issue)
        raise self.retry(exc=exc) from exc


@shared_task
def send_poll_notification(poll_id, notification_type="closed"):
    """
    Sends notifications related to poll events (e.g., poll closed, results available).

    Args:
        poll_id (int): ID of the poll.
        notification_type (str): Type of notification ('closed', 'reminder', etc.)
    """
    try:
        poll = Poll.objects.get(id=poll_id)
        creator = poll.created_by

        logger.info(
            f"Preparing to send '{notification_type}' notification for Poll {poll.id}"
        )

        # Placeholder for actual Email/WebSocket logic
        # Checking user preferences would happen here when a user is added to the poll.

        message = ""
        if notification_type == "closed":
            message = f"Your poll '{poll.title}' has ended. View the results now."
        elif notification_type == "reminder":
            message = f"Reminder: The poll '{poll.title}' is closing soon!"

        # Simulate sending email
        logger.info(f"🚀 [MOCK] Sending Email to {creator.email}: {message}")

        return f"Notification '{notification_type}' sent to {creator.email}"

    except Poll.DoesNotExist:
        logger.warning(f"Poll {poll_id} not found for notification.")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
