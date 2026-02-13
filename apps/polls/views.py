from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, permissions, serializers, viewsets

from apps.core.pagination import StandardResultsSetPagination

from .models import Option, Poll, Question, Vote
from .serializers import (
    OptionSerializer,
    PollSerializer,
    QuestionSerializer,
    VoteSerializer,
)


@extend_schema(tags=["Polls"])
class PollViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows polls to be viewed or edited.
    """

    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    lookup_field = "slug"
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        if not self.request.user.is_authenticated:
            raise exceptions.PermissionDenied()
        serializer.save(created_by=self.request.user)


@extend_schema(tags=["Questions"])
class QuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for questions.
    """

    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    lookup_field = "slug"
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@extend_schema(tags=["Options"])
class OptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for options.
    """

    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    lookup_field = "slug"
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@extend_schema(tags=["Votes"])
class VoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for votes.
    """

    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    lookup_field = "slug"
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        question = serializer.validated_data.get("question")
        user = self.request.user
        if not user.is_authenticated:
            raise exceptions.PermissionDenied()

        if Vote.objects.filter(question=question, user=user).exists():
            raise serializers.ValidationError(
                {"detail": "You have already voted on this question."}
            )
        serializer.save(user=user)
