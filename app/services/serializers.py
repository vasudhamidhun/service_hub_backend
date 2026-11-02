
from rest_framework import serializers
from app.accounts.models import ProviderProfile
from .models import ServiceRequest

class ProviderSearchSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )
    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = ProviderProfile
        fields = [
            "id",
            "provider_name",
            "email",
            "phone",
            "bio",
            "service_category",
            "experience_years",
            "service_location",
            "profile_photo",
            "verification_status",
        ]



class ServiceRequestSerializer(serializers.ModelSerializer):

    provider_name = serializers.CharField(
        source="provider.user.full_name",
        read_only=True,
    )

    provider_category = serializers.CharField(
        source="provider.service_category",
        read_only=True,
    )

    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True,
    )

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "customer",
            "customer_name",
            "provider",
            "provider_name",
            "provider_category",
            "problem_description",
            "service_location",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer",
            "customer_name",
            "provider",
            "provider_name",
            "provider_category",
            "status",
            "created_at",
            "updated_at",
        ]



class CustomerServiceRequestSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(
        source="provider.user.full_name",
        read_only=True
    )

    provider_phone = serializers.CharField(
        source="provider.phone",
        read_only=True
    )

    service_category = serializers.CharField(
        source="provider.service_category",
        read_only=True
    )

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "status",
            "created_at",
            "updated_at",

            # Request details
            "problem_description",
            "service_location",

            # Essential provider details
            "provider_name",
            "provider_phone",
            "service_category",
        ]