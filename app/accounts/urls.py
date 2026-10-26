
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomerRegisterView,
    ProviderRegisterView,
    CustomerLoginView,
    ProviderLoginView,
    ProviderProfileView,
    GetAllProvidersView,
    PendingProvidersView,
    AdminLoginView,
    ProviderVerificationView,
    ProviderCreation_SendOTPView,
    ProviderVerifyOTPView,MyProviderProfileView
)

urlpatterns = [
    # Registration
    path(
        "api/auth/customer/register/",
        CustomerRegisterView.as_view(),
        name="customer-register",
    ),
    path(
        "api/auth/provider/register/",
        ProviderRegisterView.as_view(),
        name="provider-register",
    ),

    # Login
    path(
        "api/auth/customer/login/",
        CustomerLoginView.as_view(),
        name="customer-login",
    ),
    path(
        "api/auth/provider/login/",
        ProviderLoginView.as_view(),
        name="provider-login",
    ),
    path(
        "api/auth/admin/login/",
        AdminLoginView.as_view(),
        name="admin-login",
    ),

    # Provider email OTP and profile
    path(
        "api/providers/profile/",
        ProviderCreation_SendOTPView.as_view(),
        name="provider-send-otp",
    ),
    path(
        "api/providers/phone/verify-otp/",
        ProviderVerifyOTPView.as_view(),
        name="provider-verify-otp",
    ),
    path(
        "api/providers/<int:pk>/profile/",
        ProviderProfileView.as_view(),
        name="provider-profile",
    ),

    path(
    "api/providers/me/profile/",
    MyProviderProfileView.as_view(),
    name="my-provider-profile",
),
    path(
        "api/providers/",
        GetAllProvidersView.as_view(),
        name="provider-list",
    ),

    # Admin
    path(
        "api/admin/providers/pending/",
        PendingProvidersView.as_view(),
        name="pending-providers",
    ),
    path(
        "api/admin/providers/<int:pk>/verification/",
        ProviderVerificationView.as_view(),
        name="provider-verification",
    ),

    # JWT refresh
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
]
