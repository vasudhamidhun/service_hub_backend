from django.db.models import Q, F, Value,Count
from django.db.models.functions import Greatest
from django.contrib.postgres.search import TrigramSimilarity
from rest_framework import generics, permissions,status
from django.shortcuts import get_object_or_404
from django.db.models.functions import Lower, Trim
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from app.accounts.models import ProviderProfile
from .serializers import ProviderSearchSerializer,ServiceRequestSerializer,CustomerServiceRequestSerializer

from .models import ProviderProfile, ServiceRequest
from app.notifications.models import Notification
from django.shortcuts import get_object_or_404

from rest_framework.exceptions import PermissionDenied, ValidationError

import logging

logger = logging.getLogger(__name__)

class ProviderServiceRequestListView(generics.ListAPIView):

    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        if self.request.user.role != "provider":
            raise PermissionDenied(
                "Only providers can view received requests."
            )

        try:
            provider = self.request.user.provider_profile
        except ProviderProfile.DoesNotExist:
            raise PermissionDenied(
                "Provider profile not found."
            )

        queryset = (
            ServiceRequest.objects
            .filter(provider=provider)
            .select_related(
                "customer",
                "provider",
                "provider__user"
            )
            .order_by("-created_at")
        )

        request_status = self.request.query_params.get("status")

        if request_status:
            valid_statuses = [
                choice[0]
                for choice in ServiceRequest.STATUS_CHOICES
            ]

            if request_status not in valid_statuses:
                raise ValidationError({
                    "status": "Invalid request status."
                })

            queryset = queryset.filter(status=request_status)

        return queryset

