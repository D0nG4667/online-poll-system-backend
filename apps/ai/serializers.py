from rest_framework import serializers

from apps.ai.models import AnalysisRequest


class GeneratePollRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(
        max_length=1000,
        help_text="Natural language description of the poll you want to create",
    )


class GeneratedPollResponseSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    questions = serializers.JSONField()
    provider = serializers.CharField()


class GenerateInsightRequestSerializer(serializers.Serializer):
    poll_id = serializers.IntegerField(help_text="ID of the poll to analyze")
    query = serializers.CharField(
        max_length=500, help_text="Question to ask about the poll"
    )


class GenerateInsightResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    insight = serializers.CharField()
    provider = serializers.CharField()


class IngestPollDataRequestSerializer(serializers.Serializer):
    poll_id = serializers.IntegerField(
        help_text="ID of the poll to ingest into vector store"
    )


class IngestPollDataResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    poll_id = serializers.IntegerField()


class AnalysisRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRequest
        fields = ["id", "query", "response", "provider_used", "created_at"]
