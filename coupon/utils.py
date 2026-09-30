

from decimal import Decimal

def calculate_discount(coupon, subtotal: Decimal) -> Decimal:
    if subtotal < coupon.min_order_amount:
        return Decimal("0.00")

    if coupon.discount_type == "percent":
        return (subtotal * coupon.value / Decimal("100")).quantize(Decimal("0.01"))

    if coupon.discount_type == "fixed":
        return min(coupon.value, subtotal)

    return Decimal("0.00")

