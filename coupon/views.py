from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone

from .models import Coupon
from order.models import Order


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def validate_coupon(request):
    code = request.data.get("code")

    if not code:
        return Response(
            {"valid": False, "message": "Coupon code required"},
            status=400
        )

    try:
        coupon = Coupon.objects.get(code__iexact=code, active=True)
    except Coupon.DoesNotExist:
        return Response(
            {"valid": False, "message": "Invalid or expired coupon"},
            status=400
        )

    now = timezone.now()
    if not (coupon.valid_from <= now <= coupon.valid_to):
        return Response(
            {"valid": False, "message": "Coupon not valid at this time"},
            status=400
        )

    return Response({
        "valid": True,
        "type": coupon.discount_type,
        "value": coupon.value,
        "min_order_amount": coupon.min_order_amount,
    })

