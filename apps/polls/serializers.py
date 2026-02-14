from rest_framework import serializers

from .models import Option, Poll, Question, Vote


class OptionSerializer(serializers.ModelSerializer):
    question = serializers.SlugRelatedField(slug_field="slug", queryset=Question.objects.all())

    class Meta:
        model = Option
        fields = ["id", "slug", "question", "text", "order"]


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)
    poll = serializers.SlugRelatedField(slug_field="slug", queryset=Poll.objects.all())

    class Meta:
        model = Question
        fields = ["id", "slug", "poll", "text", "question_type", "order", "options"]


class PollSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    created_by: serializers.StringRelatedField = serializers.StringRelatedField(read_only=True)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = Poll
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "created_by",
            "start_date",
            "end_date",
            "is_active",
            "is_open",
            "questions",
            "created_at",
            "updated_at",
        ]


class VoteSerializer(serializers.ModelSerializer):
    user: serializers.StringRelatedField = serializers.StringRelatedField(read_only=True)
    question = serializers.SlugRelatedField(slug_field="slug", queryset=Question.objects.all())
    option = serializers.SlugRelatedField(slug_field="slug", queryset=Option.objects.all())

    class Meta:
        model = Vote
        fields = ["id", "slug", "user", "question", "option", "created_at"]
