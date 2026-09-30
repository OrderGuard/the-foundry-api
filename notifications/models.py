from django.db import models
# from django.contrib.auth.models import User
from django.conf import settings


class DeviceToken(models.Model):
    # user = models.ForeignKey(
        # User,
        # on_delete=models.CASCADE,
        # related_name="device_tokens",
        # null=True,
        # blank=True  # allow guest tokens
    # )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    expo_push_token = models.CharField(
        max_length=255,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'expo_push_token')
        verbose_name = "Device Token"
        verbose_name_plural = "Device Tokens"

    def __str__(self):
        return f"{self.user.username if self.user else 'Guest'} - {self.expo_push_token}"

