from rest_framework import serializers

from instagram_crawler.models import Post, PostItem


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    requested_posts = serializers.CharField(max_length=255)

    class Meta:
        fields = ("username","requested_posts")


class PostURLSerializer(serializers.Serializer):
    post_url = serializers.URLField(required=True)


class PostItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PostItem
        fields = ["id", "post", "content"]


class PostSerializer(serializers.ModelSerializer):
    # post_items = PostItemSerializer(many=True, read_only=True, source="postitem_set")

    class Meta:
        model = Post
        fields = [
            "id",
            "profile",
            "is_private",
            "loading_time",
            "create_at",
            # "post_items",
        ]
