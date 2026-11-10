import re
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ai_resume_building.models import User, UserRole , Candidate , Recruiter
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
import re
import re

from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone



from .models import Candidate, TermsAcceptance


from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from .models import Candidate, UserRole


User = get_user_model()



PASSWORD_SPECIAL_CHARS_RE = r"""[!@#$%^&*(),.?":{}|<>]"""


def validate_password_strength(value):

    if len(value) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters long."
        )

    if not re.search(r"[A-Z]", value):
        raise serializers.ValidationError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(r"[a-z]", value):
        raise serializers.ValidationError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(r"\d", value):
        raise serializers.ValidationError(
            "Password must contain at least one number."
        )

    if not re.search(PASSWORD_SPECIAL_CHARS_RE, value):
        raise serializers.ValidationError(
            "Password must contain at least one special character."
        )

    return value


# CANDIDATE REGISTRATION SERIALIZER




class CandidateRegistrationSerializer(serializers.Serializer):

    # PERSONAL INFORMATION

    fullName = serializers.CharField(
        max_length=255
    )

    email = serializers.EmailField()

    mobile = serializers.CharField(
        max_length=15
    )

    degree = serializers.CharField(
        max_length=50
    )

    gender = serializers.ChoiceField(
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
            ("Other", "Other"),
            ("Prefer not to say", "Prefer not to say"),
        ]
    )

    dob = serializers.DateField()

    # AUTHENTICATION

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password_strength],
    )

    confirmPassword = serializers.CharField(
        write_only=True,
    )

    # TERMS ACCEPTANCE

    terms = serializers.BooleanField(
        write_only=True,
        required=True,
    )

    # EMAIL VALIDATION

    def validate_email(self, value):

        value = value.strip().lower()

        if User.objects.filter(email__iexact=value).exists():

            raise serializers.ValidationError(
                "Email already exists."
            )

        return value

    # NAME VALIDATION

    def validate_fullName(self, value):

        value = value.strip()

        if len(value) < 2:

            raise serializers.ValidationError(
                "Enter a valid full name."
            )

        return value

    # MOBILE VALIDATION

    def validate_mobile(self, value):

        value = value.strip()

        if not re.fullmatch(r"[6-9]\d{9}", value):

            raise serializers.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        if Candidate.objects.filter(mobile=value).exists():

            raise serializers.ValidationError(
                "Mobile number already exists."
            )

        return value

    # DEGREE VALIDATION

    def validate_degree(self, value):

        value = value.strip()

        if not value:

            raise serializers.ValidationError(
                "Degree is required."
            )

        return value

    # DOB VALIDATION

    def validate_dob(self, value):

        if value >= timezone.localdate():

            raise serializers.ValidationError(
                "Date of birth must be in the past."
            )

        return value

    # OBJECT VALIDATION

    def validate(self, attrs):

        password = attrs.get("password")

        confirm_password = attrs.get("confirmPassword")

        if password != confirm_password:

            raise serializers.ValidationError({
                "confirmPassword": "Passwords do not match."
            })

        if not attrs.get("terms"):

            raise serializers.ValidationError({
                "terms": "Please accept the terms and conditions."
            })

        return attrs

    # CREATE USER AND CANDIDATE

    @transaction.atomic
    def create(self, validated_data):

        full_name = validated_data["fullName"]

        email = validated_data["email"]

        mobile = validated_data["mobile"]

        degree = validated_data["degree"]

        gender = validated_data["gender"]

        dob = validated_data["dob"]

        password = validated_data["password"]

        # CREATE USER

        user = User.objects.create_user(
            email=email,
            password=password,
            role=UserRole.CANDIDATE,
            phone_number=mobile,
        )

        # CREATE CANDIDATE PROFILE

        Candidate.objects.create(
            user=user,
            full_name=full_name,
            mobile=mobile,
            degree=degree,
            gender=gender,
            dob=dob,
        )

        # SAVE TERMS ACCEPTANCE

        TermsAcceptance.objects.create(
            user=user,
            terms_accepted=True,
            privacy_policy_accepted=True,
            terms_version="1.0",
        )

        return user




