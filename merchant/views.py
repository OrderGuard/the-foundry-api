import logging
from datetime import timedelta
from urllib.parse import urlencode

import requests
from decouple import config
from django.shortcuts import redirect
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Merchant


logger = logging.getLogger(__name__)


# =========================================================
# Mollie configuration
# =========================================================

MOLLIE_OAUTH_REDIRECT_URI = config(
    "MOLLIE_OAUTH_REDIRECT_URI"
)

MOLLIE_CLIENT_ID = config(
    "MOLLIE_CLIENT_ID"
)

MOLLIE_CLIENT_SECRET = config(
    "MOLLIE_CLIENT_SECRET"
)

MOLLIE_API_URL = "https://api.mollie.com"


# =========================================================
# Connect merchant to Mollie
# =========================================================

def connect_mollie(request, merchant_id):

    # -----------------------------------------------------
    # Check merchant exists
    # -----------------------------------------------------

    try:
        merchant = Merchant.objects.get(
            id=merchant_id
        )

    except Merchant.DoesNotExist:

        return Response(
            {
                "error": "Merchant not found"
            },
            status=404,
        )

    # -----------------------------------------------------
    # OAuth parameters
    # -----------------------------------------------------

    params = {
        "client_id": MOLLIE_CLIENT_ID,
        "redirect_uri": MOLLIE_OAUTH_REDIRECT_URI,
        "response_type": "code",

        # Mollie permissions
        "scope": (
            "organizations.read "
            "payments.read "
            "payments.write "
            "profiles.read "
            "onboarding.read"
        ),

        # IMPORTANT:
        # Ideally this should be a random CSRF state.
        # We are using merchant ID here to match your
        # existing implementation.
        "state": str(merchant.id),
    }

    # -----------------------------------------------------
    # Build Mollie OAuth URL
    # -----------------------------------------------------

    authorization_url = (
        "https://www.mollie.com/oauth2/authorize?"
        + urlencode(params)
    )

    logger.info(
        "[MOLLIE OAUTH] Starting OAuth for merchant %s",
        merchant.id,
    )

    return redirect(authorization_url)


# =========================================================
# Mollie OAuth callback
# =========================================================

