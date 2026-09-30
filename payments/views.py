# payments/views.py
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentIntentDetailView(APIView):
    def get(self, request, intent_id):
        try:
            payment_intent = stripe.PaymentIntent.retrieve(
                intent_id,
                expand=["charges"]
            )

            # Safely access charges
            charges = getattr(payment_intent, "charges", None)
            first_charge = charges.data[0] if charges and charges.data else None

            return Response({
                "customer_email": getattr(first_charge.billing_details, "email", None) if first_charge else None,
                "amount_total": getattr(payment_intent, "amount_received", 0),
                "payment_status": getattr(payment_intent, "status", "unknown")
            })
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MockPaymentIntentDetailView(APIView):
    """
    Mock version of PaymentIntent detail for frontend testing.
    """
    def get(self, request, intent_id):
        # Just return fake payment details for testing UI
        return Response({
            "customer_email": "test@example.com",
            "amount_total": 2999,  # amount in cents ($29.99)
            "payment_status": "succeeded"
        }, status=status.HTTP_200_OK)


