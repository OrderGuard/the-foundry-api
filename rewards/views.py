# apps/rewards/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rewards.services.spin_service import spin
from django.views.decorators.csrf import csrf_exempt
from rewards.models import UserPoints, RewardConfig, SpinReward
from rewards.services.reward_selector import get_weighted_reward
from rewards.utils.coupon_generator import generate_coupon

from datetime import timedelta
from django.utils import timezone

from django.db import transaction
from django.shortcuts import get_object_or_404


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def spin_wheel(request):
    user = request.user

    points_obj, _ = UserPoints.objects.get_or_create(
        user=user
    )

    if points_obj.spins_available <= 0:
        return Response({"detail": "No spins available"}, status=400)

    # ✅ consume spin
    points_obj.spins_available -= 1

    # ⭐ OPTIONAL BUT IMPORTANT: reduce points OR reset cycle
    # if your logic is: 50 points = 1 spin
    # you should NOT manually subtract points here IF already converted

    points_obj.save()

    # Reward
    # reward = get_weighted_reward()
    rewards = list(
        RewardConfig.objects
        .filter(is_active=True)
        .order_by('id')
    )

    reward = get_weighted_reward(rewards)

    reward_index = rewards.index(reward)
    # End Reward

    coupon = None
    expires_at = timezone.now() + timedelta(days=14)

    # if reward.reward_type == "discount":
    if reward.reward_type in ["discount", "free_item"]:
        coupon = generate_coupon(user, reward)

    SpinReward.objects.create(
        user=user,
        reward_config=reward,
        coupon=coupon,
        expires_at=expires_at
    )

    return Response({
        "reward": reward.name,
        "type": reward.reward_type,
        "value": reward.value,
        "free_item": (
            reward.free_item.name
            if reward.free_item else None
        ),
        "coupon": coupon.code if coupon else None,
        "expires_at": expires_at,
        "spins_available": points_obj.spins_available,
        "points": points_obj.points,
        "index": reward_index,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reward_status(request):
    user = request.user

    obj, _ = UserPoints.objects.get_or_create(user=user)

    return Response({
        "points": obj.points,
        "spins_available": obj.spins_available,
        "can_spin": obj.spins_available > 0
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reward_history(request):
    rewards = SpinReward.objects.filter(
        user=request.user
    ).order_by('-created_at')

    data = [
        {
            "id": reward.id,
            "reward": (
                reward.reward_config.name
                if reward.reward_config
                else "Deleted Reward"
            ),
            "type": (
                reward.reward_config.reward_type
                if reward.reward_config
                else None
            ),
            "free_item": (
                {
                    "id": reward.reward_config.free_item.id,
                    "name": reward.reward_config.free_item.name,
                }
                if reward.reward_config and reward.reward_config.free_item
                else None
            ),
            "coupon": (
                reward.coupon.code
                if reward.coupon else None
            ),
            "status": reward.status,
            "expires_at": reward.expires_at,
            "created_at": reward.created_at,
        }
        for reward in rewards
    ]

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wheel_config(request):
    rewards = RewardConfig.objects.filter(
        is_active=True
    ).order_by('id')

    wheel = [
        {
            "id": r.id,
            "option": r.name,
            "weight": r.weight,
            "type": r.reward_type,
        }
        for r in rewards
    ]

    return Response({
        "wheel": wheel
    })


from django.shortcuts import get_object_or_404
from django.utils import timezone


@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def redeem_reward(request, reward_id):
    reward = get_object_or_404(
        SpinReward,
        id=reward_id,
        user=request.user
    )

    if reward.status != "available":
        return Response(
            {
                "detail": f"Reward cannot be redeemed. Current status: {reward.status}"
            },
            status=400
        )

    if reward.expires_at < timezone.now():
        reward.status = "expired"
        reward.save(update_fields=["status"])

        return Response(
            {"detail": "Reward expired."},
            status=400
        )

    if reward.reward_config.reward_type != "free_item":
        return Response(
            {"detail": "This reward cannot be redeemed."},
            status=400
        )

    reward.status = "redeemed"
    reward.save(update_fields=["status"])

    item = reward.reward_config.free_item

    return Response({
        "message": "Reward redeemed.",
        "reward_id": reward.id,
        "status": reward.status,
        "free_item": {
            "id": item.id,
            "name": item.name,
            "price": str(0),
        }
    })


@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unredeem_reward(request, reward_id):
    reward = get_object_or_404(
        SpinReward,
        id=reward_id,
        user=request.user,
    )

    if reward.status != "redeemed":
        return Response(
            {
                "detail": f"Reward cannot be unredeemed. Current status: {reward.status}"
            },
            status=400,
        )

    reward.status = "available"
    reward.save(update_fields=["status"])

    return Response({
        "message": "Reward restored.",
        "status": reward.status,
    })
