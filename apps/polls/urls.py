from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OptionViewSet, PollViewSet, QuestionViewSet, VoteViewSet

router = DefaultRouter()
router.register(r"polls", PollViewSet)
router.register(r"questions", QuestionViewSet)
router.register(r"options", OptionViewSet)
router.register(r"votes", VoteViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
