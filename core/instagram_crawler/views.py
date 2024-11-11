import json
from collections import namedtuple

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Post, Session
from .paginations import DefaultPagination
from .serializers import (
    JsonToObj,
    PostSerializer,
    SessionRegSerializer,
    SessionSerializer,
)


class CreateSessionView(generics.ListCreateAPIView):
    serializer_class = SessionRegSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save()


class SessionListCreateView(generics.ListCreateAPIView):

    queryset = Session.objects.all()
    serializer_class = SessionSerializer


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    lookup_field = "id"


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


def customDecoder(studentDict):
    return namedtuple("X", studentDict.keys())(*studentDict.values())


class PostDetailView(APIView):
    pagination_class = DefaultPagination
    serializer_class = JsonToObj

    def get(self, request, id):
        try:
            queryset = Post.objects.filter(id=id).get()
            if queryset.json_posts:
                x = json.dumps(queryset.json_posts)
                obj = json.loads(x, object_hook=customDecoder)

                paginator = self.pagination_class()
                result_page = paginator.paginate_queryset(obj, request)
                serializer = self.serializer_class(result_page, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response("No data found", status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response(
                "The entered profile does not exist", status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                f"An error occurred: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
