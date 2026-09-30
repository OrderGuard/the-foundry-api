import pytest
from django.utils import timezone
from datetime import timedelta

from coupon.models import Coupon
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_coupon_is_valid():
    coupon = Coupon.objects.create(
        code="SAVE10",
        discount_type="percent",
        value=10,
        valid_to=timezone.now() + timedelta(days=1),
        active=True
    )

    assert coupon.is_valid() is True


@pytest.mark.django_db
def test_coupon_expired():
    coupon = Coupon.objects.create(
        code="OLD10",
        discount_type="percent",
        value=10,
        valid_to=timezone.now() - timedelta(days=1),
        active=True
    )

    assert coupon.is_valid() is False


@pytest.mark.django_db
def test_coupon_minimum_order():
    coupon = Coupon.objects.create(
        code="SAVE20",
        discount_type="fixed",
        value=20,
        min_order_amount=100,
        valid_to=timezone.now() + timedelta(days=1),
        active=True
    )

    assert coupon.is_valid(order_total=50) is False
    assert coupon.is_valid(order_total=150) is True


User = get_user_model()

@pytest.mark.django_db
def test_user_coupon():
    user = User.objects.create_user(
        username="mauro",
        password="test123"
    )

    coupon = Coupon.objects.create(
        code="PRIVATE10",
        user=user,
        discount_type="percent",
        value=10,
        valid_to=timezone.now() + timedelta(days=1),
        active=True
    )

    assert coupon.user == user

