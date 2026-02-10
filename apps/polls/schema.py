import strawberry
import strawberry_django
from strawberry import auto

from . import models


@strawberry_django.filter(models.Poll, lookups=True)
class PollFilter:
    id: auto
    title: auto
    is_active: auto


@strawberry_django.order(models.Poll)
class PollOrder:
    title: auto
    created_at: auto


@strawberry_django.type(models.Option)
class OptionType:
    id: auto
    text: auto
    order: auto

    @strawberry.field
    def vote_count(self) -> int:
        return self.votes.count()


@strawberry_django.type(models.Question)
class QuestionType:
    id: auto
    text: auto
    question_type: auto
    order: auto
    options: list[OptionType]

    @strawberry.field
    def total_votes(self) -> int:
        return self.votes.count()


@strawberry_django.type(models.Poll)
class PollType:
    id: auto
    title: auto
    description: auto
    created_at: auto
    updated_at: auto
    start_date: auto
    end_date: auto
    is_active: auto
    is_open: bool
    questions: list[QuestionType]


@strawberry.type
class Query:
    polls: list[PollType] = strawberry_django.field(filters=PollFilter, order=PollOrder)
    poll: PollType = strawberry_django.field()
