# accounts/urls.py

from django.urls import path
from .views import (
    register_view,
    logout_view,
    me_view,
    CustomTokenObtainPairView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/register/", register_view),
    path("auth/logout/", logout_view),
    path("auth/me/", me_view),

    path("token/", CustomTokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
]

