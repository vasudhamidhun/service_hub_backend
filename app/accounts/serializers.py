
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import ProviderProfile

        
User = get_user_model()

class BaseRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "password"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return email

    def create(self, validated_data):
        full_name = validated_data["full_name"].strip()

        # Generate a unique internal username.
        base_username = slugify(full_name).replace("-", "_") or "user"
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        validated_data["full_name"] = full_name
        validated_data["username"] = username
        validated_data["role"] = self.user_role

        return User.objects.create_user(**validated_data)

class CustomerRegisterSerializer(BaseRegisterSerializer):
    user_role = User.Role.CUSTOMER


class ProviderRegisterSerializer(BaseRegisterSerializer):
    user_role = User.Role.PROVIDER


# --------------------LOGIN--------------------------------------



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token



class BaseRoleLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    expected_role = None

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        password = attrs["password"]

        user_record = User.objects.filter(
            email__iexact=email
        ).first()

        print("EMAIL RECEIVED:", email)
        print("USER FOUND:", user_record is not None)

        if not user_record:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        user = authenticate(
            request=self.context.get("request"),
            username=user_record.username,
            password=password,
        )

        print("USERNAME USED:", user_record.username)
        print("AUTHENTICATION SUCCESS:", user is not None)

        if user is None:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        if user.role != self.expected_role:
            raise serializers.ValidationError(
                "This account cannot use this login page."
            )

        refresh = CustomTokenObtainPairSerializer.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

class CustomerLoginSerializer(BaseRoleLoginSerializer):
    expected_role = User.Role.CUSTOMER


class ProviderLoginSerializer(BaseRoleLoginSerializer):
    expected_role = User.Role.PROVIDER


class AdminLoginSerializer(CustomTokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")

        user_record = User.objects.filter(
            email__iexact=email
        ).first()

        if not user_record:
            raise serializers.ValidationError(
                "Invalid admin credentials."
            )

        user = authenticate(
            request=self.context.get("request"),
            username=user_record.username,
            password=password,
        )

        if (
            user is None
            or not user.is_active
            or not user.is_staff
            or not user.is_superuser
            or user.role != User.Role.ADMIN
        ):
            raise serializers.ValidationError(
                "Invalid admin credentials."
            )

        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

# -----------------------PROVIDER PROFILE------------------------------------

class ProviderProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(
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
            "full_name",
            "email",
            "phone",
            "bio",
            "experience_years",
            "service_location",
            "profile_photo",
            "verification_status",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "email",
            "verification_status",
        ]

class ProviderSendOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderProfile
        fields = [
            "phone",
            "bio",
            "experience_years",
            "service_location",
            
        ]

    def validate_phone(self, value):
        phone = value.strip()

        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            raise serializers.ValidationError(
                "Enter a valid phone number using digits only."
            )

        return phone
    
class ProviderVerifyOTPSerializer(serializers.Serializer):
   
    otp = serializers.CharField(min_length=6, max_length=6)

    

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must contain exactly six digits."
            )

        return value



class ProviderVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderProfile
        fields = ["id", "verification_status"]
        read_only_fields = ["id"]

    def validate_verification_status(self, value):
        if value not in ["approved", "rejected"]:
            raise serializers.ValidationError(
                "Status must be approved or rejected."
            )
        return value