@api_view(["GET"])
def mollie_callback(request):

    logger.info(
        "[MOLLIE OAUTH] Callback received"
    )

    # Do NOT log authorization code or tokens
    logger.info(
        "[MOLLIE OAUTH] Query parameters received: %s",
        list(request.GET.keys()),
    )

    # -----------------------------------------------------
    # Get callback parameters
    # -----------------------------------------------------

    code = request.GET.get("code")

    merchant_id = request.GET.get("state")

    error = request.GET.get("error")

    error_description = request.GET.get(
        "error_description"
    )

    # =====================================================
    # Mollie authorization error
    # =====================================================

    if error:

        logger.error(
            "[MOLLIE OAUTH] Authorization error: %s",
            error,
        )

        return Response(
            {
                "error": error,
                "error_description": error_description,
            },
            status=400,
        )

    # =====================================================
    # Validate authorization code
    # =====================================================

    if not code:

        logger.error(
            "[MOLLIE OAUTH] Missing authorization code"
        )

        return Response(
            {
                "error": "Missing authorization code"
            },
            status=400,
        )

    # =====================================================
    # Validate merchant ID
    # =====================================================

    if not merchant_id:

        logger.error(
            "[MOLLIE OAUTH] Missing merchant ID"
        )

        return Response(
            {
                "error": "Missing merchant ID"
            },
            status=400,
        )

    # =====================================================
    # Find merchant
    # =====================================================

    try:

        merchant = Merchant.objects.get(
            id=merchant_id
        )

    except Merchant.DoesNotExist:

        logger.error(
            "[MOLLIE OAUTH] Merchant %s not found",
            merchant_id,
        )

        return Response(
            {
                "error": "Merchant not found",
                "merchant_id": merchant_id,
            },
            status=404,
        )

    # =====================================================
    # Exchange authorization code for tokens
    # =====================================================

    token_url = (
        f"{MOLLIE_API_URL}/oauth2/tokens"
    )

    token_data_request = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": MOLLIE_CLIENT_ID,
        "client_secret": MOLLIE_CLIENT_SECRET,
        "redirect_uri": MOLLIE_OAUTH_REDIRECT_URI,
    }

    try:

        token_response = requests.post(
            token_url,
            data=token_data_request,
            headers={
                "Accept": "application/json",
            },
            timeout=30,
        )

    except requests.RequestException:

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
        token_response.status_code,
    )

    # -----------------------------------------------------
    # Parse token response
    # -----------------------------------------------------

    try:

        token_data = token_response.json()

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

    # =====================================================
    # Check token response
    # =====================================================

    if token_response.status_code != 200:

        logger.error(
            "[MOLLIE OAUTH] Token exchange failed: %s",
            token_response.status_code,
        )

        return Response(
            {
                "error": "OAuth failed",
                "mollie_response": token_data,
            },
            status=400,
        )

    # =====================================================
    # Check access token
    # =====================================================

    access_token = token_data.get(
        "access_token"
    )

    if not access_token:

        logger.error(
            "[MOLLIE OAUTH] Access token missing"
        )

        return Response(
            {
                "error": "OAuth failed",
                "mollie_response": token_data,
            },
            status=400,
        )

    # =====================================================
    # Prepare authenticated Mollie API headers
    # =====================================================

    mollie_headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Accept": "application/json",
    }

    # =====================================================
    # Get current Mollie organization
    # =====================================================

    organization_url = (
        f"{MOLLIE_API_URL}/v2/organizations/me"
    )

    try:

        organization_response = requests.get(
            organization_url,
            headers=mollie_headers,
            timeout=30,
        )

    except requests.RequestException:

        logger.exception(
            "[MOLLIE OAUTH] Organization request failed"
        )

        return Response(
            {
                "error": (
                    "Could not retrieve Mollie "
                    "organization"
                )
            },
            status=502,
        )

    logger.info(
        "[MOLLIE OAUTH] Organization response status: %s",
        organization_response.status_code,
    )

    # -----------------------------------------------------
    # Parse organization response
    # -----------------------------------------------------

    try:

        organization_data = (
            organization_response.json()
        )

    except ValueError:

        logger.error(
            "[MOLLIE OAUTH] Invalid organization response"
        )

        return Response(
            {
                "error": (
                    "Invalid organization response "
                    "from Mollie"
                )
            },
            status=502,
        )

    # =====================================================
    # Check organization response
    # =====================================================

    if organization_response.status_code != 200:

        logger.error(
            "[MOLLIE OAUTH] Could not retrieve organization"
        )

        return Response(
            {
                "error": (
                    "Could not retrieve Mollie "
                    "organization"
                ),
                "mollie_response": organization_data,
            },
            status=400,
        )

    # =====================================================
    # Get organization ID
    # =====================================================

    mollie_organization_id = (
        organization_data.get("id")
    )

    if not mollie_organization_id:

        logger.error(
            "[MOLLIE OAUTH] Organization ID missing"
        )

        return Response(
            {
                "error": (
                    "Mollie organization ID not found"
                )
            },
            status=400,
        )

    logger.info(
        "[MOLLIE OAUTH] Organization %s retrieved",
        mollie_organization_id,
    )

    # =====================================================
    # Get Mollie profiles
    # =====================================================

    profiles_url = (
        f"{MOLLIE_API_URL}/v2/profiles"
    )

    try:

        profiles_response = requests.get(
            profiles_url,
            headers=mollie_headers,
            params={
                "limit": 50,
            },
            timeout=30,
        )

    except requests.RequestException:

        logger.exception(
            "[MOLLIE OAUTH] Profiles request failed"
        )

        return Response(
            {
                "error": (
                    "Could not retrieve Mollie profiles"
                )
            },
            status=502,
        )

    logger.info(
        "[MOLLIE OAUTH] Profiles response status: %s",
        profiles_response.status_code,
    )

    # -----------------------------------------------------
    # Parse profiles response
    # -----------------------------------------------------

    try:

        profiles_data = profiles_response.json()

    except ValueError:

        logger.error(
            "[MOLLIE OAUTH] Invalid profiles response"
        )

        return Response(
            {
                "error": (
                    "Invalid profiles response "
                    "from Mollie"
                )
            },
            status=502,
        )

    # =====================================================
    # Check profiles response
    # =====================================================

    if profiles_response.status_code != 200:

        logger.error(
            "[MOLLIE OAUTH] Could not retrieve profiles"
        )

        return Response(
            {
                "error": (
                    "Could not retrieve Mollie profiles"
                ),
                "mollie_response": profiles_data,
            },
            status=400,
        )

    # =====================================================
    # Extract profiles
    # =====================================================

    profiles = (
        profiles_data
        .get("_embedded", {})
        .get("profiles", [])
    )

    if not profiles:

        logger.error(
            "[MOLLIE OAUTH] No Mollie profiles found"
        )

        return Response(
            {
                "error": "No Mollie profile found"
            },
            status=400,
        )

    # =====================================================
    # Select profile
    # =====================================================

    # For now we use the first profile.
    #
    # If your merchants can have multiple Mollie
    # profiles, you should later add logic to select
    # the correct one.

    mollie_profile_id = profiles[0].get("id")

    if not mollie_profile_id:

        logger.error(
            "[MOLLIE OAUTH] Profile ID missing"
        )

        return Response(
            {
                "error": (
                    "Mollie profile ID not found"
                )
            },
            status=400,
        )

    logger.info(
        "[MOLLIE OAUTH] Profile %s retrieved",
        mollie_profile_id,
    )

    # =====================================================
    # Save OAuth tokens
    # =====================================================

    merchant.oauth_access_token = access_token

    merchant.oauth_refresh_token = (
        token_data.get("refresh_token")
    )

    # =====================================================
    # Save organization/profile IDs
    # =====================================================

    merchant.mollie_organization_id = (
        mollie_organization_id
    )

    merchant.mollie_profile_id = (
        mollie_profile_id
    )

    # =====================================================
    # Save token expiration
    # =====================================================

    expires_in = token_data.get(
        "expires_in"
    )

    if expires_in:

        merchant.token_expires_at = (
            timezone.now()
            + timedelta(
                seconds=int(expires_in)
            )
        )

    # =====================================================
    # Determine Mollie mode
    # =====================================================

    # IMPORTANT:
    # Do not rely on the access token prefix as the
    # primary way of determining mode.
    #
    # We use the selected profile's mode instead.

    profile_mode = profiles[0].get("mode")

    if profile_mode in ["test", "live"]:

        merchant.mollie_mode = profile_mode

    else:

        merchant.mollie_mode = "test"

    # =====================================================
    # Save merchant
    # =====================================================

    merchant.save()

    logger.info(
        "[MOLLIE OAUTH] Merchant %s connected successfully",
        merchant.id,
    )

    # =====================================================
    # Return response
    # =====================================================

    return Response(
        {
            "message": (
                "Mollie connected successfully"
            ),

            "merchant_id": merchant.id,

            "mollie_organization_id": (
                merchant.mollie_organization_id
            ),

            "mollie_profile_id": (
                merchant.mollie_profile_id
            ),

            "mollie_mode": (
                merchant.mollie_mode
            ),

            "token_expires_at": (
                merchant.token_expires_at
            ),

            "has_access_token": bool(
                merchant.oauth_access_token
            ),

            "has_refresh_token": bool(
                merchant.oauth_refresh_token
            ),
        }
    )

