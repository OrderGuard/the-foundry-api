import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from rewards.models import RewardConfig, UserPoints
from rewards.services.reward_selector import get_weighted_reward

User = get_user_model()

@pytest.mark.django_db
def test_wheel_config():
    client = APIClient()

    user = User.objects.create_user(
        username="testuser",
        password="password123"
    )

    client.force_authenticate(user=user)

    RewardConfig.objects.create(
        name="10% OFF",
        reward_type="discount",
        weight=1,
        is_active=True
    )

    res = client.get("/api/rewards/wheel/")

    assert res.status_code == 200
    assert "wheel" in res.data
    assert len(res.data["wheel"]) == 1


@pytest.mark.django_db
def test_spin_returns_index():
    client = APIClient()

    user = User.objects.create_user(
        username="testuser",
        password="password123"
    )

    client.force_authenticate(user=user)

    from rewards.models import UserPoints

    obj, _ = UserPoints.objects.get_or_create(user=user)
    obj.spins_available = 1
    obj.save()

    RewardConfig.objects.create(
        name="10% OFF",
        reward_type="discount",
        weight=1,
        is_active=True
    )

    res = client.post("/api/rewards/spin/")

    assert res.status_code == 200
    assert "index" in res.data
    assert isinstance(res.data["index"], int)


@pytest.mark.django_db
def test_reward_status():
    client = APIClient()

    user = User.objects.create_user(
        username="testuser",
        password="password123"
    )

    client.force_authenticate(user=user)

    res = client.get("/api/rewards/status/")

    assert res.status_code == 200
    assert "points" in res.data
    assert "spins_available" in res.data

