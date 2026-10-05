from django.urls import path
from .views import connect_mollie, mollie_callback

urlpatterns = [
    path(
        "mollie/connect/<int:merchant_id>/",
        connect_mollie,
        name="connect-mollie",
    ),
    path(
        "mollie/callback/",
        mollie_callback,
        name="mollie-callback",
    ),
]

