from django.contrib import admin
from .models import DeviceToken


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'expo_push_token', 'created_at']
    search_fields = ['expo_push_token', 'user__email']

