from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from menu.models import MenuItem, Topping, Meal, MealComponent
from coupon.models import Coupon
from decimal import Decimal
import uuid
from merchant.models import Merchant


class Order(models.Model):
    ORDER_TYPES = [('pickup', 'Pickup'), ('delivery', 'Delivery')]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('new', 'New'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('preparing', 'Preparing'),
        ('delivering', 'Delivering'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_email = models.EmailField()
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    delivery_address = models.TextField(blank=True, null=True)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.75)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True, null=True)
    estimated_time = models.PositiveIntegerField(default=15, help_text="Estimated preparation time in minutes")
    payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tracking_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    # def get_total_amount(self):
        # return sum(item.get_total_price() for item in self.items.all())

    def get_subtotal(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_amount(self):
        subtotal = self.get_subtotal()

        total = (
            subtotal
            + self.service_fee
            + self.delivery_charge
            - self.discount
        )

        return max(total, Decimal("0.00"))

    def remove_coupon(self):
        self.coupon = None
        self.discount = 0
        self.save()

    def save(self, *args, **kwargs):
        """
        Override save() to detect order status changes.

        Sets a temporary instance attribute `_status_changed` to True
        when the order's status is updated compared to its previous value.

        This flag is used by post-save signals (e.g. email notifications)
        to ensure status-related actions are only triggered when the
        status actually changes, and not on every save() call.

        Notes:
        - `_status_changed` is NOT stored in the database.
        - On initial creation (no pk yet), `_status_changed` remains False.
        """

        self._status_changed = False

        if self.pk:
            old = Order.objects.get(pk=self.pk)
            self._status_changed = old.status != self.status

        # Set estimated_time BEFORE saving
        if not self.estimated_time or self.estimated_time == 15:
            if self.order_type == "pickup":
                self.estimated_time = 25
            elif self.order_type == "delivery":
                self.estimated_time = 45
            else:
                self.estimated_time = 15

        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    toppings = models.ManyToManyField(
        MenuItem,
        blank=True,
        related_name="topping_orders"
    )
    components = models.JSONField(default=dict, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note = models.TextField(blank=True, null=True)
    is_free = models.BooleanField(default=False)

    def get_total_price(self):
        if self.is_free:
            return Decimal("0.00")

        base_price = self.item.price

        toppings_total = sum(
            t.topping.price * t.quantity
            for t in self.order_toppings.all()
        )

        components_total = 0

        if isinstance(self.item, Meal):
            rules = {
                rule.category_id: rule
                for rule in self.item.components.all()
            }

            for component in self.order_components.all():
                rule = rules.get(component.category_id)

                if rule and rule.pricing_type == "addon":
                    components_total += component.item.price * component.quantity

        return (base_price + toppings_total + components_total) * self.quantity

    def save(self, *args, **kwargs):
        # auto-calculate total_price before saving
        super().save(*args, **kwargs)
        self.total_price = self.get_total_price()
        super().save(update_fields=["total_price"])


class OrderItemComponent(models.Model):
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="order_components"
    )
    category = models.CharField(max_length=255)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class OrderItemTopping(models.Model):
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="order_toppings"
    )
    topping = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
