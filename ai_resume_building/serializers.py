import re

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from ai_resume_building.models import User, UserRole , Candidate , Recruiter
from django.contrib.auth import get_user_model

User = get_user_model()

PASSWORD_SPECIAL_CHARS_RE = r"[!@#$%^&*(),.?\":{}|<>]"


def validate_password_strength(value):
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", value):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", value):
        raise serializers.ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", value):
        raise serializers.ValidationError("Password must contain at least one number.")
    if not re.search(PASSWORD_SPECIAL_CHARS_RE, value):
        raise serializers.ValidationError("Password must contain at least one special character.")
    return value

class CandidateRegistrationSerializer(serializers.Serializer):

    role = serializers.ChoiceField(
        choices=UserRole.choices,
        default=UserRole.CANDIDATE
    )

    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    mobile = serializers.CharField(max_length=15)
    degree = serializers.CharField(max_length=100)

    gender = serializers.ChoiceField(
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other'),
            ('Prefer not to say', 'Prefer not to say'),
        ]
    )

    dob = serializers.DateField()

    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        min_length=8
    )

    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists."
            )
        return value

    def validate(self, attrs):

        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        return attrs

    def create(self, validated_data):

        validated_data.pop("confirm_password")

        password = validated_data.pop("password")
        role = validated_data.pop("role")
        email = validated_data.pop("email")

        user = User(
            email=email,
            role=role,
            phone_number=validated_data.get("mobile")
        )

        user.set_password(password)
        user.save()

        Candidate.objects.create(
            user=user,
            full_name=validated_data.get("full_name"),
            mobile=validated_data.get("mobile"),
            degree=validated_data.get("degree"),
            gender=validated_data.get("gender"),
            dob=validated_data.get("dob"),
        )

        return user


#Recruiter registration serializer
class RecruiterRegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    recruiter_name = serializers.CharField(write_only=True)
    designation = serializers.CharField(write_only=True)
    company_name = serializers.CharField(write_only=True)
    company_website = serializers.URLField(write_only=True, required=False, allow_blank=True)
    company_location = serializers.CharField(write_only=True)
    industry_type = serializers.CharField(write_only=True)

    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            #"username",
            "email",
            "phone_number",
            "recruiter_name",
            "designation",
            "company_name",
            "company_website",
            "company_location",
            "industry_type",
            "password",
            "confirm_password",
        ]

    def validate_full_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Full name is required.")

        return value

    def validate_username(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Username is required.")

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already exists.")

        return value

    def validate_email(self, value):
        value = value.strip().lower()

        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Enter a valid email address.")

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")

        return value

    def validate_phone_number(self, value):
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "Phone number should contain only digits."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "Phone number must contain exactly 10 digits."
            )

        return value

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_password": "Passwords do not match."
                }
            )

        return attrs

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        recruiter_name = validated_data.pop("recruiter_name")
        designation = validated_data.pop("designation")
        company_name = validated_data.pop("company_name")
        company_website = validated_data.pop("company_website", "")
        company_location = validated_data.pop("company_location")
        industry_type = validated_data.pop("industry_type")

        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        user = User(
            #username=validated_data["username"],
            email=validated_data["email"],
            phone_number=validated_data["phone_number"],
            role=UserRole.EMPLOYER,
        )

        user.set_password(password)
        user.save()

        Recruiter.objects.create(
            user=user,
            full_name=full_name,
            recruiter_name=recruiter_name,
            designation=designation,
            company_name=company_name,
            company_website=company_website,
            company_location=company_location,
            industry_type=industry_type,
        )

        return user
    

class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserRole.choices)

    def validate(self, attrs):
        login = attrs["login"].strip()
        role = attrs["role"]

        if role == UserRole.CANDIDATE:
            try:
                serializers.EmailField().run_validation(login)
            except serializers.ValidationError:
                raise serializers.ValidationError(
                    {"login": "Please enter a valid email address."}
                )

        attrs["login"] = login
        return attrs

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRole.choices)
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class ResetPasswordSerializer(serializers.Serializer):

    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


# class GoogleLoginSerializer(serializers.Serializer):
#     id_token = serializers.CharField(required=True)


# class LinkedInLoginSerializer(serializers.Serializer):
#     code = serializers.CharField()


