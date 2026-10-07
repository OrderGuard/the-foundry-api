from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import DeviceToken
from .serializers import DeviceTokenSerializer


class DeviceTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceTokenSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DeviceToken.objects.none()

        return DeviceToken.objects.filter(
            user=self.request.user
        )

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]

        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        expo_token = request.data.get("expo_push_token")

        if not expo_token:
            return Response(
                {
                    "success": False,
                    "error": "expo_push_token is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        device_token, created = DeviceToken.objects.update_or_create(
            expo_push_token=expo_token,
            defaults={
                "user": (
                    request.user
                    if request.user.is_authenticated
                    else None
                ),
            },
        )

        return Response(
            {
                "success": True,
                "expo_push_token": device_token.expo_push_token,
                "authenticated": request.user.is_authenticated,
                "created": created,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )

