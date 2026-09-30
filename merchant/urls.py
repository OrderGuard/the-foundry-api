from django.urls import path
from .views import connect_mollie, mollie_callback

urlpatterns = [
    path("connect/<int:merchant_id>/", connect_mollie),
    path("callback/", mollie_callback),
]

