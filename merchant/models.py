from django.db import models


class Merchant(models.Model):

    name = models.CharField(
        max_length=255
    )

    mollie_mode = models.CharField(
        max_length=10,
        choices=[
            ("test", "Test"),
            ("live", "Live"),
        ],
        default="test",
    )

    mollie_organization_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    mollie_profile_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    oauth_access_token = models.TextField(
        null=True,
        blank=True,
    )

    oauth_refresh_token = models.TextField(
        null=True,
        blank=True,
    )

    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

