from rest_framework import serializers
from .models import Order, OrderItem, OrderItemTopping, OrderItemComponent
from menu.models import MenuItem, Topping
from rewards.models import SpinReward


class OrderTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "customer_name",
            "order_type",
            "estimated_time",
            "created_at",
        ]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used for creating individual order items within an order.

    """
    rewardId = serializers.IntegerField(
        required=False,
        write_only=True,
        allow_null=True,
    )
    toppings = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=MenuItem.objects.filter(category__name="Toppings"),
            required=False
        )

    class Meta:
        model = OrderItem
        fields = [
            'item',
            'toppings',
            'quantity',
            'components',
            'note',
            'rewardId',
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new order with nested order items.

    """
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'customer_name',
            'delivery_address',
            'customer_email',
            'phone_number',
            'order_type',
            'items'
        ]

    def create(self, validated_data):
        """
        Create an Order and its related OrderItems.
        If a user is authenticated, attach them to the order.
        """
        request = self.context.get('request')
        print(request.data)
        items_data = validated_data.pop('items')

        # Create order and attach authenticated user if available
        order = Order.objects.create(
            user=request.user if request and request.user.is_authenticated else None,
            **validated_data
        )

        for item_data in items_data:

            toppings = item_data.pop("toppings", [])

            reward_id = item_data.pop("rewardId", None)

            is_free = False

            if reward_id:

                reward = SpinReward.objects.get(
                    id=reward_id,
                    user=request.user,
                    status="redeemed",
                )

                if reward.reward_config.free_item != item_data["item"]:
                    raise serializers.ValidationError(
                        "Invalid reward item."
                    )

                is_free = True

                # Prevent the reward from being reused
                reward.status = "consumed"
                reward.save(update_fields=["status"])

            order_item = OrderItem.objects.create(
                order=order,
                is_free=is_free,
                **item_data,
            )

            order_item.toppings.set(toppings)
        return order


class ToppingReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "name", "price"]


# class OrderItemReadSerializer(serializers.ModelSerializer):
    # """
    # Serializer for reading/displaying order items, including calculated total price and resolved components.

    # """
    # item = serializers.StringRelatedField()
    # item_price = serializers.DecimalField(source='item.price', max_digits=10, decimal_places=2, read_only=True)
    # # toppings = serializers.StringRelatedField(many=True)
    # toppings = serializers.SerializerMethodField()
    # total_price = serializers.SerializerMethodField()
    # components = serializers.SerializerMethodField()

    # class Meta:
        # model = OrderItem
        # fields = [
            # 'item',
            # 'item_price',
            # 'quantity',
            # 'components',
            # 'toppings',
            # 'note',
            # 'total_price'
        # ]

    # def get_components(self, obj):
        # """
        # Convert component IDs into readable item names by querying MenuItem.
        # Example: {"Pizza Toppings": [10, 11]} -> {"Pizza Toppings": ["Mushrooms", "Olives"]}
        # """
        # result = {}
        # for category, item_ids in obj.components.items():
            # # Query MenuItems with matching IDs
            # menu_items = MenuItem.objects.filter(id__in=item_ids)
            # result[category] = [item.name for item in menu_items]
        # return result

    # def get_total_price(self, obj):
        # """
        # Return the calculated total price of the order item including
        # toppings and components.
        # """

        # return obj.get_total_price()

    # def get_toppings(self, obj):
        # """
        # Return a list of toppings for this order item, including their names
        # and prices.
        # """
        # result = []
        # for topping in obj.toppings.all():  # ✅ FIX: iterate through `.all()`
            # result.append({
                # "name": topping.name,
                # "price": topping.price
            # })
        # return result


class OrderItemToppingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemTopping
        fields = ['topping_id', 'quantity']


class OrderItemComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemComponent
        fields = ['category', 'item_id', 'quantity']


class OrderItemReadSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(source="item.id", read_only=True)
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_price = serializers.DecimalField(
        source="item.price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    # Use related_name from FK models
    toppings = serializers.SerializerMethodField()
    components = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item_id",
            "item_name",
            "item_price",
            "quantity",
            "components",
            "toppings",
            "is_free",
            "note",
            "total_price",
        ]

    def get_toppings(self, obj):
        # obj.toppings is the related manager from OrderItemTopping
        return [
            {
                "id": t.topping.id,
                "name": t.topping.name,
                "price": t.topping.price,
                "quantity": t.quantity
            }
            for t in obj.order_toppings.all()
        ]

    def get_components(self, obj):
        # obj.components is the related manager from OrderItemComponent
        return [
            {
                "category": c.category,
                "id": c.item.id,
                "name": c.item.name,
                "price": c.item.price,
                "quantity": c.quantity
            }
            for c in obj.order_components.all()
        ]


class OrderReadSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying order details including items, user name,
    and total amount.

    """
    items = OrderItemReadSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'payment_id',
            'tracking_token',
            'username',
            'customer_name',
            'order_type',
            'estimated_time',
            'delivery_address',
            'customer_email',
            'phone_number',
            'created_at',
            'scheduled_at',
            'status',
            'items',
            'coupon_code',
            'discount',
            'total_amount',
        ]

    def get_total_amount(self, obj):
        """Return the sum of all item totals in the order."""
        return obj.get_total_amount()

    def get_username(self, obj):
        """
        Return the full name of the user who placed the order,
        or their username, or 'Guest' if not logged in.
        """
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        if obj.customer_name:
            return obj.customer_name
        return "Guest"


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the status of an existing order.

    """
    class Meta:
        model = Order
        fields = ['status']


class PaymentStatusSerializer(serializers.Serializer):
    """
    Serializer for Mollie payment status check response
    """
    payment_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DictField()  # Mollie returns dict: {"currency": "EUR", "value": "10.00"}
    paid = serializers.BooleanField()
    order_id = serializers.IntegerField(allow_null=True)
    tracking_token = serializers.CharField(allow_null=True)

class OrderHistorySerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)

    username = serializers.CharField(source="user.username", read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "payment_id",
            "tracking_token",
            "username",
            "customer_name",
            "order_type",
            "estimated_time",
            "delivery_address",
            "customer_email",
            "phone_number",
            "created_at",
            "scheduled_at",
            "status",
            "items",
            "coupon_code",
            "discount",
            "total_amount",
        ]

    def get_total_amount(self, obj):
        return obj.get_total_amount()

