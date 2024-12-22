from django.urls import path

from instagram_crawler.views import (
    CreateSessionAPIView,
    # CreateSessionView,
    FetchPageView,
    FetchSinglePostView,
    PostDetailAPIView,
    PostListAPIView,
    ResolveChallengeAPIView,
    SessionDetailView,
    SessionListCreateView,
)

urlpatterns = [
    path("create-session/", CreateSessionAPIView.as_view(), name="create-session"),
    path(
        "resolve-session-challenge/",
        ResolveChallengeAPIView.as_view(),
        name="resolve-challenge",
    ),
    path("list-session/", SessionListCreateView.as_view(), name="session_list"),
    path(
        "detail-session/<int:id>/", SessionDetailView.as_view(), name="session_detail"
    ),
    path("fetch-page/", FetchPageView.as_view(), name="fetches_page"),
    path("fetch-post/", FetchSinglePostView.as_view(), name="fetch-post"),
    
    path('posts/', PostListAPIView.as_view(), name='post-list'),
    path('posts/<int:pk>/', PostDetailAPIView.as_view(), name='post-detail'),
]
