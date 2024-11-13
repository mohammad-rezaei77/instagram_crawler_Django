import json
from collections import namedtuple

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Post, Session
from .paginations import DefaultPagination
from .serializers import (
    JsonToObj,
    PostSerializer,
    PostURLSerializer,
    SessionRegSerializer,
    SessionSerializer,
    UsernameSerializer,
)
from .tasks import fetch_profile_data, fetch_single_post_data


class CreateSessionView(generics.ListCreateAPIView):
    serializer_class = SessionRegSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


class SessionListCreateView(generics.ListCreateAPIView):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()
    serializer_class = PostSerializer


def customDecoder(studentDict):
    return namedtuple("X", studentDict.keys())(*studentDict.values())


class PostDetailView(APIView):
    pagination_class = DefaultPagination
    serializer_class = JsonToObj
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            queryset = Post.objects.filter(id=id).get()
            print(queryset)
            
            if queryset.post_data:
                x = json.dumps(queryset.post_data)
                obj = json.loads(x, object_hook=customDecoder)

                paginator = self.pagination_class()
                result_page = paginator.paginate_queryset(obj, request)
                
                serializer = self.serializer_class(result_page, many=True)
                
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response({"message": "No data found"}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response(
                "The entered profile does not exist", status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "message": f"An error occurred: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FetchPostView(APIView):
    serializer_class = UsernameSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UsernameSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            post = Post.objects.create(profile=username, user=request.user)
            fetch_profile_data.delay(post.id)

            return Response(
                {
                    "message": "Profile crawl request submitted, and the process has started.",
                    "post_id": post.id,
                },
                status=status.HTTP_201_CREATED,
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