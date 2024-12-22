from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram_crawler.models import Post, PostItem
from instagram_crawler.paginations import DefaultPagination
from instagram_crawler.serializers import (
    PostItemSerializer,
    PostSerializer,
    PostURLSerializer,
    UsernameSerializer,
)
from instagram_crawler.tasks import (
    fetch_page,
    fetch_single_post_data,
    get_and_validate_best_session,
    is_profile_private,
)


class FetchPageView(APIView):
    serializer_class = UsernameSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UsernameSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            
            client = get_and_validate_best_session()
            if not client:
                return Response(
                    {"error": "No valid session available. Please try again later."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            is_private = is_profile_private(client, username)
            if is_private is None:
                return Response(
                    {"error": f"Could not retrieve privacy status for {username}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            post = Post.objects.create(
                    profile=username,
                    is_private=is_private,
                    )
            fetch_page(post.id)
            print("fetch_page...")
            return Response(
                    {
                        "message": f"Profile crawl request for {username} was processed.",
                        "is_private": is_private,
                        "post_id": post.id
                    },
                    status=status.HTTP_200_OK,      
                )
        

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FetchSinglePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PostURLSerializer(data=request.data)

        if serializer.is_valid():
            post_url = serializer.validated_data["post_url"]

            data = fetch_single_post_data(post_url)

            return Response(
                {
                    "result": data,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostListAPIView(APIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        posts = Post.objects.all()
        serializer = self.serializer_class(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostDetailAPIView(APIView):
    def get(self, request, pk, *args, **kwargs):
        # پیدا کردن پست
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # گرفتن PostItem‌های مرتبط
        post_items = PostItem.objects.filter(post=post)

        # اعمال صفحه‌بندی
        paginator = DefaultPagination()
        paginated_items = paginator.paginate_queryset(post_items, request)

        # سریالایز کردن داده‌ها
        serializer = PostItemSerializer(paginated_items, many=True)
        return paginator.get_paginated_response(serializer.data)
