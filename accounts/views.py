# accounts/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    MeSerializer,
)


# ✅ Register
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response({"message": "User created successfully"})


# ✅ Login
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ✅ Logout (client-side token removal, but keep endpoint)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    return Response({"message": "Logged out successfully"})


# ✅ /me
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me_view(request):

    if request.method == "GET":
        serializer = MeSerializer(request.user)
        return Response(serializer.data)

    elif request.method == "PATCH":
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
