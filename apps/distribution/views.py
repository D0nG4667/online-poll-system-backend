from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse

if TYPE_CHECKING:
    from rest_framework.request import Request
from django.shortcuts import get_object_or_404, render
from django.views import View
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import views
from rest_framework.response import Response

from apps.distribution.models import DistributionAnalytics, DistributionEvent
from apps.distribution.serializers import (
    PollDistributionAnalyticsResponseSerializer,
    PollDistributionInfoSerializer,
    PublicPollSerializer,
)
from apps.distribution.services import DistributionService
from apps.distribution.tasks import log_distribution_event_task
from apps.polls.models import Poll


class PublicPollPageView(View):
    """
    Template-based view for public poll sharing with social metadata.
    """

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        poll = get_object_or_404(Poll, slug=slug, is_active=True)

        # Log event asynchronously
        log_distribution_event_task.delay(
            poll.id,
            DistributionEvent.LINK_OPEN,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
            referrer=request.META.get("HTTP_REFERER"),
        )

        return render(request, "distribution/public_poll.html", {"poll": poll})


class PublicPollDetailView(views.APIView):
    """
    Returns public data for a poll identified by slug.
    Also logs a LINK_OPEN event.
    """

    permission_classes = []  # Public access

    @extend_schema(
        tags=["Distribution"],
        summary="Get Public Poll Detail",
        description="Retrieves basic poll information accessible\n"
        "by anyone with the shareable link.",
        responses={200: PublicPollSerializer},
    )
    def get(self, request: "Request", slug: str) -> Response:
        poll = get_object_or_404(Poll, slug=slug, is_active=True)

        # Log event asynchronously
        log_distribution_event_task.delay(
            poll.id,
            DistributionEvent.LINK_OPEN,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
            referrer=request.META.get("HTTP_REFERER"),
        )

        # We use a specific PublicPollSerializer here for clean structure
        serializer = PublicPollSerializer(poll)
        return Response(serializer.data)


class PollQRCodeView(views.APIView):
    """
    Returns a QR code image for a poll.
    Logs a QR_SCAN event.
    """

    permission_classes = []

    @extend_schema(
        tags=["Distribution"],
        summary="Generate Poll QR Code",
        description="Generates a PNG or SVG QR code for the poll's public URL.",
        responses={
            (200, "image/png"): OpenApiTypes.BINARY,
            (200, "image/svg+xml"): OpenApiTypes.BYTE,
        },
    )
    def get(self, request: "Request", slug: str) -> HttpResponse:
        poll = get_object_or_404(Poll, slug=slug, is_active=True)

        img_format = request.query_params.get("format", "png")
        qr_content = DistributionService.generate_qr_code(poll, img_format=img_format)

        # Log event
        log_distribution_event_task.delay(
            poll.id,
            DistributionEvent.QR_SCAN,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
            referrer=request.META.get("HTTP_REFERER"),
        )

        content_type = "image/svg+xml" if img_format == "svg" else "image/png"
        return HttpResponse(qr_content, content_type=content_type)


class PollEmbedView(views.APIView):
    """
    Returns embed information or snippet.
    Logs an EMBED_LOAD event.
    """

    permission_classes = []

    @extend_schema(
        tags=["Distribution"],
        summary="Get Poll Embed Details",
        description="Returns the iframe embed snippet and canonical public URL.",
        responses={200: PollDistributionInfoSerializer},
    )
    def get(self, request: "Request", slug: str) -> Response:
        poll = get_object_or_404(Poll, slug=slug, is_active=True)

        # Log event asynchronously
        log_distribution_event_task.delay(
            poll.id,
            DistributionEvent.EMBED_LOAD,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
            referrer=request.META.get("HTTP_REFERER"),
        )

        return Response(
            PollDistributionInfoSerializer(
                {
                    "embed_code": DistributionService.get_embed_code(poll),
                    "public_url": DistributionService.get_public_url(poll),
                    "qr_code_url": f"{DistributionService.get_public_url(poll)}qr/",
                }
            ).data
        )


class PollDistributionAnalyticsView(views.APIView):
    """
    Returns distribution analytics for a poll.
    Only accessible by the poll creator.
    """

    @extend_schema(
        tags=["Analytics"],
        summary="Get Distribution Analytics",
        description=(
            "Retrieves aggregated distribution metrics & recent events for poll owners."
        ),
        responses={200: PollDistributionAnalyticsResponseSerializer},
    )
    def get(self, request: "Request", slug: str) -> Response:
        poll = get_object_or_404(Poll, slug=slug, created_by=request.user)
        analytics = DistributionAnalytics.objects.filter(poll=poll)

        summary = {
            "total_link_opens": analytics.filter(
                event_type=DistributionEvent.LINK_OPEN
            ).count(),
            "total_qr_scans": analytics.filter(
                event_type=DistributionEvent.QR_SCAN
            ).count(),
            "total_embed_loads": analytics.filter(
                event_type=DistributionEvent.EMBED_LOAD
            ).count(),
        }

        serializer = PollDistributionAnalyticsResponseSerializer(
            {"summary": summary, "recent_events": analytics[:100]}
        )
        return Response(serializer.data)
