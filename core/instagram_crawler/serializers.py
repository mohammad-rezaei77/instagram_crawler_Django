from rest_framework import serializers

from .models import Post, Session


class SessionRegSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ("username", "password")


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            "id",
            "username",
            "session_data",
            "create_at",
            "is_block",
            "is_temp_block",
            "is_challenge",
            "number_of_use",
        ]


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "session", "profile", "loading_time", "create_at", "post_data"]


class ImageSerializer(serializers.Serializer):
    video_url = serializers.CharField()
    thumbnail_url = serializers.CharField()


class JsonToObj(serializers.Serializer):
    caption = serializers.CharField()
    likes = serializers.IntegerField()
    comments = serializers.IntegerField()
    imgs = serializers.ListField(child=ImageSerializer())
    reels = serializers.CharField()

    class Meta:
        fields = (
            "caption",
            "likes",
            "comments",
            "imgs",
            "reels",
        )
