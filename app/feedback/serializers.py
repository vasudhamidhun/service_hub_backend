
from rest_framework import serializers
from .models import (
    Review,
    Complaint,
    ComplaintHistory,
    ProviderAction
)
from app.accounts.models import ProviderProfile


class ReviewSerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True
    )

    provider_name = serializers.CharField(
        source="provider.user.full_name",
        read_only=True
    )

    class Meta:
        model = Review

        fields = [
            "id",
            "customer",
            "customer_name",
            "provider",
            "provider_name",
            "service_request",
            "rating",
            "comment",
            "sentiment",
            "sentiment_confidence",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer",
            "provider",
            "sentiment",
            "sentiment_confidence",
            "created_at",
            "updated_at",
        ]

    def validate_rating(self, value):

        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )

        return value

    def validate_service_request(self, value):

        request = self.context.get("request")

        if request.user.role != "customer":
            raise serializers.ValidationError(
                "Only customers can submit reviews."
            )

        if value.customer != request.user:
            raise serializers.ValidationError(
                "You can only review your own service requests."
            )

        if value.status != "completed":
            raise serializers.ValidationError(
                "You can review only completed service requests."
            )

        if Review.objects.filter(
            service_request=value
        ).exists():
            raise serializers.ValidationError(
                "You have already reviewed this service request."
            )

        return value

    def create(self, validated_data):

        service_request = validated_data["service_request"]

        validated_data["customer"] = self.context[
            "request"
        ].user

        validated_data["provider"] = service_request.provider

        return super().create(validated_data)




class ComplaintHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ComplaintHistory

        fields = [
            "id",
            "event_type",
            "old_status",
            "new_status",
            "created_at",
        ]

        read_only_fields = fields


class ComplaintSerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True
    )

    provider_name = serializers.CharField(
        source="provider.user.full_name",
        read_only=True
    )

    history = ComplaintHistorySerializer(
        many=True,
        read_only=True
    )

    provider = serializers.PrimaryKeyRelatedField(
        queryset=ProviderProfile.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Complaint

        fields = [
            "id",
            "customer",
            "customer_name",
            "service_request",
            "provider",
            "provider_name",
            "category",
            "subject",
            "description",
            "evidence",
            "status",
            "provider_response",
            "provider_responded_at",
            "response_deadline",
            "resolution",
            "history",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer",
            "customer_name",
            "provider",
            "provider_name",
            "status",
            "provider_response",
            "provider_responded_at",
            "response_deadline",
            "resolution",
            "history",
            "created_at",
            "updated_at",
        ]

    
class ProviderComplaintResponseSerializer(serializers.Serializer):

    provider_response = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )

    def validate_provider_response(self, value):

        if not value.strip():
            raise serializers.ValidationError(
                "Please provide a valid response."
            )

        return value

class ProviderComplaintSerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True
    )

    class Meta:
        model = Complaint

        fields = [
            "id",
            "customer_name",
            "category",
            "subject",
            "description",
            "evidence",
            "service_request",
            "status",
            "provider_response",
            "provider_responded_at",
            "response_deadline",
            "created_at",
        ]

        read_only_fields = fields


class AdminComplaintHistorySerializer(serializers.ModelSerializer):

    updated_by_name = serializers.CharField(
        source="updated_by.full_name",
        read_only=True
    )

    class Meta:
        model = ComplaintHistory

        fields = [
            "id",
            "event_type",
            "updated_by",
            "updated_by_name",
            "old_status",
            "new_status",
            "remarks",
            "created_at",
        ]

        read_only_fields = fields


class AdminComplaintSerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True
    )

    provider_name = serializers.CharField(
        source="provider.user.full_name",
        read_only=True
    )

    history = AdminComplaintHistorySerializer(
    many=True,
    read_only=True
    )

    provider_actions = serializers.SerializerMethodField()

    class Meta:
        model = Complaint

        fields = [
            "id",
            "customer",
            "customer_name",
            "provider",
            "provider_name",
            "service_request",
            "category",
            "subject",
            "description",
            "evidence",
            "status",
            "provider_response",
            "provider_responded_at",
            "response_deadline",
            "admin_notes",
            "resolution",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
            "history",
            "provider_actions",
        ]

        read_only_fields = [
            "id",
            "customer",
            "provider",
            "provider_response",
            "provider_responded_at",
            "response_deadline",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
            "history",
            "provider_actions",
        ]

    def get_provider_actions(self, obj):

        actions = obj.provider_actions.select_related(
            "provider__user",
            "performed_by"
        )

        return ProviderActionSerializer(
            actions,
            many=True
        ).data

class ProviderActionSerializer(serializers.ModelSerializer):

    provider_name = serializers.CharField(
        source="provider.user.full_name",
        read_only=True
    )

    admin_name = serializers.CharField(
        source="performed_by.full_name",
        read_only=True
    )

    class Meta:
        model = ProviderAction

        fields = [
            "id",
            "provider",
            "provider_name",
            "complaint",
            "action_type",
            "reason",
            "performed_by",
            "admin_name",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "provider_name",
            "performed_by",
            "admin_name",
            "created_at",
        ]





