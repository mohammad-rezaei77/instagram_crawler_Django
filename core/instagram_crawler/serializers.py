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
    type = serializers.CharField()
    thumbnail_url = serializers.CharField()
    video_url = serializers.CharField()


class JsonToObj(serializers.Serializer):
    post_id = serializers.CharField()
    caption = serializers.CharField()
    likes = serializers.IntegerField()
    comments = serializers.IntegerField()
    reels = serializers.CharField()
    type = serializers.CharField()
    media = serializers.ListField(child=ImageSerializer())

    class Meta:
        fields = (
            "post_id",
            "caption",
            "likes",
            "comments",
            "reels",
            "type",
            "media",
        )


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)

    class Meta:
        fields = ("username",)
        
class PostURLSerializer(serializers.Serializer):
    post_url = serializers.URLField(required=True)
