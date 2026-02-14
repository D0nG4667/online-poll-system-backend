from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

if TYPE_CHECKING:
    from rest_framework.request import Request

from apps.ai.models import AnalysisRequest
from apps.ai.serializers import (
    AnalysisRequestSerializer,
    GeneratedPollResponseSerializer,
    GenerateInsightRequestSerializer,
    GenerateInsightResponseSerializer,
    GeneratePollRequestSerializer,
    IngestPollDataRequestSerializer,
    IngestPollDataResponseSerializer,
)
from apps.ai.services import RAGService
from apps.polls.models import Poll


class GeneratePollFromPromptView(APIView):
    """
    Generate a complete poll structure from a natural language description.
    Makes poll creation easier by using AI to generate questions and options.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GeneratePollRequestSerializer,
        responses={200: GeneratedPollResponseSerializer},
        description="Generate a poll structure using AI from a natural language prompt",
        tags=["AI"],
    )
    def post(self, request: "Request") -> Response:
        serializer = GeneratePollRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prompt = serializer.validated_data["prompt"]

        try:
            rag = RAGService()
            poll_structure = rag.generate_poll_structure(prompt)

            provider = "openai" if rag.openai_key else "gemini"

            response_data = {
                "title": poll_structure["title"],
                "description": poll_structure["description"],
                "questions": poll_structure["questions"],
                "provider": provider,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to generate poll: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GeneratePollInsightView(APIView):
    """
    Generate AI-powered insights for a poll based on a user query.
    Uses RAG (Retrieval-Augmented Generation) to provide data-driven answers.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GenerateInsightRequestSerializer,
        responses={200: GenerateInsightResponseSerializer},
        description="Generate AI insights about a specific poll",
        tags=["AI"],
    )
    def post(self, request: "Request") -> Response:
        serializer = GenerateInsightRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        poll_slug = serializer.validated_data["poll_slug"]
        query = serializer.validated_data["query"]

        try:
            poll = Poll.objects.get(slug=poll_slug)
        except Poll.DoesNotExist:
            return Response(
                {"error": f"Poll with slug {poll_slug} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            rag = RAGService()
            # Pass poll.id to service since it still expects ID for now,
            # or update service to take slug.
            # Plan says: "Service methods like generate_insight will accept slug"
            # So let's pass slug to service.
            insight = rag.generate_insight(poll.slug, query)

            provider = "openai" if rag.openai_key else "gemini"

            # Save to database
            AnalysisRequest.objects.create(
                user=request.user if request.user.is_authenticated else None,  # type: ignore
                poll=poll,
                query=query,
                response=insight,
                provider_used=provider,
            )

            response_data = {
                "query": query,
                "insight": insight,
                "provider": provider,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to generate insight: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class IngestPollDataView(APIView):
    """
    Ingest poll data into the vector store for AI analysis.
    Converts poll data into embeddings for semantic search.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=IngestPollDataRequestSerializer,
        responses={200: IngestPollDataResponseSerializer},
        description="Ingest poll data into vector database for AI analysis",
        tags=["AI"],
    )
    def post(self, request: "Request") -> Response:
        serializer = IngestPollDataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        poll_slug = serializer.validated_data["poll_slug"]

        try:
            rag = RAGService()
            # Service will accept slug
            rag.ingest_poll_data(poll_slug)

            response_data = {
                "message": (f"Successfully ingested poll {poll_slug} data into vector store"),
                "poll_slug": poll_slug,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to ingest poll data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PollInsightHistoryView(APIView):
    """
    Retrieve all AI insights generated for a specific poll.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: AnalysisRequestSerializer(many=True)},
        description="Get history of AI-generated insights for a poll",
        tags=["AI"],
    )
    def get(self, request: "Request", slug: str) -> Response:
        insights = AnalysisRequest.objects.filter(poll__slug=slug).order_by("-created_at")
        serializer = AnalysisRequestSerializer(insights, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