class RecruiterRegistrationSerializer(serializers.Serializer):

    # PERSONAL INFORMATION

    fullName = serializers.CharField(
        max_length=255
    )

    Officialemail = serializers.EmailField()

    mobile = serializers.CharField(
        max_length=15
    )

    Designation = serializers.CharField(
        max_length=100
    )

    gender = serializers.ChoiceField(
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
            ("Other", "Other"),
            ("Prefer not to say", "Prefer not to say"),
        ]
    )

    # COMPANY INFORMATION

    CompanyName = serializers.CharField(
        max_length=255
    )

    Url = serializers.URLField(
        max_length=500
    )

    Industry = serializers.CharField(
        max_length=150
    )

    # AUTHENTICATION

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password_strength],
    )

    confirmPassword = serializers.CharField(
        write_only=True
    )

    # TERMS

    terms = serializers.BooleanField(
        write_only=True,
        required=True
    )

    # FULL NAME VALIDATION

    def validate_fullName(self, value):

        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Enter a valid full name."
            )

        return value

    # EMAIL VALIDATION

    def validate_Officialemail(self, value):

        value = value.strip().lower()

        if User.objects.filter(
            email__iexact=value
        ).exists():

            raise serializers.ValidationError(
                "Email already exists."
            )

        return value

    # MOBILE VALIDATION

    def validate_mobile(self, value):

        value = value.strip()

        if not re.fullmatch(r"[6-9]\d{9}", value):

            raise serializers.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        if User.objects.filter(
            phone_number=value
        ).exists():

            raise serializers.ValidationError(
                "Mobile number already exists."
            )

        return value

    # DESIGNATION VALIDATION

    def validate_Designation(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Designation is required."
            )

        return value

    # COMPANY NAME VALIDATION

    def validate_CompanyName(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Company name is required."
            )

        return value

    # WEBSITE VALIDATION

    def validate_Url(self, value):

        return value.strip()

    # INDUSTRY VALIDATION

    def validate_Industry(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Industry type is required."
            )

        return value

    # OBJECT VALIDATION

    def validate(self, attrs):

        password = attrs.get("password")

        confirm_password = attrs.get("confirmPassword")

        if password != confirm_password:

            raise serializers.ValidationError({
                "confirmPassword": "Passwords do not match."
            })

        if not attrs.get("terms"):

            raise serializers.ValidationError({
                "terms": "Please accept the terms and conditions."
            })

        return attrs

    # CREATE USER AND RECRUITER

    @transaction.atomic
    def create(self, validated_data):

        full_name = validated_data["fullName"]

        email = validated_data["Officialemail"]

        mobile = validated_data["mobile"]

        designation = validated_data["Designation"]

        gender = validated_data["gender"]

        company_name = validated_data["CompanyName"]

        company_website = validated_data["Url"]

        industry_type = validated_data["Industry"]

        password = validated_data["password"]

        # CREATE USER

        user = User.objects.create_user(
            email=email,
            password=password,
            role=UserRole.EMPLOYER,
            phone_number=mobile,
        )

        # CREATE RECRUITER PROFILE

        recruiter = Recruiter.objects.create(
            user=user,
            full_name=full_name,
            designation=designation,
            gender=gender,
            company_name=company_name,
            company_website=company_website,
            industry_type=industry_type,
        )

        # SAVE TERMS ACCEPTANCE

        TermsAcceptance.objects.create(
            user=user,
            terms_accepted=True,
            privacy_policy_accepted=True,
            terms_version="1.0",
        )

        return user
    



