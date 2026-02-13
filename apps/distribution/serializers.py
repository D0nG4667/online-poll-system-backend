from rest_framework import serializers

from apps.distribution.models import DistributionAnalytics
from apps.polls.models import Poll


class DistributionAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributionAnalytics
        fields = [
            "event_type",
            "timestamp",
            "ip_address",
            "user_agent",
            "referrer",
            "metadata",
        ]


class PollDistributionInfoSerializer(serializers.Serializer):
    public_url = serializers.URLField()
    qr_code_url = serializers.URLField()
    embed_code = serializers.CharField()


class PublicPollSerializer(serializers.ModelSerializer):
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = Poll
        fields = ["id", "title", "description", "is_open"]


class DistributionSummarySerializer(serializers.Serializer):
    total_link_opens = serializers.IntegerField()
    total_qr_scans = serializers.IntegerField()
    total_embed_loads = serializers.IntegerField()


class PollDistributionAnalyticsResponseSerializer(serializers.Serializer):
    summary = DistributionSummarySerializer()
    recent_events = DistributionAnalyticsSerializer(many=True)
