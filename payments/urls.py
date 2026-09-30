from django.urls import path
from .views import (
    PaymentIntentDetailView,
    MockPaymentIntentDetailView
)

urlpatterns = [
    path("payment-intent/<str:intent_id>/", PaymentIntentDetailView.as_view()),
    path("mock-session/<str:intent_id>/", MockPaymentIntentDetailView.as_view()),  # mock route
    # path('payment/create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    # path('payment/payment-intent/<str:payment_intent_id>/', RetrievePaymentIntentView.as_view(), name='retrieve-payment-intent'),
]

