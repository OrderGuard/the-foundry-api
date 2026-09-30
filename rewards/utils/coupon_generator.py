import uuid
from datetime import timedelta
from django.utils import timezone

from coupon.models import Coupon


def generate_coupon(user, reward):
    code = f"RW-{uuid.uuid4().hex[:8].upper()}"

    value = reward.value or 0

    discount_type = "percent" if reward.reward_type == "discount" else "fixed"

    coupon = Coupon.objects.create(
        code=code,
        discount_type=discount_type,
        value=value,
        valid_to=timezone.now() + timedelta(days=7),
        active=True
    )

    return coupon
