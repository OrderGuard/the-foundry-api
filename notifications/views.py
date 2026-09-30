from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import DeviceToken
from .serializers import DeviceTokenSerializer

class DeviceTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceTokenSerializer

    def get_queryset(self):
        # Only authenticated users can list their tokens
        if not self.request.user.is_authenticated:
            return DeviceToken.objects.none()
        return DeviceToken.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        expo_token = serializer.validated_data["expo_push_token"]

        device_token, created = DeviceToken.objects.update_or_create(
            expo_push_token=expo_token,
            defaults={
                "user": request.user if request.user.is_authenticated else None
            },
        )

        return Response(
            {
                "success": True,
                "expo_push_token": device_token.expo_push_token,
                "authenticated": request.user.is_authenticated,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
