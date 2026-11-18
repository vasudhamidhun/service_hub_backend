
from rest_framework import generics, permissions,status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Review,Complaint,ComplaintHistory
from .serializers import ( ReviewSerializer,ComplaintSerializer,
                          AdminComplaintSerializer,
                          ProviderComplaintSerializer,
                          ProviderActionSerializer,
                          ProviderComplaintResponseSerializer)
from rest_framework.response import Response
from app.accounts.models import ProviderProfile
from app.AI_features.services.sentiment import analyze_sentiment
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from app.notifications.services import create_notification
from django.db.models import Q
from app.notifications.services import create_notification

User = get_user_model()
def is_admin(user):
    return (
        user.role == "admin"
        or user.is_superuser
    )
class CreateReviewView(generics.CreateAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):

        if request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can submit reviews."
            )

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):

        comment = serializer.validated_data.get("comment", "")

        if comment and comment.strip():
            result = analyze_sentiment(comment)

            serializer.save(
                sentiment=result["sentiment"],
                sentiment_confidence=result["confidence"]
            )
        else:
            serializer.save(
                sentiment=None,
                sentiment_confidence=None
            )

class UpdateReviewView(generics.UpdateAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    http_method_names = ["patch", "head", "options"]

    def get_queryset(self):

        if self.request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can update reviews."
            )

        return Review.objects.filter(
            customer=self.request.user
        )

    def perform_update(self, serializer):

        instance = serializer.instance

        # Run sentiment analysis only when the comment changes
        if "comment" in serializer.validated_data:

            comment = serializer.validated_data["comment"]

            if comment != instance.comment:

                if comment and comment.strip():
                    result = analyze_sentiment(comment)

                    serializer.save(
                        sentiment=result["sentiment"],
                        sentiment_confidence=result["confidence"]
                    )
                else:
                    serializer.save(
                        sentiment=None,
                        sentiment_confidence=None
                    )
                return

        # No comment change: retain the existing sentiment
        serializer.save()

# to view review submitted by customer themself
class MyReviewsView(generics.ListAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        if self.request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can view their submitted reviews."
            )

        return Review.objects.filter(
            customer=self.request.user
        ).select_related(
            "customer",
            "provider__user",
            "service_request"
        ).order_by("-created_at")

# This view is used by customers or public visitors to 
# see reviews of a particular provider.
# No login required.
# Anyone can view that provider's reviews.
# Provider ID is passed through the URL.
# Useful on the customer-facing Provider Details page.
class ProviderReviewsView(generics.ListAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):

        return Review.objects.filter(
            provider_id=self.kwargs["provider_id"],
            service_request__status="completed"
        ).select_related(
            "customer",
            "provider__user",
            "service_request"
        ).order_by("-created_at")

# This view is used by a logged-in provider to see 
# their own reviews.
class MyProviderReviewsView(generics.ListAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        if self.request.user.role != "provider":
            raise PermissionDenied(
                "Only providers can view their received reviews."
            )

        try:
            provider = ProviderProfile.objects.get(
                user=self.request.user
            )
        except ProviderProfile.DoesNotExist:
            return Review.objects.none()

        return Review.objects.filter(
            provider=provider,
            service_request__status="completed"
        ).select_related(
            "customer",
            "provider__user",
            "service_request"
        ).order_by("-created_at")

#-------------------------------------------------compplaint
#  customer raise complaint

class CreateComplaintView(generics.CreateAPIView):

    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser
    ]

    def create(self, request, *args, **kwargs):

        if request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can submit complaints."
            )

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):

        service_request = serializer.validated_data.get("service_request")

        provider = None

        if service_request:
            provider = service_request.provider

        complaint = serializer.save(
            customer=self.request.user,
            provider=provider
        )

        admins = User.objects.filter(role="admin").distinct()

        for admin in admins:
            transaction.on_commit(
                lambda admin=admin: create_notification(
                    recipient=admin,
                    title="New Complaint Received",
                    message=(
                        f"{self.request.user.full_name} "
                        "has submitted a new complaint."
                    ),
                    notification_type="new_complaint",
                    complaint=complaint
                )
            )

            complaint = serializer.save(
                customer=self.request.user
            )

            admins = User.objects.filter(
                role="admin"
            ).distinct()
            print("Admin count:", admins.count())
            for admin in admins.distinct():
                print(
                    admin.id,
                    admin.email,
                    admin.role,
                    admin.is_superuser
                )
                
                transaction.on_commit(
                    lambda admin=admin: create_notification(
                        recipient=admin,
                        title="New Complaint Received",
                        message=(
                            f"{self.request.user.full_name} "
                            "has submitted a new complaint."
                        ),
                        notification_type="new_complaint",
                        complaint=complaint
                    )
                )


