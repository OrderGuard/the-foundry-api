# accounts/models.py

from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20, blank=True)
    # Address fields
    house_number_or_name = models.CharField(max_length=100, blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    def get_full_address(self):
        return ", ".join(
            filter(None, [
                self.house_number_or_name,
                self.street_address,
                self.city,
                self.postal_code,
            ])
        )

