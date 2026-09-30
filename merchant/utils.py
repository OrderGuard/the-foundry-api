# merchant/utils/mollie_utils.py
from mollie.api.client import Client
from mollie.api.error import UnauthorizedError, Error
import requests
from decouple import config
from django.utils import timezone
from datetime import timedelta
import logging

from merchant.logging.logging_utils import mask_token, sanitize_payload

logger = logging.getLogger(__name__)


def refresh_mollie_token(merchant):
    """
    Refresh Mollie OAuth token for a merchant.
    Logs all important steps, masks sensitive data.
    """
    logger.info(f"[MOLLIE] 🔄 Refreshing token for merchant {merchant.id}")

    token_url = "https://api.mollie.com/oauth2/tokens"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": merchant.oauth_refresh_token,
        "client_id": config("MOLLIE_CLIENT_ID"),
        "client_secret": config("MOLLIE_CLIENT_SECRET"),
    }

    # Log sanitized request payload
    logger.info(f"[MOLLIE] 📡 Sending token refresh request: {sanitize_payload(data)}")

    try:
        response = requests.post(token_url, data=data)
    except requests.RequestException as e:
        logger.error(f"[MOLLIE] ❌ Token refresh HTTP error: {str(e)}")
        raise

    logger.info(f"[MOLLIE] 📥 Response status: {response.status_code}")

    try:
        token_data = response.json()
    except ValueError:
        logger.error("[MOLLIE] ❌ Failed to parse JSON from token response")
        raise Exception(f"Mollie refresh failed: non-JSON response {response.text}")

    if "access_token" in token_data:
        merchant.oauth_access_token = token_data["access_token"]

        # Only overwrite refresh token if provided
        if "refresh_token" in token_data:
            merchant.oauth_refresh_token = token_data["refresh_token"]

        # Store expiry time if provided
        if "expires_in" in token_data:
            merchant.token_expires_at = timezone.now() + timedelta(seconds=token_data["expires_in"])

        merchant.save()
        logger.info(
            f"[MOLLIE] ✅ Token refreshed | access={mask_token(merchant.oauth_access_token)}"
        )
        return merchant.oauth_access_token

    logger.error(f"[MOLLIE] ❌ Token refresh failed: {token_data}")
    raise Exception(f"Mollie refresh failed: {token_data}")


def ensure_valid_token(merchant):
    """
    Ensures that the merchant has a valid token.
    If expired or missing, automatically refreshes it.
    """
    if not merchant.token_expires_at or merchant.token_expires_at <= timezone.now():
        logger.info(f"[MOLLIE] ⏱ Token expired or missing for merchant {merchant.id}, refreshing...")
        refresh_mollie_token(merchant)
    else:
        logger.info(f"[MOLLIE] ✅ Token valid for merchant {merchant.id}")


def mollie_onboarding_status(merchant):
    """
    Fetch onboarding status from Mollie.
    Automatically refreshes token if unauthorized.
    """
    logger.info(f"[MOLLIE] 📊 Fetching onboarding status for merchant {merchant.id}")

    mollie_client = Client()
    mollie_client.set_access_token(merchant.oauth_access_token)

    try:
        onboarding = mollie_client.onboarding.get()
    except UnauthorizedError:
        logger.info(f"[MOLLIE] 🔄 UnauthorizedError, refreshing token for merchant {merchant.id}")
        new_token = refresh_mollie_token(merchant)
        mollie_client.set_access_token(new_token)
        onboarding = mollie_client.onboarding.get()
    except Error as e:
        logger.error(f"[MOLLIE] ❌ Mollie API error: {str(e)}")
        raise

    status = getattr(onboarding, "status", "unknown")
    logger.info(f"[MOLLIE] 📊 Onboarding status for merchant {merchant.id}: {status}")
    return status

