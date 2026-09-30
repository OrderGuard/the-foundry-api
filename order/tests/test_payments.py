import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.urls import reverse
from rest_framework.test import APIClient

from merchant.models import Merchant
from menu.models import MenuItem, Category


# -------------------------
# FIXTURES
# -------------------------

@pytest.fixture
def category(db):
    return Category.objects.create(name="Food")


@pytest.fixture
def menu_item(db, category):
    return MenuItem.objects.create(
        name="Burger",
        price=Decimal("5.00"),
        category=category
    )


@pytest.fixture
def api_client():
    return APIClient()


# -------------------------
# TEST MODE
# -------------------------

@pytest.mark.django_db
@patch("merchant.services.mollie_service.MollieService.create_payment")
def test_create_payment_test_mode(mock_create_payment, api_client, menu_item):

    Merchant.objects.create(
        name="kk83",
        mollie_mode="test",
        mollie_profile_id="prof_123",
        oauth_access_token="test_token"
    )

    # Mock Mollie response
    mock_create_payment.return_value = MagicMock(
        id="tr_test_123",
        checkout_url="https://checkout.test"
    )

    payload = {
        "order_type": "pickup",
        "items": [
            {"item": menu_item.id, "quantity": 1, "toppings": []}
        ]
    }

    response = api_client.post(
        reverse("create-payment"),
        payload,
        format="json"
    )

    assert response.status_code == 200
    assert response.data["payment_id"] == "tr_test_123"
    assert response.data["checkout_url"] == "https://checkout.test"

    # ✅ FIX: extract payload correctly
    sent_payload = mock_create_payment.call_args[0][0]
    assert sent_payload["testmode"] is True


# -------------------------
# LIVE MODE
# -------------------------

@pytest.mark.django_db
@patch("merchant.services.mollie_service.MollieService.create_payment")
def test_create_payment_live_mode(mock_create_payment, api_client, menu_item):

    Merchant.objects.create(
        name="kk83",
        mollie_mode="live",
        mollie_profile_id="prof_123",
        oauth_access_token="live_token"
    )

    # Mock Mollie response
    mock_create_payment.return_value = MagicMock(
        id="tr_live_456",
        checkout_url="https://checkout.live"
    )

    payload = {
        "order_type": "delivery",
        "distanceKm": 2,
        "items": [
            {"item": menu_item.id, "quantity": 2, "toppings": []}
        ]
    }

    response = api_client.post(
        reverse("create-payment"),
        payload,
        format="json"
    )

    assert response.status_code == 200
    assert response.data["payment_id"] == "tr_live_456"
    assert response.data["checkout_url"] == "https://checkout.live"

    # ✅ FIX: extract payload correctly
    sent_payload = mock_create_payment.call_args[0][0]
    assert sent_payload["testmode"] is False

