
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .services import otp_service

from .serializers import (
    CustomerRegisterSerializer,
    ProviderRegisterSerializer,
    CustomerLoginSerializer,
    ProviderLoginSerializer,
    AdminLoginSerializer,
    ProviderProfileSerializer,
    ProviderVerificationSerializer,
    ProviderSendOTPSerializer,
    ProviderVerifyOTPSerializer
)

from .models import ProviderProfile

class CustomerRegisterView(generics.CreateAPIView):
    serializer_class = CustomerRegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProviderRegisterView(generics.CreateAPIView):
    serializer_class = ProviderRegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomerLoginView(TokenObtainPairView):
    serializer_class = CustomerLoginSerializer
    permission_classes = [permissions.AllowAny]


class ProviderLoginView(TokenObtainPairView):
    serializer_class = ProviderLoginSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        print("ACTIVE SERIALIZER:", serializer.__class__)
        print("SERIALIZER FIELDS:", list(serializer.fields.keys()))
        return serializer

class AdminLoginView(TokenObtainPairView):
    serializer_class = AdminLoginSerializer
    permission_classes = [permissions.AllowAny]



class ProviderCreation_SendOTPView(generics.GenericAPIView):
    serializer_class = ProviderSendOTPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        if user.role != "provider":
            return Response(
                {"detail": "Only service providers can request OTP verification."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if ProviderProfile.objects.filter(user=user).exists():
            return Response(
                {"detail": "Your provider profile already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile_data = serializer.validated_data
        phone = profile_data["phone"]

        otp = otp_service.generate_otp(
            user_id=user.id,
            phone=phone,
            profile_data=profile_data,
        )
        otp_service.send_otp_email(user.email, otp)

        return Response(
    {
        "detail": "OTP sent to your registered email address."
    },
    status=status.HTTP_200_OK,
)

    


class ProviderVerifyOTPView(generics.GenericAPIView):
    serializer_class = ProviderVerifyOTPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        if user.role != "provider":
            return Response(
                {"detail": "Only service providers can verify a phone number."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if ProviderProfile.objects.filter(user=user).exists():
            return Response(
                {"detail": "Your provider profile already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]

        if not otp_service.verify_otp(user.id, otp):
            return Response(
                {"detail": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pending_data = otp_service.get_pending_profile(user.id)

        if not pending_data:
            return Response(
                {"detail": "No pending profile found. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile_data = pending_data["profile_data"]

        profile = ProviderProfile.objects.create(
    user=user,
    phone=pending_data["phone"],
    bio=profile_data.get("bio", ""),
    experience_years=profile_data.get("experience_years", 0),
    service_location=profile_data.get("service_location", ""),
    phone_verified=False,
)

        otp_service.clear_pending_profile(user.id)

        return Response(
            {
                "detail": "Email verified and  profile created successfully.",
                "profile": ProviderProfileSerializer(profile).data,
            },
            status=status.HTTP_201_CREATED,
        )



class ProviderProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProviderProfileSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [permissions.AllowAny()]

        return [permissions.IsAuthenticated()]

    def get_object(self):
        profile_id = self.kwargs.get("pk")

        try:
            profile = ProviderProfile.objects.select_related(
                "user"
            ).get(pk=profile_id)
        except ProviderProfile.DoesNotExist:
            raise NotFound("Provider profile not found.")

        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return profile

        user = self.request.user

        if user.role == "provider" and profile.user_id == user.id:
            return profile

        if user.is_staff:
            return profile

        raise permissions.PermissionDenied(
            "You are not allowed to update this profile."
        )

class GetAllProvidersView(generics.ListAPIView):
    serializer_class = ProviderProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return ProviderProfile.objects.filter(
            verification_status="approved"
        ).select_related("user")

class PendingProvidersView(generics.ListAPIView):
    serializer_class = ProviderProfileSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return ProviderProfile.objects.filter(
            verification_status="pending"
        ).select_related("user")
    
class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
    
class ProviderVerificationView(generics.UpdateAPIView):
    queryset = ProviderProfile.objects.select_related("user").all()
    serializer_class = ProviderVerificationSerializer
    permission_classes = [IsSuperUser]
    http_method_names = ["patch", "options", "head"]



class MyProviderProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProviderProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user

        if user.role != "provider":
            raise permissions.PermissionDenied(
                "Only providers can access this profile."
            )

        try:
            return ProviderProfile.objects.get(user=user)
        except ProviderProfile.DoesNotExist:
            raise NotFound("Provider profile not found.")

