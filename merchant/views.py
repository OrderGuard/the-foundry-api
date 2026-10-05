import logging
from datetime import timedelta

import requests
from decouple import config
from django.shortcuts import redirect
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Merchant


logger = logging.getLogger(__name__)


MOLLIE_OAUTH_REDIRECT_URI = config("MOLLIE_OAUTH_REDIRECT_URI")
MOLLIE_CLIENT_ID = config("MOLLIE_CLIENT_ID")
MOLLIE_CLIENT_SECRET = config("MOLLIE_CLIENT_SECRET")


# ---------------------------------------------------------
# Connect merchant to Mollie
# ---------------------------------------------------------

def connect_mollie(request, merchant_id):

    # Make sure merchant exists
    try:
        Merchant.objects.get(id=merchant_id)
    except Merchant.DoesNotExist:
        return Response(
            {
                "error": "Merchant not found"
            },
            status=404,
        )

    url = (
        "https://www.mollie.com/oauth2/authorize"
        f"?client_id={MOLLIE_CLIENT_ID}"
        f"&redirect_uri={MOLLIE_OAUTH_REDIRECT_URI}"
        "&response_type=code"
        "&scope=organizations.read payments.write profiles.read onboarding.read"
        f"&state={merchant_id}"
    )

    logger.info(
        "[MOLLIE OAUTH] Starting OAuth for merchant %s",
        merchant_id,
    )

    return redirect(url)


# ---------------------------------------------------------
# Mollie OAuth callback
# ---------------------------------------------------------

@api_view(["GET"])
def mollie_callback(request):

    logger.info("[MOLLIE OAUTH] Callback received")

    # Don't log the authorization code itself
    logger.info(
        "[MOLLIE OAUTH] Query parameters received: %s",
        list(request.GET.keys()),
    )

    code = request.GET.get("code")
    merchant_id = request.GET.get("state")
    error = request.GET.get("error")

    # Mollie authorization error
    if error:
        logger.error(
            "[MOLLIE OAUTH] Authorization error: %s",
            error,
        )

        return Response(
            {
                "error": error,
                "error_description": request.GET.get(
                    "error_description"
                ),
            },
            status=400,
        )

    # Missing code
    if not code:
        return Response(
            {
                "error": "Missing authorization code"
            },
            status=400,
        )

    # Missing merchant ID
    if not merchant_id:
        return Response(
            {
                "error": "Missing merchant ID"
            },
            status=400,
        )

    # Find merchant
    try:
        merchant = Merchant.objects.get(id=merchant_id)
    except Merchant.DoesNotExist:
        return Response(
            {
                "error": "Merchant not found",
                "merchant_id": merchant_id,
            },
            status=404,
        )

    # -----------------------------------------------------
    # Exchange authorization code for tokens
    # -----------------------------------------------------

    token_url = "https://api.mollie.com/oauth2/tokens"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": MOLLIE_CLIENT_ID,
        "client_secret": MOLLIE_CLIENT_SECRET,
        "redirect_uri": MOLLIE_OAUTH_REDIRECT_URI,
    }

    try:
        response = requests.post(
            token_url,
            data=data,
            timeout=30,
        )
    except requests.RequestException as e:

        logger.exception(
            "[MOLLIE OAUTH] Token request failed"
        )

        return Response(
            {
                "error": "Could not connect to Mollie"
            },
            status=502,
        )

    logger.info(
        "[MOLLIE OAUTH] Token response status: %s",
        response.status_code,
    )

    try:
        token_data = response.json()
    except ValueError:

        logger.error(
            "[MOLLIE OAUTH] Mollie returned invalid JSON"
        )

        return Response(
            {
                "error": "Invalid response from Mollie"
            },
            status=502,
        )

    # -----------------------------------------------------
    # Check token response
    # -----------------------------------------------------

    if response.status_code != 200:
        logger.error(
            "[MOLLIE OAUTH] Token exchange failed"
        )

        return Response(
            {
                "error": "OAuth failed",
                "mollie_response": token_data,
            },
            status=400,
        )

    if "access_token" not in token_data:
        return Response(
            {
                "error": "OAuth failed",
                "mollie_response": token_data,
            },
            status=400,
        )

    # -----------------------------------------------------
    # Save OAuth tokens
    # -----------------------------------------------------

    merchant.oauth_access_token = token_data["access_token"]

    merchant.oauth_refresh_token = token_data.get(
        "refresh_token"
    )

    # -----------------------------------------------------
    # Save token expiration
    # -----------------------------------------------------

    expires_in = token_data.get("expires_in")

    if expires_in:
        merchant.token_expires_at = (
            timezone.now()
            + timedelta(seconds=int(expires_in))
        )

    # -----------------------------------------------------
    # Save Mollie mode
    # -----------------------------------------------------

    merchant.mollie_mode = (
        "test"
        if token_data["access_token"].startswith("test_")
        else "live"
    )

    merchant.save()

    logger.info(
        "[MOLLIE OAUTH] Merchant %s connected successfully",
        merchant.id,
    )

    return Response(
        {
            "message": "Mollie connected successfully",
            "merchant_id": merchant.id,
            "mollie_mode": merchant.mollie_mode,
            "token_expires_at": merchant.token_expires_at,
            "has_access_token": bool(
                merchant.oauth_access_token
            ),
            "has_refresh_token": bool(
                merchant.oauth_refresh_token
            ),
        }
    )

