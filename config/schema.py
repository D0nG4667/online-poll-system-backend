import strawberry

from apps.polls.schema import Query as PollsQuery


@strawberry.type
class Query(PollsQuery):
    pass


schema = strawberry.Schema(query=Query)