# admin view the complaints
class AdminComplaintListView(generics.ListAPIView):

    serializer_class = AdminComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        if (
            self.request.user.role != "admin"
            and not self.request.user.is_superuser
        ):
            raise PermissionDenied(
                "Only admins can view complaints."
            )

        queryset = Complaint.objects.select_related(
            "customer",
            "provider__user",
            "service_request"
        ).order_by("-created_at")

        # Optional status filter
        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        # Optional category filter
        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(category=category)

        return queryset


# view for display complaint by customer
class MyComplaintsView(generics.ListAPIView):

    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        if self.request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can view their complaints."
            )

        return Complaint.objects.filter(
            customer=self.request.user
        ).select_related(
            "customer",
            "provider__user",
            "service_request"
        ).prefetch_related(
            "history"
        ).order_by("-created_at")

# custoemr can view compliant in detail
class ComplaintDetailView(generics.RetrieveAPIView):

    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        if self.request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can view complaint details."
            )

        return Complaint.objects.filter(
            customer=self.request.user
        ).select_related(
            "customer",
            "provider__user",
            "service_request"
        ).prefetch_related(
            "history"
        )



class ProviderComplaintResponseView(generics.GenericAPIView):

    serializer_class = ProviderComplaintResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        if self.request.user.role != "provider":
            raise PermissionDenied(
                "Only providers can respond to complaints."
            )

        try:
            provider = ProviderProfile.objects.get(
                user=self.request.user
            )
        except ProviderProfile.DoesNotExist:
            return Complaint.objects.none()

        return Complaint.objects.filter(
            provider=provider
        )

    def post(self, request, *args, **kwargs):

        complaint = self.get_object()

        # Provider can respond only when a response is requested
        if complaint.status != "awaiting_response":
            raise PermissionDenied(
                "This complaint is not awaiting a provider response."
            )

        # Check response deadline
        if (
            complaint.response_deadline
            and timezone.now() > complaint.response_deadline
        ):
            raise PermissionDenied(
                "The response deadline has passed."
            )

        # Validate provider response
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response_text = serializer.validated_data[
            "provider_response"
        ]

        old_status = complaint.status

        with transaction.atomic():

            complaint.provider_response = response_text
            complaint.provider_responded_at = timezone.now()

            # Move complaint to admin review
            complaint.status = "under_review"

            complaint.save(
                update_fields=[
                    "provider_response",
                    "provider_responded_at",
                    "status",
                    "updated_at"
                ]
            )

            # Record activity in complaint history
            ComplaintHistory.objects.create(
                complaint=complaint,
                event_type="provider_responded",
                updated_by=request.user,
                old_status=old_status,
                new_status=complaint.status,
                remarks="Provider submitted a response."
            )

            # Notify customer that provider has responded
            transaction.on_commit(
                lambda: create_notification(
                    recipient=complaint.customer,
                    title="Provider Responded to Your Complaint",
                    message=(
                        f"The provider has submitted a response "
                        f"for your complaint #{complaint.id}. "
                        "You can view the complaint details."
                    ),
                    notification_type="provider_responded",
                    complaint=complaint
                )
            )
            # Notify admins that the provider has responded
            admins = User.objects.filter(role="admin").distinct()

            for admin in admins:
                transaction.on_commit(
                    lambda admin=admin: create_notification(
                        recipient=admin,
                        title="Provider Response Received",
                        message=(
                            f"The provider has submitted an explanation "
                            f"for complaint #{complaint.id}: "
                            f"{complaint.subject}."
                        ),
                        notification_type="provider_responded",
                        complaint=complaint
                    )
                )

            return Response(
                        {
                            "message": "Your response has been submitted successfully.",
                            "complaint_id": complaint.id,
                            "status": complaint.status,
                            "provider_response": complaint.provider_response,
                            "provider_responded_at": complaint.provider_responded_at
                        },
                        status=200
                    )

class MyProviderComplaintsView(generics.ListAPIView):

    serializer_class = ProviderComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        if self.request.user.role != "provider":
            raise PermissionDenied(
                "Only providers can view their complaints."
            )

        try:
            provider = ProviderProfile.objects.get(
                user=self.request.user
            )
        except ProviderProfile.DoesNotExist:
            return Complaint.objects.none()

        return Complaint.objects.filter(
            provider=provider
        ).select_related(
            "customer",
            "provider__user",
            "service_request"
        ).order_by("-created_at")



