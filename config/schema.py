import strawberry

from apps.ai.schema import Mutation as AIMutation
from apps.ai.schema import Query as AIQuery
from apps.analytics.schema import AnalyticsMutation, AnalyticsQuery
from apps.distribution.schema import Query as DistributionQuery
from apps.polls.schema import Query as PollQuery


@strawberry.type
class Query(PollQuery, DistributionQuery, AnalyticsQuery, AIQuery):
    pass


@strawberry.type
class Mutation(AIMutation, AnalyticsMutation):
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)
