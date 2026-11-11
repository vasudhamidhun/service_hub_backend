from django.db import models
from app.accounts.models import User, ProviderProfile
from app.services.models import ServiceRequest


class Review(models.Model):

    SENTIMENT_CHOICES = [
        ("positive", "Positive"),
        ("neutral", "Neutral"),
        ("negative", "Negative"),
    ]

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

    sentiment = models.CharField(
        max_length=10,
        choices=SENTIMENT_CHOICES,
        null=True,
        blank=True
    )

    sentiment_confidence = models.FloatField(
        null=True,
        blank=True
    )

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
    provider_response = models.TextField(blank=True)

    provider_responded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    response_deadline = models.DateTimeField(
        null=True,
        blank=True
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_complaints"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"Complaint #{self.id} - "
            f"{self.customer.full_name} - {self.category}"
        )



class ComplaintHistory(models.Model):

    EVENT_CHOICES = [
        ("submitted", "Complaint Submitted"),
        ("provider_notified", "Provider Notified"),
        ("provider_responded", "Provider Responded"),
        ("admin_review_started", "Admin Review Started"),
        ("status_changed", "Status Changed"),
        ("warning_issued", "Warning Issued"),
        ("response_deadline_missed", "Response Deadline Missed"),
        ("provider_suspended", "Provider Suspended"),
        ("provider_reinstated", "Provider Reinstated"),
        ("resolved", "Complaint Resolved"),
        ("rejected", "Complaint Rejected"),
    ]

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="history"
    )

    event_type = models.CharField(
        max_length=30,
        choices=EVENT_CHOICES
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaint_activities"
    )

    old_status = models.CharField(
        max_length=30,
        blank=True
    )

    new_status = models.CharField(
        max_length=30,
        blank=True
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"Complaint #{self.complaint_id} - "
            f"{self.event_type}"
        ) 

class ProviderAction(models.Model):

    ACTION_CHOICES = [
        ("warning", "Warning"),
        ("suspend", "Suspend"),
        ("reinstate", "Reinstate"),
        
    ]

    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admin_actions"
    )

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="provider_actions"
    )

    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )

    reason = models.TextField()

    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="provider_actions_taken"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.provider} - "
            f"{self.action_type}"
        )