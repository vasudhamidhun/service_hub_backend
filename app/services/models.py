
from django.conf import settings
from django.db import models
from app.accounts.models import (User,ProviderProfile)

class ServiceRequest(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
        ("in_progress", "In Progress"),
    ("awaiting_completion", "Awaiting Provider Confirmation"),
        ("completed", "Completed"),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="service_requests",
    )

    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="received_requests",
    )

    problem_description = models.TextField()

    service_location = models.CharField(
        max_length=500
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Request #{self.id} - "
            f"{self.customer} to {self.provider.user.full_name}"
        )
