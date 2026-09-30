# apps/rewards/models.py

from django.conf import settings
from django.db import models

# Coupon
from coupon.models import Coupon
# Reward Free Item
from menu.models import MenuItem
from django.core.exceptions import ValidationError


class UserPoints(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    spins_available = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user} - {self.points} pts / {self.spins_available} spins"


class RewardConfig(models.Model):
    REWARD_TYPES = [
        ('none', 'Try Again'),
        ('discount', 'Discount'),
        ('free_item', 'Free Item'),
    ]

    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    name = models.CharField(max_length=50)

    reward_type = models.CharField(
        max_length=20,
        choices=REWARD_TYPES
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES,
        null=True,
        blank=True
    )

    value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    free_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    weight = models.IntegerField(default=1)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.reward_type == "discount":
            if self.value is None:
                raise ValidationError(
                    "Discount reward requires a value."
                )

            if not self.discount_type:
                raise ValidationError(
                    "Discount reward requires a discount type."
                )

        if self.reward_type == "free_item":
            if not self.free_item:
                raise ValidationError(
                    "Free item reward requires a menu item."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SpinReward(models.Model):

    STATUS_CHOICES = [
        ("available", "Available"),
        ("redeemed", "Redeemed"),
        ("consumed", "Consumed"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    reward_config = models.ForeignKey(
        RewardConfig,
        on_delete=models.SET_NULL,
        null=True
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # used = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
    )



