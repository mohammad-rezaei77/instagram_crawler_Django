# instagram_crawler/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CreateSessionView,
    PostDetailView,
    PostViewSet,
    SessionDetailView,
    SessionListCreateView,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet)

urlpatterns = [
    path("session/create/", CreateSessionView.as_view(), name="create_session"),
    path("session/", SessionListCreateView.as_view(), name="session_list"),
    path("session/<int:id>/", SessionDetailView.as_view(), name="session_detail"),
    path("", include(router.urls)),
    path("post/<int:id>", PostDetailView.as_view(), name="post_detail"),
    # ... get profile
    # ... show profile posts
]
