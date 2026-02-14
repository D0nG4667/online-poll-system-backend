import logging

import strawberry
import strawberry_django
from django.core.cache import cache
from strawberry import auto
from strawberry_django.fields.types import field_type_map

from apps.core.fields import RandomSlugField

from . import models

# Register custom field for 'auto' support in strawberry-django
field_type_map.update({RandomSlugField: str})

logger = logging.getLogger(__name__)


@strawberry_django.filter_type(models.Poll, lookups=True)
class PollFilter:
    id: auto
    title: auto
    is_active: auto


@strawberry_django.order_type(models.Poll)
class PollOrder:
    title: auto
    created_at: auto


@strawberry_django.type(models.Option)
class OptionType:
    id: auto
    slug: auto
    text: auto
    order: auto

    @strawberry.field
    def vote_count(self: models.Option) -> int:
        # Try to fetch from cache generic pattern: poll_{id}_votes
        try:
            # We need the poll_id. Option -> Question -> Poll
            poll = self.question.poll
            poll_id = poll.id
            cache_key = f"poll_{poll_id}_votes"
            cached_data = cache.get(cache_key)

            if cached_data:
                # Structure: { question_id: { 'options': { opt_id: count }, ... } }
                q_data = cached_data.get(self.question_id)
                if q_data:
                    return int(q_data.get("options", {}).get(self.id, 0))
        except Exception as e:
            logger.warning(f"Failed to fetch vote_count from cache for Option {self.id}: {e}")

        return self.votes.count()


@strawberry_django.type(models.Question)
class QuestionType:
    id: auto
    slug: auto
    text: auto
    question_type: auto
    order: auto
    options: list[OptionType]

    @strawberry.field
    def total_votes(self: models.Question) -> int:
        try:
            poll = self.poll
            cache_key = f"poll_{poll.id}_votes"
            cached_data = cache.get(cache_key)

            if cached_data:
                q_data = cached_data.get(self.id)
                if q_data:
                    return int(q_data.get("total_votes", 0))
        except Exception as e:
            logger.warning(f"Failed to fetch total_votes from cache for Question {self.id}: {e}")

        return self.votes.count()


@strawberry_django.type(models.Poll)
class PollType(strawberry.relay.Node):
    title: auto
    description: auto
    created_at: auto
    updated_at: auto

    slug: auto

    start_date: auto
    end_date: auto
    is_active: auto
    is_open: bool
    questions: list[QuestionType]


@strawberry.type
class Query:
    polls: strawberry.relay.ListConnection[PollType] = strawberry_django.connection(
        strawberry.relay.ListConnection[PollType],
        filters=PollFilter,
        ordering=PollOrder,
    )
    poll: PollType = strawberry_django.field()
