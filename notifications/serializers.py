from rest_framework import serializers
from .models import DeviceToken

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "expo_push_token", "user", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

