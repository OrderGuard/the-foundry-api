# newsletter/admin.py

from django.contrib import admin
from .models import NewsletterSubscriber

admin.site.register(NewsletterSubscriber)

