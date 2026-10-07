from rest_framework import serializers
from .models import Category, MenuItem, Topping, Meal, MealComponent, Menu

class ToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topping
        fields = ['id', 'name', 'price']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class MealComponentSerializer(serializers.ModelSerializer):
    """
    Serializer for MealComponent model.

    Handles serialization and deserialization of individual components
    within a meal, including category and items selection.
    """

    category = serializers.StringRelatedField()
    items = serializers.SerializerMethodField()
    toppings = ToppingSerializer(many=True, source='topping_set', read_only=True)

    class Meta:
        model = MealComponent
        fields = ['id', 'category', 'max_selections', 'required', 'items', 'toppings']

    def get_items(self, obj):
        items = obj.category.items.filter(available=True)

        # ✅ Include price if category name contains "toppings" (case-insensitive)
        if "toppings" in obj.category.name.lower():
            return MenuItemSimpleWithPriceSerializer(items, many=True).data

        return MenuItemSimpleSerializer(items, many=True).data


class MenuItemToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price']


class MenuItemSerializer(serializers.ModelSerializer):
    """
    Get Menu Item
    """
    # category = serializers.PrimaryKeyRelatedField(
        # queryset=Category.objects.all()
    # )
    category = CategorySerializer(read_only=True)
    toppings = MenuItemToppingSerializer(many=True, read_only=True)
    # toppings = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)
    components = MealComponentSerializer(many=True, read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'image', 'category', 'price', 'available', 'created_at', 'toppings', 'components' ]

    def get_toppings(self, obj):
        toppings = obj.topping_set.all()
        return ToppingSerializer(toppings, many=True).data


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """
    Create Menu

    """
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    toppings = serializers.PrimaryKeyRelatedField(many=True, queryset=MenuItem.objects.all(), required=False)
    components = serializers.PrimaryKeyRelatedField(many=True, queryset=MealComponent.objects.all(), required=False)
    image = serializers.ImageField(required=False)

    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'image', 'category', 'price', 'available', 'toppings', 'components']

class MenuItemSimpleSerializer(serializers.ModelSerializer):
    # toppings = ToppingSerializer(many=True, source='topping_set', read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'name']


class MenuItemSimpleWithPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price']  # Includes price


class MealSerializer(serializers.ModelSerializer):
    components = MealComponentSerializer(many=True, read_only=True)
    # toppings = ToppingSerializer(many=True)

    class Meta:
        model = Meal
        fields = ['id', 'name', 'price', 'components']


class MenuSerializer(serializers.ModelSerializer):
    is_open = serializers.ReadOnlyField()
    opening_time_display = serializers.ReadOnlyField()
    closing_time_display = serializers.ReadOnlyField()

    class Meta:
        model = Menu
        fields = [
            "id",
            "name",
            "start_time",
            "end_time",
            "is_open",
            "opening_time_display",
            "closing_time_display",
        ]

