from django.contrib import admin
from django.utils.html import format_html

from adminsortable2.admin import (
    SortableAdminMixin,
    SortableInlineAdminMixin,
)

from .models import (
    Menu,
    Category,
    MenuItem,
    Meal,
    MealComponent,
)


# ============================================================
# MENU ITEM INLINE
# ============================================================

class MenuItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = MenuItem
    extra = 1

    fields = [
        "name",
        "price",
        "available",
        "position",
    ]

    readonly_fields = ["position"]


# ============================================================
# CATEGORY INLINE
# ============================================================

class CategoryInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Category
    extra = 1

    fields = [
        "name",
        "position",
    ]

    readonly_fields = ["position"]


# ============================================================
# MENU ADMIN
# ============================================================

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "start_time",
        "end_time",
        "open_status",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "start_time",
    )

    fields = (
        "name",
        "start_time",
        "end_time",
    )

    @admin.display(boolean=True, description="Open")
    def open_status(self, obj):
        return obj.is_open


# ============================================================
# MENU ITEM ADMIN
# ============================================================

@admin.register(MenuItem)
class MenuItemAdmin(SortableAdminMixin, admin.ModelAdmin):

    list_display = (
        "name",
        "image_preview",
        "category",
        "price",
        "available",
        "created_at",
    )

    list_filter = (
        "category",
        "available",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "image_preview",
    )

    filter_horizontal = (
        "toppings",
    )

    ordering = (
        "position",
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" '
                'style="object-fit: cover; border-radius: 6px;" />',
                obj.image.url,
            )

        return "No Image"

    image_preview.short_description = "Preview"


# ============================================================
# CATEGORY ADMIN
# ============================================================

@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):

    list_display = (
        "name",
        "menu",
        "position",
    )

    list_filter = (
        "menu",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "position",
    )

    inlines = [
        MenuItemInline,
    ]


# ============================================================
# MEAL COMPONENT INLINE
# ============================================================

class MealComponentInline(admin.TabularInline):

    model = MealComponent
    extra = 1

    autocomplete_fields = [
        "category",
    ]

    readonly_fields = [
        "category_options",
    ]

    fields = [
        "category",
        "category_options",
        "required",
        "max_selections",
        "pricing_type",
    ]


# ============================================================
# MEAL ADMIN
# ============================================================

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):

    list_display = [
        "name",
        "category",
        "price",
        "available",
    ]

    list_filter = [
        "category",
        "available",
    ]

    search_fields = [
        "name",
    ]

    inlines = [
        MealComponentInline,
    ]

    def get_form(self, request, obj=None, **kwargs):
        """
        Remove toppings from Meal admin.
        """
        form = super().get_form(request, obj, **kwargs)

        if "toppings" in form.base_fields:
            form.base_fields.pop("toppings")

        return form

