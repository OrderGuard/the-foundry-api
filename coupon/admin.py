

from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "min_order_amount",
        "active",
        "valid_from",
        "valid_to",
        "used_count",
    )
    list_filter = ("active",)
    search_fields = ("code",)

