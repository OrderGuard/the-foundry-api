

from django.db import models
from django.utils import timezone
from django.conf import settings
# from order.models import Order


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("percent", "Percentage"),
        ("fixed", "Fixed amount"),
        ("free_delivery", "Free Delivery"),
        ("free_item", "Free Item"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="coupons"
    )

    code = models.CharField(max_length=50, unique=True)

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES
    )

    value = models.DecimalField(   # ✅ THIS IS THE KEY
        max_digits=6,
        decimal_places=2,
        help_text="Percentage (e.g. 10) or fixed amount (e.g. 5.00)"
    )

    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()

    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self, order_total=None):
        now = timezone.now()

        if not self.active:
            return False

        if self.valid_from > now:
            return False

        if self.valid_to < now:
            return False

        if self.usage_limit and self.used_count >= self.usage_limit:
            return False

        if order_total and order_total < self.min_order_amount:
            return False

        return True


class CouponUsage(models.Model):
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="usages"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coupon_usages"
    )

    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE
    )

    used_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['coupon', 'order'],
                name='unique_coupon_per_order'
            )
        ]

        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['coupon']),
            models.Index(fields=['used_at']),
        ]

    def __str__(self):
        return f"{self.user} used {self.coupon.code}"
