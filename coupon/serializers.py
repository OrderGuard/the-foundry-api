

from rest_framework import serializers
from rest_framework.permissions import AllowAny

from coupon.models import Coupon

class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField()

    def validate(self, data):
        order = self.context["order"]

        try:
            coupon = Coupon.objects.get(code=data["code"], active=True)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code")

        if not coupon.is_valid(order.get_subtotal()):
            raise serializers.ValidationError("Coupon not applicable")

        data["coupon"] = coupon
        return data

    def save(self, order):
        coupon = self.validated_data["coupon"]
        subtotal = order.get_subtotal()

        if coupon.discount_percent:
            discount = subtotal * (coupon.discount_percent / 100)
        else:
            discount = coupon.discount_amount

        order.coupon = coupon
        order.discount_amount = discount
        order.save()

        coupon.used_count += 1
        coupon.save()

        return order