class ServiceSearchView(generics.ListAPIView):
    serializer_class = ProviderSearchSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = ProviderProfile.objects.filter(
            verification_status="approved",
            user__is_active=True,
        ).select_related("user")

        query = self.request.query_params.get("q", "").strip()

        if not query:
            return queryset.none()

        search_words = query.lower().split()

        # Calculate similarity for category and location
        queryset = queryset.annotate(
            category_similarity=TrigramSimilarity(
                "service_category", query
            ),
            location_similarity=TrigramSimilarity(
                "service_location", query
            ),
        ).annotate(
            search_score=Greatest(
                F("category_similarity"),
                F("location_similarity"),
            )
        )

        # Include direct substring matches and fuzzy matches
        condition = Q(
            service_category__icontains=query
        ) | Q(
            service_location__icontains=query
        ) | Q(search_score__gte=0.25)

        # Also check individual words for multi-word queries
        for word in search_words:
            condition |= (
                Q(service_category__icontains=word)
                | Q(service_location__icontains=word)
            )

        return (
            queryset.filter(condition)
            .order_by("-search_score", "user__full_name")
            .distinct()
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_unique_service_categories(request):

    categories = (
        ProviderProfile.objects
        .filter(
            verification_status="approved",
            user__is_active=True,
        )
        .exclude(service_category__isnull=True)
        .exclude(service_category__exact="")
        .annotate(
            normalized_category=Lower(Trim("service_category"))
        )
        .values_list("normalized_category", flat=True)
        .distinct()
        .order_by("normalized_category")
    )

    return Response({
        "categories": list(categories)
    })



class SendServiceRequestView(generics.CreateAPIView):

    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):

        if getattr(request.user, "role", None) != "customer":
            return Response(
                {"error": "Only customers can send service requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        problem_description = request.data.get(
            "problem_description", ""
        ).strip()

        service_location = request.data.get(
            "service_location", ""
        ).strip()

        if not problem_description or not service_location:
            return Response(
                {
                    "error": "Problem description and service location are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        provider = get_object_or_404(
            ProviderProfile,
            id=self.kwargs["provider_id"],
            verification_status="approved",
            user__is_active=True,
        )

        if provider.user_id == request.user.id:
            return Response(
                {"error": "You cannot send a request to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_request = ServiceRequest.objects.filter(
            customer=request.user,
            provider=provider,
        ).exclude(
            status__in=["rejected", "completed"]
        ).exists()

        if active_request:
            return Response(
                {
                    "message": "An active request already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request = ServiceRequest.objects.create(
            customer=request.user,
            provider=provider,
            problem_description=problem_description,
            service_location=service_location,
            status="pending",
        )
        Notification.objects.create(
            recipient=provider.user,
            title="New Service Request",
            message=f"{request.user.full_name} has sent you a service request for {provider.service_category}.",
            notification_type="new_request",
            service_request=service_request,
        )
        print("Notification created:", Notification.id)

        return Response(
            {
                "message": "Service request sent successfully.",
                "request_id": service_request.id,
                "customer": request.user.full_name,
                "provider": provider.user.full_name,
                "problem_description": service_request.problem_description,
                "service_location": service_request.service_location,
                "status": service_request.status,
                "created_at": service_request.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class ServiceRequestView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_provider(self):
        return get_object_or_404(
            ProviderProfile,
            id=self.kwargs["provider_id"],
            verification_status="approved",
            user__is_active=True,
        )

    def get(self, request, *args, **kwargs):
        """Check whether an active request exists."""

        if request.user.role != "customer":
            return Response(
                {"error": "Only customers can access this request."},
                status=status.HTTP_403_FORBIDDEN,
            )

        provider = self.get_provider()

        active_request = ServiceRequest.objects.filter(
            customer=request.user,
            provider=provider,
        ).exclude(
            status__in=["rejected", "completed"]
        ).order_by("-created_at").first()

        return Response({
            "has_active_request": active_request is not None,
            "request_status": active_request.status if active_request else None,
        })

    def post(self, request, *args, **kwargs):

        if request.user.role != "customer":
            return Response(
                {"error": "Only customers can send service requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        provider = self.get_provider()

        if provider.user_id == request.user.id:
            return Response(
                {"error": "You cannot send a request to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        problem_description = request.data.get(
            "problem_description", ""
        ).strip()

        service_location = request.data.get(
            "service_location", ""
        ).strip()

        if not problem_description or not service_location:
            return Response(
                {
                    "error": "Problem description and service location are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_request = ServiceRequest.objects.filter(
            customer=request.user,
            provider=provider,
        ).exclude(
            status__in=["rejected", "completed"]
        ).exists()

        if active_request:
            return Response(
                {
                    "message": "An active request already exists.",
                    "has_active_request": True,
                },
                status=status.HTTP_200_OK,
            )

        service_request = ServiceRequest.objects.create(
            customer=request.user,
            provider=provider,
            problem_description=problem_description,
            service_location=service_location,
            status="pending",
        )

        Notification.objects.create(
                    recipient=provider.user,
                    title="New Service Request",
                    message=f"{request.user.full_name} has sent you a service request for {provider.service_category}.",
                    notification_type="new_request",
                    service_request=service_request,
                )

        return Response(
            {
                "message": "Service request sent successfully.",
                "request_id": service_request.id,
                "problem_description": service_request.problem_description,
                "service_location": service_request.service_location,
                "status": service_request.status,
                "has_active_request": True,
            },
            status=status.HTTP_201_CREATED,
        )

class CustomerServiceRequestListView(generics.ListAPIView):
    serializer_class = CustomerServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can view their service requests."
            )

        return (
            ServiceRequest.objects
            .filter(customer=self.request.user)
            .select_related("provider", "provider__user")
            .order_by("-created_at")
        )


class CustomerServiceRequestDetailView(generics.RetrieveAPIView):
    serializer_class = CustomerServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can view service request details."
            )

        return (
            ServiceRequest.objects
            .filter(customer=self.request.user)
            .select_related("provider", "provider__user")
        )




class CustomerCancelServiceRequestView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        # Only customers can cancel their requests
        if request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can cancel service requests."
            )

        service_request = get_object_or_404(
            ServiceRequest,
            pk=pk,
            customer=request.user
        )

        # Allow cancellation only for pending requests
        if service_request.status != "pending" and service_request.status != "accepted":
            return Response(
                {
                    "message": (
                        "Only pending and accepted requests can be cancelled."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        service_request.status = "cancelled"
        service_request.save(update_fields=["status", "updated_at"])

        serializer = CustomerServiceRequestSerializer(
            service_request,
            context={"request": request}
        )

        return Response(
            {
                "message": "Service request cancelled successfully.",
                "request": serializer.data
            },
            status=status.HTTP_200_OK
        )


# --------------------------------------PROVIDER

class ProviderServiceRequestListView(generics.ListAPIView):

    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != "provider":
            raise PermissionDenied("Only providers can access requests.")

        try:
            provider = self.request.user.provider_profile
        except ProviderProfile.DoesNotExist:
            raise PermissionDenied("Provider profile not found.")

        queryset = ServiceRequest.objects.filter(
            provider=provider
        ).select_related(
            "customer",
            "provider",
            "provider__user"
        ).order_by("-created_at")

        status_filter = self.request.query_params.get("status")

        if status_filter:
            valid_statuses = [
                "pending", "accepted", "rejected",
                "cancelled", "completed"
            ]

            if status_filter not in valid_statuses:
                raise ValidationError("Invalid status.")

            queryset = queryset.filter(status=status_filter)

        return queryset
    
class ProviderDashboardStatsView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        # Log dashboard access
        logger.info(
            "Provider dashboard accessed by user ID: %s",
            request.user.id
        )

        if request.user.role != "provider":
            logger.warning(
                "Unauthorized dashboard access attempt by user ID: %s",
                request.user.id
            )
            return Response(
                {"error": "Only providers can access this dashboard."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            provider = request.user.provider_profile
        except ProviderProfile.DoesNotExist:
            logger.warning(
                "Provider profile not found for user ID: %s",
                request.user.id
            )
            return Response(
                {"error": "Provider profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        stats = ServiceRequest.objects.filter(
            provider=provider
        ).aggregate(
            total_requests=Count("id"),
            pending_requests=Count(
                "id",
                filter=Q(status="pending")
            ),
            completed_requests=Count(
                "id",
                filter=Q(status="completed")
            )
        )

        logger.info(
            "Provider dashboard stats retrieved successfully for user ID: %s",
            request.user.id
        )

        return Response(stats)
    
class ProviderServiceRequestStatusUpdateView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk, action):

        user = request.user

        logger.info(
            "Provider request status update attempted. User ID: %s, Request ID: %s, Action: %s",
            user.id, pk, action
        )

        # 1. Verify provider role
        if user.role != "provider":
            logger.warning(
                "Non-provider attempted to update service request. User ID: %s",
                user.id
            )
            raise PermissionDenied(
                "Only providers can update service requests."
            )

        # 2. Get logged-in provider profile
        try:
            provider = user.provider_profile
        except ProviderProfile.DoesNotExist:
            logger.warning(
                "Provider profile not found during status update. User ID: %s",
                user.id
            )
            raise PermissionDenied(
                "Provider profile not found."
            )

        # 3. Define allowed status transitions
        status_actions = {
            "accept": {
                "current": "pending",
                "new": "accepted",
            },
            "reject": {
                "current": "pending",
                "new": "rejected",
            },
            "complete": {
                "current": "accepted",
                "new": "completed",
            },
        }

        if action not in status_actions:
            logger.warning(
                "Invalid action '%s' for request ID: %s",
                action, pk
            )
            return Response(
                {"error": "Invalid request action."},
                status=status.HTTP_400_BAD_REQUEST
            )

        action_details = status_actions[action]

        # 4. Get request belonging to this provider only
        service_request = get_object_or_404(
            ServiceRequest,
            pk=pk,
            provider=provider
        )

        # 5. Validate current status
        if service_request.status != action_details["current"]:
            logger.warning(
                "Invalid status transition. Request ID: %s, Current status: %s, Action: %s",
                pk, service_request.status, action
            )
            return Response(
                {
                    "error": (
                        f"Cannot {action} this request "
                        f"because its current status is "
                        f"{service_request.status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 6. Update status
        old_status = service_request.status
        service_request.status = action_details["new"]

        service_request.save(
            update_fields=["status", "updated_at"]
        )

        logger.info(
            "Service request status updated successfully. Request ID: %s, User ID: %s, Old status: %s, New status: %s",
            pk, user.id, old_status, service_request.status
        )

        # 7. Return updated request details
        serializer = ServiceRequestSerializer(
            service_request,
            context={"request": request}
        )

        return Response(
            {
                "message": f"Request {action}ed successfully."
                if action in ["accept", "reject"]
                else "Request completed successfully.",
                "request": serializer.data
            },
            status=status.HTTP_200_OK
        )


# view more

class ProviderServiceRequestDetailView(generics.RetrieveAPIView):

    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        logger.info(
            "Provider request details accessed. User ID: %s",
            user.id
        )

        if user.role != "provider":
            logger.warning(
                "Non-provider attempted to view request details. User ID: %s",
                user.id
            )
            raise PermissionDenied(
                "Only providers can view request details."
            )

        try:
            provider = user.provider_profile
        except ProviderProfile.DoesNotExist:
            logger.warning(
                "Provider profile not found while viewing request details. User ID: %s",
                user.id
            )
            raise PermissionDenied(
                "Provider profile not found."
            )

        queryset = (
            ServiceRequest.objects
            .filter(provider=provider)
            .select_related(
                "customer",
                "provider",
                "provider__user"
            )
        )

        logger.info(
            "Provider request detail queryset prepared. User ID: %s, Request count: %s",
            user.id, queryset.count()
        )

        return queryset





    