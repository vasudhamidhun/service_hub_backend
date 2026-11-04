from django.db import models
from app.accounts.models import User, ProviderProfile
from app.services.models import ServiceRequest


class Review(models.Model):

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="given_reviews"
    )

    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="received_reviews"
    )

    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="review"
    )

    rating = models.PositiveSmallIntegerField()

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Review by {self.customer.full_name} "
            f"for {self.provider.user.full_name}"
        )


class Complaint(models.Model):

    CATEGORY_CHOICES = [
        ("service", "Service Related"),
        ("provider", "Provider Related"),
        ("platform", "Platform Related"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("awaiting_response", "Awaiting Response"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
        ("closed", "Closed"),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="complaints"
    )

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints"
    )

    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints"
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    subject = models.CharField(max_length=255)

    description = models.TextField()

    evidence = models.ImageField(
        upload_to="complaint_evidence/",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )

    admin_notes = models.TextField(blank=True)

    resolution = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Complaint #{self.id} - "
            f"{self.customer.full_name} - {self.category}"
        )
