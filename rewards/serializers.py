# apps/rewards/serializers.py

from rest_framework import serializers
from .models import UserReward


class UserRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReward
        fields = [
            'id',
            'reward',
            'reward_type',
            'free_item',
            'value',
            'coupon_code',
            'expires_at',
            'used',
            'created_at',
        ]

