from rest_framework import viewsets, permissions, serializers
from drf_spectacular.utils import extend_schema
from .models import Poll, Question, Option, Vote
from .serializers import (
    PollSerializer,
    QuestionSerializer,
    OptionSerializer,
    VoteSerializer,
)


@extend_schema(tags=["Polls"])
class PollViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows polls to be viewed or edited.
    """

    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@extend_schema(tags=["Questions"])
class QuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for questions.
    """

    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@extend_schema(tags=["Options"])
class OptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for options.
    """

    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@extend_schema(tags=["Votes"])
class VoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for votes.
    """

    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        question = serializer.validated_data.get("question")
        user = self.request.user
        if Vote.objects.filter(question=question, user=user).exists():
            raise serializers.ValidationError(
                {"detail": "You have already voted on this question."}
            )
        serializer.save(user=user)
