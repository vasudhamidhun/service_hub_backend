
from rest_framework import serializers
from .models import Review,Complaint


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
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer",
            "provider",
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



class ComplaintSerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True
    )

    provider_name = serializers.CharField(
        source="provider.user.full_name",
        read_only=True
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
            "admin_notes",
            "resolution",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer",
            "provider",
            "status",
            "admin_notes",
            "resolution",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):

        request = self.context.get("request")

        if request.user.role != "customer":
            raise serializers.ValidationError(
                "Only customers can submit complaints."
            )

        service_request = attrs.get("service_request")
        category = attrs.get("category")

        if service_request:
            if service_request.customer != request.user:
                raise serializers.ValidationError(
                    "You can complain only about your own service requests."
                )

            attrs["provider"] = service_request.provider

        elif category != "platform" and not attrs.get("provider"):

            raise serializers.ValidationError(
                "A provider or service request is required "
                "for this complaint category."
            )

        return attrs

    def create(self, validated_data):
        validated_data["customer"] = self.context[
            "request"
        ].user
        return super().create(validated_data)











