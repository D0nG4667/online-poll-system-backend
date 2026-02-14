from typing import cast

import strawberry
import strawberry_django
from django.contrib.auth import get_user_model
from strawberry.types import Info

from apps.ai.models import AnalysisRequest
from apps.ai.services import RAGService
from apps.polls.models import Poll

User = get_user_model()


@strawberry.type
class PollInsightType:
    query: str
    insight: str
    provider: str


@strawberry.type
class GeneratedPollType:
    title: str
    description: str
    questions: strawberry.scalars.JSON
    provider: str


@strawberry_django.type(AnalysisRequest)
class AnalysisRequestType:
    id: strawberry.ID
    query: str
    response: str
    provider_used: str
    created_at: strawberry.auto


@strawberry.type
class Query:
    @strawberry.field
    def poll_insight_history(
        self, info: Info, poll_slug: str, limit: int = 10
    ) -> list[AnalysisRequestType]:
        """Get all AI insights generated for a specific poll."""
        # We need to cast the queryset to list or use strawberry_django's magic.
        # But for list[AnalysisRequestType], Strawberry expects a list of objects
        # that match the type. AnalysisRequest objects match AnalysisRequestType.
        return cast(
            list[AnalysisRequestType],
            list(
                AnalysisRequest.objects.filter(poll__slug=poll_slug).order_by("-created_at")[:limit]
            ),
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    def ingest_poll_data(self, info: Info, poll_slug: str) -> str:
        """
        Ingest poll data into the vector store for AI analysis.
        Requires authentication.
        """
        if not info.context.request.user.is_authenticated:
            raise Exception("Authentication required")

        try:
            rag = RAGService()
            rag.ingest_poll_data(poll_slug)
            return f"Successfully ingested poll {poll_slug} data into vector store"
        except Exception as e:
            raise Exception(f"Failed to ingest poll data: {str(e)}") from e

    @strawberry.mutation
    def generate_poll_insight(self, info: Info, poll_slug: str, query: str) -> PollInsightType:
        """
        Generate AI-powered insights for a poll based on a user query.
        Requires authentication.
        """
        if not info.context.request.user.is_authenticated:
            raise Exception("Authentication required")

        try:
            # Get or create poll
            poll = Poll.objects.get(slug=poll_slug)

            # Generate insight using RAG
            rag = RAGService()
            insight = rag.generate_insight(poll_slug, query)

            # Determine which provider was used
            provider = "openai" if rag.openai_key else "gemini"

            # Save to database
            AnalysisRequest.objects.create(
                user=info.context.request.user,
                poll=poll,
                query=query,
                response=insight,
                provider_used=provider,
            )

            return PollInsightType(query=query, insight=insight, provider=provider)
        except Poll.DoesNotExist as e:
            raise Exception(f"Poll with slug {poll_slug} not found") from e
        except Exception as e:
            raise Exception(f"Failed to generate insight: {str(e)}") from e

    @strawberry.mutation
    def generate_poll_from_prompt(self, info: Info, prompt: str) -> GeneratedPollType:
        """
        Generate a complete poll structure from a natural language description.
        Makes poll creation easier by using AI to generate questions and options.
        Requires authentication.
        """
        if not info.context.request.user.is_authenticated:
            raise Exception("Authentication required")

        try:
            rag = RAGService()
            poll_structure = rag.generate_poll_structure(prompt)

            # Determine provider used
            provider = "openai" if rag.openai_key else "gemini"

            return GeneratedPollType(
                title=poll_structure["title"],
                description=poll_structure["description"],
                questions=poll_structure["questions"],
                provider=provider,
            )
        except Exception as e:
            raise Exception(f"Failed to generate poll: {str(e)}") from e


schema = strawberry.Schema(query=Query, mutation=Mutation)