# for registration both 
class SendOTPSerializer(serializers.Serializer):

    method = serializers.ChoiceField(
        choices=["email", "sms"]
    )

    value = serializers.CharField(max_length=255)

    def validate(self, attrs):

        method = attrs["method"]
        value = attrs["value"].strip()

        if method == "email":

            value = value.lower()

            email_serializer = serializers.EmailField()

            attrs["value"] = email_serializer.run_validation(value)

        elif method == "sms":

            if not re.fullmatch(r"[6-9]\d{9}", value):
                raise serializers.ValidationError({
                    "value": "Enter a valid 10-digit Indian mobile number."
                })

            attrs["value"] = value

        return attrs


class VerifyOTPSerializer(serializers.Serializer):

    method = serializers.ChoiceField(
        choices=["email", "sms"]
    )

    value = serializers.CharField(max_length=255)

    otp = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={
            "invalid": "OTP must contain exactly 6 digits."
        }
    )

    def validate(self, attrs):

        method = attrs["method"]
        value = attrs["value"].strip()

        if method == "email":

            value = value.lower()

            email_serializer = serializers.EmailField()

            attrs["value"] = email_serializer.run_validation(value)

        elif method == "sms":

            if not re.fullmatch(r"[6-9]\d{9}", value):
                raise serializers.ValidationError({
                    "value": "Enter a valid 10-digit Indian mobile number."
                })

            attrs["value"] = value

        return attrs

class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True
    )

    def validate_email(self, value):
        return value.strip().lower()


class ForgotPasswordSerializer(serializers.Serializer):

    method = serializers.ChoiceField(
        choices=["email", "sms"]
    )

    value = serializers.CharField(max_length=255)

    def validate(self, attrs):

        method = attrs["method"]
        value = attrs["value"].strip()

        if method == "email":

            value = value.lower()

            serializers.EmailField().run_validation(value)

        elif method == "sms":

            if not re.fullmatch(r"[6-9]\d{9}", value):
                raise serializers.ValidationError({
                    "value": "Enter a valid 10-digit mobile number."
                })

        attrs["value"] = value

        return attrs

    
class VerifyForgotPasswordOTPSerializer(serializers.Serializer):

    method = serializers.ChoiceField(
        choices=["email", "sms"]
    )

    value = serializers.CharField(max_length=255)

    otp = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={
            "invalid": "OTP must contain exactly 6 digits."
        }
    )

    def validate(self, attrs):

        method = attrs["method"]
        value = attrs["value"].strip()

        if method == "email":
            value = value.lower()
            serializers.EmailField().run_validation(value)

        elif method == "sms":
            if not re.fullmatch(r"[6-9]\d{9}", value):
                raise serializers.ValidationError({
                    "value": "Enter a valid 10-digit mobile number."
                })

        attrs["value"] = value

        return attrs


class ResetPasswordSerializer(serializers.Serializer):

    method = serializers.ChoiceField(
        choices=["email", "sms"]
    )

    value = serializers.CharField()

    otp = serializers.CharField(
        min_length=6,
        max_length=6
    )

    password = serializers.CharField(
        write_only=True
    )

    confirm_password = serializers.CharField(
        write_only=True
    )

    def validate_password(self, value):

        if len(value) < 8:
            raise ValidationError(
                "Password must be at least 8 characters long."
            )

        if not re.search(r"[A-Z]", value):
            raise ValidationError(
                "Password must contain an uppercase letter."
            )

        if not re.search(r"[a-z]", value):
            raise ValidationError(
                "Password must contain a lowercase letter."
            )

        if not re.search(r"\d", value):
            raise ValidationError(
                "Password must contain a number."
            )

        if not re.search(r"[@$!%*?&]", value):
            raise ValidationError(
                "Password must contain a special character."
            )

        validate_password(value)

        return value

    def validate(self, attrs):

        if attrs["password"] != attrs["confirm_password"]:
            raise ValidationError({
                "confirm_password": "Passwords do not match."
            })

        return attrs


    
# class GoogleLoginSerializer(serializers.Serializer):
#     id_token = serializers.CharField(required=True)


# class LinkedInLoginSerializer(serializers.Serializer):
#     code = serializers.CharField()




