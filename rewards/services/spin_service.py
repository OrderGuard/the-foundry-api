# apps/rewards/services/spin_service.py

from datetime import timedelta
from django.utils import timezone

from rewards.models import UserPoints, SpinReward
from rewards.services.reward_selector import get_weighted_reward
from rewards.utils.coupon_generator import generate_coupon


def spin(user):
    points_obj, _ = UserPoints.objects.get_or_create(user=user)

    if points_obj.spins_available <= 0:
        raise Exception("No spins available")

    # consume spin
    points_obj.spins_available -= 1
    points_obj.save()

    reward = get_weighted_reward()

    coupon_code = None

    if reward.reward_type != 'none':
        coupon_code = generate_coupon(user, reward)

    expires_at = timezone.now() + timedelta(days=14)

    SpinReward.objects.create(
        user=user,
        reward=reward.name,
        coupon_code=coupon_code,
        expires_at=expires_at
    )

    return {
        "reward": reward.name,
        "type": reward.reward_type,
        "value": reward.value,
        "coupon_code": coupon_code,
    }

