
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Review
from .serializers import ReviewSerializer
from rest_framework.exceptions import PermissionDenied


# class CreateReviewView(generics.CreateAPIView):

#     serializer_class = ReviewSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return Review.objects.all()

#     def perform_create(self, serializer):

#         if self.request.user.role != "customer":
#             raise PermissionDenied(
#                 "Only customers can submit reviews."
#             )

#         serializer.save()


class CreateReviewView(generics.CreateAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):

        if request.user.role != "customer":
            raise PermissionDenied(
                "Only customers can submit reviews."
            )

        return super().create(request, *args, **kwargs)



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
