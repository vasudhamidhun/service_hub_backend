from django.db import models
from django.conf import settings


# class Notification(models.Model):

#     NOTIFICATION_TYPES = [
#         ("new_request", "New Service Request"),
#         ("request_accepted", "Request Accepted"),
#         ("request_rejected", "Request Rejected"),
#         ("request_cancelled", "Request Cancelled"),
#     ]

#     recipient = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="notifications"
#     )

#     title = models.CharField(max_length=255)

#     message = models.TextField()

#     notification_type = models.CharField(
#         max_length=50,
#         choices=NOTIFICATION_TYPES
#     )

#     service_request = models.ForeignKey(
#         "services.ServiceRequest",
#         on_delete=models.CASCADE,
#         related_name="notifications",
#         null=True,
#         blank=True
#     )

#     is_read = models.BooleanField(default=False)

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ["-created_at"]

#     def __str__(self):
#         return f"{self.title} - {self.recipient}"


class Notification(models.Model):

    NOTIFICATION_TYPES = [
        # Service request notifications
       # Service request notifications
        ("new_request", "New Service Request"),
        ("request_accepted", "Request Accepted"),
        ("request_rejected", "Request Rejected"),
        ("request_cancelled", "Request Cancelled"),
        ("completion_requested", "Completion Requested"),
        ("request_completed", "Request Completed"),

        # Complaint notifications
        ("new_complaint", "New Complaint"),
        ("explanation_requested", "Explanation Requested"),
        ("provider_responded", "Provider Responded"),
        ("complaint_updated", "Complaint Updated"),
        ("complaint_resolved", "Complaint Resolved"),
        ("complaint_rejected", "Complaint Rejected"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES
    )

    service_request = models.ForeignKey(
        "services.ServiceRequest",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )

    complaint = models.ForeignKey(
        "feedback.Complaint",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.recipient}"