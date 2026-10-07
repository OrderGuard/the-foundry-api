

from django.db import models
from django.utils.safestring import mark_safe
from model_utils.managers import InheritanceManager
from django.utils import timezone


class Menu(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        now = timezone.localtime().time()
        return self.start_time <= now <= self.end_time

    @property
    def opening_time_display(self):
        return self.start_time.strftime("%-I:%M %p")

    @property
    def closing_time_display(self):
        return self.end_time.strftime("%-I:%M %p")


class Category(models.Model):

    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    name = models.CharField(max_length=50)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position']  # ✅ required for sortable inline admin

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='menu_images/',
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='items',
        default=1
    )
    position = models.PositiveIntegerField(default=0)
    toppings = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='topped_items',
        limit_choices_to={'category__name__icontains': 'toppings'}
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    available = models.BooleanField(default=True)
    objects = InheritanceManager()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class MealComponent(models.Model):
    PRICING_CHOICES = [
        ("included", "Included in meal price"),
        ("addon", "Add-on (adds price)")
    ]
    meal = models.ForeignKey('Meal', on_delete=models.CASCADE, related_name='components')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    required = models.BooleanField(default=True)
    max_selections = models.PositiveIntegerField(
        default=1,
        help_text="1 for single selection (radio), more than 1 for multiple selections (checkboxes)"
    )
    pricing_type = models.CharField(
        max_length=20,
        choices=PRICING_CHOICES,
        default="included"
    )

    def __str__(self):
        return f"{self.meal.name} - {self.category.name}"

    def category_options(self):
        items = self.category.items.all()
        if not items:
            return "No items"
        return mark_safe("<ul style='margin-left: 1em;'>" + "".join([f"<li>{i.name}</li>" for i in items]) + "</ul>")

    category_options.short_description = "Available Items"


class Meal(MenuItem):
    pass


class Topping(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    applicable_to = models.ManyToManyField(MenuItem, blank=True)

    def __str__(self):
        return self.name
