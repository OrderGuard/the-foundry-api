from rest_framework.routers import DefaultRouter
from .views import DeviceTokenViewSet

router = DefaultRouter()
router.register(r"device-tokens", DeviceTokenViewSet, basename="device-token")

urlpatterns = router.urls

