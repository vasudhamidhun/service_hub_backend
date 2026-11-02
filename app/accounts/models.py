
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        PROVIDER = "provider", "Service Provider"
        ADMIN = "admin", "Admin"

    full_name = models.CharField(max_length=150)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    email = models.EmailField(unique=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN

        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name or self.username

class ProviderProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    service_category=models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField(default=0)
    service_location = models.CharField(max_length=255, blank=True)
    profile_photo = models.ImageField(
        upload_to="provider_profiles/",
        blank=True,
        null=True,
    )
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    phone_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Provider Profile - {self.user.full_name}"