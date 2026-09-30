# accounts/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models import Profile

from order.models import Order
from order.serializers import OrderReadSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# ✅ Login (JWT + user + latest order)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # data["user"] = {
            # "id": user.id,
            # "username": user.username,
            # "email": user.email,
            # "full_name": user.get_full_name(),
        # }
        data["user"] = MeSerializer(user).data

        return data


class MeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    contact_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    # address fields
    house_number_or_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    street_address = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    city = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    postal_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    # computed full address
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "contact_number",
            "house_number_or_name",
            "street_address",
            "city",
            "postal_code",
            "full_address",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_full_address(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile:
            return None
        return profile.get_full_address()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        profile = Profile.objects.filter(user=instance).first()

        if profile:
            data["contact_number"] = profile.contact_number
            data["house_number_or_name"] = profile.house_number_or_name
            data["street_address"] = profile.street_address
            data["city"] = profile.city
            data["postal_code"] = profile.postal_code
        else:
            data["contact_number"] = None

        return data

    def update(self, instance, validated_data):
        contact_number = validated_data.pop("contact_number", None)
        house_number_or_name = validated_data.pop("house_number_or_name", None)
        street_address = validated_data.pop("street_address", None)
        city = validated_data.pop("city", None)
        postal_code = validated_data.pop("postal_code", None)

        # update user fields
        for attr in ["username", "email", "first_name", "last_name"]:
            setattr(instance, attr, validated_data.get(attr, getattr(instance, attr)))

        instance.save()

        profile, _ = Profile.objects.get_or_create(user=instance)

        # Contact Number
        if contact_number is not None:
            profile.contact_number = contact_number

        # Address
        if house_number_or_name is not None:
            profile.house_number_or_name = house_number_or_name

        if street_address is not None:
            profile.street_address = street_address

        if city is not None:
            profile.city = city

        if postal_code is not None:
            profile.postal_code = postal_code

        profile.save()

        return instance
