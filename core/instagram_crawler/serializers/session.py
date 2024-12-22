from rest_framework import serializers

from instagram_crawler.models import Session


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
