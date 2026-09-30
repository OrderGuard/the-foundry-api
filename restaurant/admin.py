from django.contrib import admin
from .models import Restaurant

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_open')
    list_editable = ('is_open',)
    list_filter = ('is_open',)

