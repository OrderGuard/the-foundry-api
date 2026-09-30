import requests
from decouple import config
from django.shortcuts import redirect

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Merchant

# BASE_URL = config("BASE_URL")  # dynamic base URL
MOLLIE_OAUTH_REDIRECT_URI = config("MOLLIE_OAUTH_REDIRECT_URI")
MOLLIE_CLIENT_ID = config("MOLLIE_CLIENT_ID")
MOLLIE_CLIENT_SECRET = config("MOLLIE_CLIENT_SECRET")

# Connect merchant to Mollie
def connect_mollie(request, merchant_id):
    url = (
        "https://www.mollie.com/oauth2/authorize"
        f"?client_id={MOLLIE_CLIENT_ID}"
        f"&redirect_uri={MOLLIE_OAUTH_REDIRECT_URI}"
        "&response_type=code"
        "&scope=organizations.read payments.write profiles.read onboarding.read"
        f"&state={merchant_id}"
    )
    return redirect(url)


# Mollie redirects here after merchant approves
@api_view(["GET"])
def mollie_callback(request):
    code = request.GET.get("code")
    merchant_id = request.GET.get("state")

    token_url = "https://api.mollie.com/oauth2/tokens"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": MOLLIE_CLIENT_ID,
        "client_secret": MOLLIE_CLIENT_SECRET,
        "redirect_uri": MOLLIE_OAUTH_REDIRECT_URI,
    }

    response = requests.post(token_url, data=data)
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
    token_data = response.json()
    if "access_token" not in token_data:
        return Response({
            "error": "OAuth failed",
            "mollie_response": token_data
        }, status=400)

    merchant = Merchant.objects.get(id=merchant_id)
    merchant.oauth_access_token = token_data["access_token"]
    merchant.oauth_refresh_token = token_data.get("refresh_token")

    # Check if test or live
    merchant.mollie_mode = (
        "test" if token_data["access_token"].startswith("test_") else "live"
    )

    merchant.save()

    return Response({"message": "Mollie connected successfully"})
