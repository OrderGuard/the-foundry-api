from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    OrderViewSet,
    mollie_webhook,
    create_payment,
    check_payment,
    OrderStatusSummaryView,
    track_order,
    my_orders,
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('mollie/webhook/', mollie_webhook, name='mollie-webhook'),
    path('create-payment/', create_payment, name='create-payment'),
    path('check-payment/<str:payment_id>/', check_payment, name='check-payment'),
    path('status-summary/', OrderStatusSummaryView.as_view()),
    path("track/<uuid:token>/", track_order),
    path("my/", my_orders, name="my-orders"),
]


