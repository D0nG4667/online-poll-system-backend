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
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from strawberry.django.views import GraphQLView

from config.schema import schema


def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('sentry-debug/', trigger_error),
    path("admin/", admin.site.urls),
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema))),
    # Frontend Callback Mocks (to avoid 404s when frontend is not running)
    path(
        "account/provider/callback",
        lambda r: JsonResponse(
            {"detail": "This is a placeholder for the frontend callback."}, status=200
        ),
        name="frontend-callback-placeholder",
    ),
    # Authentication
    # Authentication (Headless)
    path("_allauth/", include("allauth.headless.urls")),
    # Required by allauth for internal logic (providers/callbacks),
    # even in headless mode.
    path("accounts/", include("allauth.urls")),
    # Swagger/Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/auth-ui/",
        SpectacularSwaggerView.as_view(url="/_allauth/openapi.json"),
        name="swagger-ui-auth",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # App APIs
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/", include("apps.polls.urls")),
    path("api/v1/ai/", include("apps.ai.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
