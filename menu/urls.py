from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MenuItemViewSet, ToppingViewSet, MealViewSet, MenuViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'items', MenuItemViewSet)
router.register(r'toppings', ToppingViewSet)
router.register(r'meal', MealViewSet)
router.register(r'menu', MenuViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

