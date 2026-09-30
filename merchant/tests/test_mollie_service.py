from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
from merchant.models import Merchant
from merchant.services.mollie_service import MollieService

import logging

logger = logging.getLogger(__name__)


class TestMollieService(TestCase):

    def setUp(self):
        # ✅ Use objects.create (auto handles created_at, etc.)
        self.merchant = Merchant.objects.create(
            oauth_access_token="OLD_TOKEN",
            oauth_refresh_token="OLD_REFRESH",
            token_expires_at=timezone.now() - timedelta(minutes=1)
        )

    @patch("merchant.utils.requests.post")
    @patch("merchant.services.mollie_service.Client")
    def test_payment_with_token_refresh(self, mock_client_class, mock_post):

        logger.info("🚀 Starting test_payment_with_token_refresh")

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.set_access_token.return_value = None

        mock_client.payments.create.return_value = {
            "id": "tr_test_123",
            "status": "open"
        }

        logger.info("🧪 Mock client configured")

        mock_post.return_value.json.return_value = {
            "access_token": "NEW_TOKEN",
            "refresh_token": "NEW_REFRESH",
            "expires_in": 3600
        }

        logger.info("🔄 Mock token refresh configured")

        service = MollieService(self.merchant)

        payload = {
            "amount": {"currency": "EUR", "value": "10.00"},
            "description": "Test Payment",
            "redirectUrl": "https://example.com/thank-you",
            "webhookUrl": "https://example.com/webhook",
        }

        logger.info("📡 Calling MollieService.create_payment()")

        payment = service.create_payment(payload)

        logger.info(f"💳 Payment response: {payment}")

        self.merchant.refresh_from_db()

        logger.info(f"🔑 Access token: {self.merchant.oauth_access_token}")
        logger.info(f"🔄 Refresh token: {self.merchant.oauth_refresh_token}")

        logger.info("✅ Running assertions")

        self.assertEqual(self.merchant.oauth_access_token, "NEW_TOKEN")
        self.assertEqual(self.merchant.oauth_refresh_token, "NEW_REFRESH")

        self.assertEqual(payment["id"], "tr_test_123")
        self.assertEqual(payment["status"], "open")
