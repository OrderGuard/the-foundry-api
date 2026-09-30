from rest_framework import serializers
from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ["created_at"]

    def validate_people(self, value):
        if value > 20:
            raise serializers.ValidationError("Too many people")
        return value


