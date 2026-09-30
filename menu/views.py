from rest_framework import viewsets
from .models import Category, MenuItem, Topping, Meal, Menu
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    MenuItemCreateSerializer,
    ToppingSerializer,
    MealSerializer,
    MenuSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.prefetch_related('items')
    serializer_class = CategorySerializer


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing MenuItem objects.

    - Uses different serializers for read vs write operations.
    - Orders items by creation date (newest first).
    - Automatically handles standard actions: list, retrieve, create, update, delete.
    - Supports ?available=true for frontend filtering.
    """
    queryset = MenuItem.objects.all()
    # queryset = MenuItem.objects.filter(is_available=True).select_related("category")
    serializer_class = MenuItemSerializer
    ordering = ["category__position", "position"]


    def get_queryset(self):
        # queryset = MenuItem.objects.select_subclasses().all().order_by('-created_at')
        queryset = (
            MenuItem.objects
            .select_subclasses()
            .select_related("category")
            .order_by("category__position", "position")
        )

        # ✅ Log param to confirm
        available_param = self.request.query_params.get('available')
        print("🔍 available param:", available_param)

        if available_param == 'true':
            queryset = queryset.filter(available=True)
        elif available_param == 'false':
            queryset = queryset.filter(available=False)

        return queryset


    def get_serializer_class(self):
        """
        Returns the appropriate serializer class based on the action.

        - Uses MenuItemCreateSerializer for create/update/partial_update.
        - Uses MenuItemSerializer for all other actions (e.g., list, retrieve).
        """
        if self.action in ['create', 'update', 'partial_update']:
            return MenuItemCreateSerializer
        return MenuItemSerializer


class ToppingViewSet(viewsets.ModelViewSet):
    queryset = Topping.objects.all()
    serializer_class = ToppingSerializer


class MealViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Meal.objects.prefetch_related('components__category__items')
    serializer_class = MealSerializer


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    @action(
        detail=False,
        methods=["get"],
        url_path=r"(?P<menu_name>[^/.]+)"
    )
    def categories(self, request, menu_name=None):
        try:
            menu = Menu.objects.get(
                name__iexact=menu_name
            )
        except Menu.DoesNotExist:
            return Response(
                {"detail": "Menu not found."},
                status=404
            )

        categories = menu.categories.all()

        serializer = CategorySerializer(
            categories,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data)

