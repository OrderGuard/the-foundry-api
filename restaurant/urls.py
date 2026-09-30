# restaurants/urls.py
from django.urls import path
from .views import RestaurantStatusView

urlpatterns = [
    path("status/", RestaurantStatusView.as_view()),
]

