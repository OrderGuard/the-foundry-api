from decimal import Decimal
import json
import pytest
from unittest.mock import patch

from order.views import calculate_delivery_fee
from merchant.models import Merchant


def test_delivery_fee_below_4km():
    assert calculate_delivery_fee(3.9) == Decimal("3.50")


def test_delivery_fee_at_4km():
    assert calculate_delivery_fee(4.0) == Decimal("4.00")


def test_delivery_fee_between_4_and_6_5km():
    assert calculate_delivery_fee(5.5) == Decimal("4.00")


def test_delivery_fee_at_6_5km():
    assert calculate_delivery_fee(6.5) == Decimal("4.50")


def test_delivery_fee_over_6_5km():
    assert calculate_delivery_fee(7.0) == Decimal("4.50")


# @pytest.mark.django_db
# @patch("order.views.MollieService")
# def test_delivery_order_rejected_over_8km(mock_payment, client):
    # Merchant.objects.create(name="kk83")

    # payload = {
        # "order_type": "delivery",
        # "distance_km": 8.5,
    # }

    # response = client.post(
        # "/api/order/create-payment/",
        # data=json.dumps(payload),
        # content_type="application/json"
    # )

    # assert response.status_code == 400
    # mock_payment.assert_not_called()

