"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, HttpResponse, JsonResponse  # noqa: F401
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from strawberry.django.views import GraphQLView

from config.schema import schema

# def trigger_error(request: HttpRequest) -> HttpResponse:
#     _ = 1 / 0
#     return HttpResponse(status=500)


# Base Project URLs
base_patterns = [
    path("healthz", lambda r: HttpResponse("OK", status=200)),
    path("admin", admin.site.urls),
    path("graphql", csrf_exempt(GraphQLView.as_view(schema=schema))),
    path(
        "account/provider/callback",
        lambda r: JsonResponse(
            {"detail": "This is a placeholder for the frontend callback."}, status=200
        ),
        name="frontend-callback-placeholder",
    ),
]

# Authentication (Headless & Allauth)
auth_patterns = [
    path("_allauth/", include("allauth.headless.urls")),
    path("accounts", include("allauth.urls")),
]

# Documentation & Schema
doc_patterns = [
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/auth-ui",
        SpectacularSwaggerView.as_view(url="/_allauth/openapi.json"),
        name="swagger-ui-auth",
    ),
    path(
        "api/schema/redoc",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

# API Version 1
api_v1_patterns = [
    path("", include("apps.core.urls")),
    path("users/", include("apps.users.urls")),
    path("", include("apps.polls.urls")),
    path("ai/", include("apps.ai.urls")),
    path("distribution/", include("apps.distribution.urls")),
]

urlpatterns = (
    base_patterns
    + auth_patterns
    + doc_patterns
    + [
        path("api/v1/", include(api_v1_patterns)),
    ]
)


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
