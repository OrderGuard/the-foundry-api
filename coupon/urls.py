

from django.urls import path
# from .views import ApplyCouponAPIView, validate_coupon
from .views import validate_coupon

urlpatterns = [
    # path('apply-coupon/', ApplyCouponAPIView.as_view(), name='apply-coupon'),
    path("validate/", validate_coupon),
]

