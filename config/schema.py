import strawberry

from apps.ai.schema import Mutation as AIMutation
from apps.ai.schema import Query as AIQuery
from apps.distribution.schema import Query as DistributionQuery
from apps.polls.schema import Query as PollsQuery


@strawberry.type
class Query(PollsQuery, AIQuery, DistributionQuery):
    pass


@strawberry.type
class Mutation(AIMutation):
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)
