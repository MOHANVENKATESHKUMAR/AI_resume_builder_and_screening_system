import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ai_resume_building.utils import FRONTEND_RESET_PASSWORD_URL, api_response, generate_otp, get_client_ip, get_valid_otp, issue_otp, send_otp_email

from .models import OTP, Candidate, OTPPurpose, PasswordResetToken
from .serializers import (
    CandidateSignupSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)




# Signup


class CandidateSignupView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CandidateSignupSerializer(data=request.data)

        if not serializer.is_valid():
            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        email = serializer.validated_data["email"]

       
        verified_otp = OTP.objects.filter(
            email=email,
            purpose=OTPPurpose.SIGNUP,
            is_verified=True,
        ).order_by("-created_at").first()

        if verified_otp is None:
            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors={"email": ["Please verify your email with the OTP before signing up."]},
            )

        try:
            with transaction.atomic():
                user = serializer.save()
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
                verified_otp.delete()
                 # Create an empty candidate profile
                Candidate.objects.create(
                    user=user
                )
        except IntegrityError:
            logger.exception("Failed to create user account for email: %s", email)
            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors={"non_field_errors": ["An account with these details already exists."]},
            )

        return api_response(
            True,
            "User registered successfully.",
            http_status=status.HTTP_201_CREATED,
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
            },
        )


class SendSignupOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        if User.objects.filter(email__iexact=email).exists():
            return api_response(
                False,
                "Email already registered.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        otp = issue_otp(email, OTPPurpose.SIGNUP)
        send_otp_email(email, otp, "Signup Email Verification")

        return api_response(True, "OTP sent successfully.")


class VerifySignupOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp_value = serializer.validated_data["otp"]

        otp_obj, error = get_valid_otp(email, OTPPurpose.SIGNUP, otp_value)
        if error:
            return api_response(False, error, http_status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_verified = True
        otp_obj.save(update_fields=["is_verified"])

        return api_response(True, "Email verified successfully.")



# Login (2-step: password, then OTP)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(email=email).first()

        authenticated_user = authenticate(
            username=user.username if user else email,
            password=password,
        )

        if authenticated_user is None:
            return api_response(
                False,
                "Invalid email or password.",
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        if not authenticated_user.is_active:
            return api_response(
                False,
                "Your account has been deactivated.",
                http_status=status.HTTP_403_FORBIDDEN,
            )

        otp = issue_otp(email, OTPPurpose.LOGIN)
        send_otp_email(email, otp, "Login Verification OTP")

        return api_response(True, "OTP sent successfully.", email=email)


class VerifyLoginOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp_value = serializer.validated_data["otp"]

        otp_obj, error = get_valid_otp(email, OTPPurpose.LOGIN, otp_value)
        if error:
            return api_response(False, error, http_status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()

        
        if user is None or not user.is_active:
            return api_response(
                False,
                "Your account has been deactivated.",
                http_status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            otp_obj.is_verified = True
            otp_obj.save(update_fields=["is_verified"])

            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)
        ip_address = get_client_ip(request)

        return api_response(
            True,
            "Login successful.",
            access=str(refresh.access_token),
            refresh=str(refresh),
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "phone_number": user.phone_number,
                "is_email_verified": user.is_email_verified,
                "is_phone_verified": user.is_phone_verified,
            },
            login_info={
                "last_login": user.last_login.strftime("%d-%m-%Y %I:%M:%S %p"),
                "ip_address": ip_address,
            },
        )



# Forgot / reset password


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()

        # Only do the real work if the account exists, but always return
        # the same message/status either way so the endpoint can't be used
        # to enumerate registered emails.
        if user is not None:
            reset = PasswordResetToken.objects.create(user=user)
            reset_link = f"{FRONTEND_RESET_PASSWORD_URL}?token={reset.token}"

            send_mail(
                subject="Reset Your Password",
                message=f"Click the link below to reset your password:\n\n{reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )

        return api_response(
            True,
            "If an account exists for this email, a password reset link has been sent.",
        )


class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]

        reset = PasswordResetToken.objects.filter(token=token, is_used=False).first()

        if reset is None:
            return api_response(
                False,
                "Invalid reset link.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if reset.expires_at < timezone.now():
            return api_response(
                False,
                "Reset link has expired.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = reset.user
            user.set_password(password)
            user.save(update_fields=["password"])

            reset.is_used = True
            reset.save(update_fields=["is_used"])

            # Invalidate any other outstanding reset tokens for this user
            # so an older, still-valid link can't be used afterward.
            PasswordResetToken.objects.filter(
                user=user, is_used=False
            ).exclude(pk=reset.pk).update(is_used=True)

        return api_response(True, "Password updated successfully.")


# ---------------------------------------------------------------------------
# Social login — inactive, left untouched.
# ---------------------------------------------------------------------------

# class GoogleLoginAPIView(generics.GenericAPIView):
#     serializer_class = GoogleLoginSerializer
#     permission_classes=[AllowAny]
#
#     def post(self, request):
#
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         token = serializer.validated_data["id_token"]
#
#         try:
#             google_user = id_token.verify_oauth2_token(
#                 token,
#                 requests.Request(),
#                 settings.GOOGLE_CLIENT_ID,
#             )
#
#         except Exception:
#             return Response(
#                 {"message": "Invalid Google Token"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#
#         email = google_user["email"]
#
#         user, created = User.objects.get_or_create(
#             email=email,
#             defaults={
#                 "username": email.split("@")[0],
#                 "first_name": google_user.get("given_name", ""),
#                 "last_name": google_user.get("family_name", ""),
#                 "is_email_verified": True,
#             },
#         )
#
#         refresh = RefreshToken.for_user(user)
#
#         return Response(
#             {
#                 "message": "Login Successful",
#                 "access": str(refresh.access_token),
#                 "refresh": str(refresh),
#                 "user": {
#                     "id": user.id,
#                     "email": user.email,
#                     "username": user.username,
#                     "role": user.role,
#                 },
#             }
#         )


# from .serializers import LinkedInLoginSerializer
#
# class LinkedInLoginAPIView(generics.GenericAPIView):
#
#     serializer_class = LinkedInLoginSerializer
#
#     def post(self, request):
#
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         code = serializer.validated_data["code"]
#
#         token_response = requests.post(
#             "https://www.linkedin.com/oauth/v2/accessToken",
#             data={
#                 "grant_type": "authorization_code",
#                 "code": code,
#                 "client_id": settings.LINKEDIN_CLIENT_ID,
#                 "client_secret": settings.LINKEDIN_CLIENT_SECRET,
#                 "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
#             },
#         )
#
#         if token_response.status_code != 200:
#             return Response(
#                 {"message": "Unable to authenticate"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#
#         access_token = token_response.json()["access_token"]
#
#         profile = requests.get(
#             "https://api.linkedin.com/v2/userinfo",
#             headers={
#                 "Authorization": f"Bearer {access_token}"
#             },
#         ).json()
#
#         email = profile["email"]
#
#         user, created = User.objects.get_or_create(
#             email=email,
#             defaults={
#                 "username": email.split("@")[0],
#                 "first_name": profile.get("given_name", ""),
#                 "last_name": profile.get("family_name", ""),
#                 "is_email_verified": True,
#             },
#         )
#
#         refresh = RefreshToken.for_user(user)
#
#         return Response(
#             {
#                 "access": str(refresh.access_token),
#                 "refresh": str(refresh),
#                 "user": {
#                     "id": user.id,
#                     "email": user.email,
#                     "username": user.username,
#                 },
#             }
#         )