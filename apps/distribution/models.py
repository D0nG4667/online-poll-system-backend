from django.db import models
from django.utils.translation import gettext_lazy as _


class DistributionEvent(models.TextChoices):
    LINK_OPEN = "LINK_OPEN", _("Link Open")
    QR_SCAN = "QR_SCAN", _("QR Scan")
    EMBED_LOAD = "EMBED_LOAD", _("Embed Load")
    SOCIAL_SHARE = "SOCIAL_SHARE", _("Social Share Click")


class DistributionAnalytics(models.Model):
    """
    Tracks how users interact with poll distribution channels.
    """

    poll = models.ForeignKey(
        "polls.Poll", on_delete=models.CASCADE, related_name="distribution_analytics"
    )
    event_type = models.CharField(
        max_length=20, choices=DistributionEvent.choices, db_index=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    # Metadata for deep analysis
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(max_length=500, blank=True)

    # JSONB for flexible device/browser/location data
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Distribution Analytics")
        verbose_name_plural = _("Distribution Analytics")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.poll.title} - {self.event_type} at {self.timestamp}"