# admin can update Complaint
class AdminComplaintDetailView(
    generics.RetrieveUpdateAPIView
):

    serializer_class = AdminComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):

        if not is_admin(self.request.user):
            raise PermissionDenied(
                "Only admins can access complaint details."
            )

        return Complaint.objects.select_related(
            "customer",
            "provider__user",
            "service_request",
            "reviewed_by"
        ).prefetch_related(
            "history__updated_by",
            "provider_actions__provider__user",
            "provider_actions__performed_by"
        )

    def perform_update(self, serializer):

        complaint = self.get_object()
        old_status = complaint.status

        new_status = serializer.validated_data.get(
            "status",
            old_status
        )

        admin_notes = serializer.validated_data.get(
            "admin_notes",
            complaint.admin_notes
        )

        resolution = serializer.validated_data.get(
            "resolution",
            complaint.resolution
        )

        if new_status in ["resolved", "rejected"]:
            if not resolution.strip():
                raise ValidationError({
                    "resolution":
                    "Please provide a resolution or explanation before closing the complaint."
                })

        with transaction.atomic():

            updated_complaint = serializer.save(
                reviewed_by=self.request.user,
                reviewed_at=timezone.now()
            )

            if new_status != old_status:

                if new_status == "resolved":
                    event_type = "resolved"

                elif new_status == "rejected":
                    event_type = "rejected"

                else:
                    event_type = "status_changed"

                ComplaintHistory.objects.create(
                    complaint=updated_complaint,
                    event_type=event_type,
                    updated_by=self.request.user,
                    old_status=old_status,
                    new_status=new_status,
                    remarks="Complaint status updated by admin."
                )
            if new_status != old_status:

                    notification_type = None
                    title = None
                    message = None

                    if new_status == "resolved":
                        notification_type = "complaint_resolved"
                        title = "Complaint Resolved"
                        message = (
                            f"Your complaint #{updated_complaint.id} "
                            "has been resolved by the admin."
                        )

                    elif new_status == "rejected":
                        notification_type = "complaint_rejected"
                        title = "Complaint Rejected"
                        message = (
                            f"Your complaint #{updated_complaint.id} "
                            "has been rejected by the admin."
                        )

                    else:
                        notification_type = "complaint_updated"
                        title = "Complaint Status Updated"
                        message = (
                            f"Your complaint #{updated_complaint.id} "
                            f"status has been updated to {new_status}."
                        )

                    transaction.on_commit(
                        lambda: create_notification(
                            recipient=updated_complaint.customer,
                                title=title,
                                message=message,
                                notification_type=notification_type,
                                complaint=updated_complaint
                            )
                        )
                # Notify provider when admin requests an explanation
            if (
                    new_status == "awaiting_response"
                    and updated_complaint.provider
                ):

                    provider_user = updated_complaint.provider.user

                    transaction.on_commit(
                        lambda: create_notification(
                            recipient=provider_user,
                            title="Complaint Explanation Required",
                            message=(
                                f"Admin has requested an explanation "
                                f"for complaint #{updated_complaint.id}: "
                                f"{updated_complaint.subject}. "
                                "Please review the complaint and submit your response."
                            ),
                            notification_type="explanation_requested",
                            complaint=updated_complaint
                        )
                    )

            elif admin_notes != complaint.admin_notes:
                ComplaintHistory.objects.create(
                    complaint=updated_complaint,
                    event_type="status_changed",
                    updated_by=self.request.user,
                    old_status=old_status,
                    new_status=old_status,
                    remarks="Admin updated the internal complaint notes."
                )

class AdminProviderActionView(generics.CreateAPIView):

    serializer_class = ProviderActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):

        if not is_admin(request.user):
            raise PermissionDenied(
                "Only admins can perform provider actions."
            )

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):

        provider = serializer.validated_data.get("provider")
        complaint = serializer.validated_data.get("complaint")
        action_type = serializer.validated_data["action_type"]
        reason = serializer.validated_data["reason"].strip()

        if provider is None:
            raise ValidationError({
                "provider": "A provider must be selected."
            })

        if not reason:
            raise ValidationError({
                "reason": "Please provide a valid reason."
            })

        if complaint and complaint.provider_id != provider.id:
            raise ValidationError({
                "complaint":
                "This complaint does not belong to the selected provider."
            })

        if action_type == "suspend" and provider.is_suspended:
            raise ValidationError({
                "detail": "This provider is already suspended."
            })

        if action_type == "reinstate" and not provider.is_suspended:
            raise ValidationError({
                "detail": "This provider is not currently suspended."
            })

        with transaction.atomic():

            if action_type == "suspend":

                provider.is_suspended = True
                provider.suspension_reason = reason
                provider.suspended_at = timezone.now()

                provider.save(
                    update_fields=[
                        "is_suspended",
                        "suspension_reason",
                        "suspended_at"
                    ]
                )

                event_type = "provider_suspended"

            elif action_type == "reinstate":

                provider.is_suspended = False
                provider.suspension_reason = ""
                provider.suspended_at = None

                provider.save(
                    update_fields=[
                        "is_suspended",
                        "suspension_reason",
                        "suspended_at"
                    ]
                )

                event_type = "provider_reinstated"

            else:
                event_type = "warning_issued"

            action = serializer.save(
                performed_by=self.request.user
            )

            if complaint:

                ComplaintHistory.objects.create(
                    complaint=complaint,
                    event_type=event_type,
                    updated_by=self.request.user,
                    old_status=complaint.status,
                    new_status=complaint.status,
                    remarks=reason
                )




