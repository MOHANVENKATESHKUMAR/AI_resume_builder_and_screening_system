import logging
import secrets
from datetime import timedelta

from rest_framework.permissions import IsAuthenticated



from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from ai_resume_building.utils import (
    api_response,
    issue_otp,
    send_otp_email,
    get_valid_otp,
    send_otp_sms,
)

from .models import OTP, Candidate, OTPPurpose,  UserRole
from .serializers import (
    CandidateRegistrationSerializer,
    RecruiterRegistrationSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
   
    SendOTPSerializer,
    VerifyForgotPasswordOTPSerializer,
    VerifyOTPSerializer,
   
)

User = get_user_model()
logger = logging.getLogger(__name__)



import logging

from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status

from .models import OTP, OTPPurpose



logger = logging.getLogger(__name__)

User = get_user_model()



logger = logging.getLogger(__name__)

class CandidateRegistrationView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = CandidateRegistrationSerializer(
            data=request.data
        )

        # VALIDATE REQUEST

        if not serializer.is_valid():

            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        email = serializer.validated_data["email"].strip().lower()
        mobile = serializer.validated_data["mobile"].strip()

        try:

            with transaction.atomic():

                current_time = timezone.now()

              

                verified_email_otp = (
                    OTP.objects.select_for_update()
                    .filter(
                        email__iexact=email,
                        phone_number__isnull=True,
                        purpose=OTPPurpose.SIGNUP,
                        is_verified=True,
                        is_used=False,
                        expires_at__gt=current_time,
                    )
                    .order_by("-created_at")
                    .first()
                )

                if verified_email_otp is None:

                    return api_response(
                        False,
                        http_status=status.HTTP_400_BAD_REQUEST,
                        errors={
                            "email": [
                                "Please verify your email with OTP before signing up."
                            ]
                        },
                    )

                verified_sms_otp = (
                    OTP.objects.select_for_update()
                    .filter(
                        phone_number=mobile,
                        email__isnull=True,
                        purpose=OTPPurpose.SIGNUP,
                        is_verified=True,
                        is_used=False,
                        expires_at__gt=current_time,
                    )
                    .order_by("-created_at")
                    .first()
                )

                if verified_sms_otp is None:

                    return api_response(
                        False,
                        http_status=status.HTTP_400_BAD_REQUEST,
                        errors={
                            "mobile": [
                                "Please verify your mobile number with OTP before signing up."
                            ]
                        },
                    )

              

                user = serializer.save()

                # MARK EMAIL VERIFIED

                user.is_email_verified = True

                user.save(
                    update_fields=["is_email_verified"]
                )


                verified_email_otp.is_used = True

                verified_email_otp.save(
                    update_fields=["is_used"]
                )

                verified_sms_otp.is_used = True

                verified_sms_otp.save(
                    update_fields=["is_used"]
                )

        except IntegrityError:

            logger.exception(
                "Failed to create candidate account for email: %s",
                email,
            )

            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors={
                    "non_field_errors": [
                        "An account with these details already exists."
                    ]
                },
            )


        return api_response(
            True,
            "Candidate registered successfully.",
            http_status=status.HTTP_201_CREATED,
            data={
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "is_email_verified": user.is_email_verified,

                "candidate_id": user.candidate.id,
                "fullName": user.candidate.full_name,
                "mobile": user.candidate.mobile,
                "degree": user.candidate.degree,
                "gender": user.candidate.gender,
                "dob": user.candidate.dob,
            },
        )


class RecruiterRegistrationView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RecruiterRegistrationSerializer(
            data=request.data
        )

        # VALIDATE REQUEST

        if not serializer.is_valid():

            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        email = serializer.validated_data["Officialemail"].strip().lower()
        mobile = serializer.validated_data["mobile"].strip()

        try:

            with transaction.atomic():

                current_time = timezone.now()

              

                verified_email_otp = (
                    OTP.objects.select_for_update()
                    .filter(
                        email__iexact=email,
                        phone_number__isnull=True,
                        purpose=OTPPurpose.SIGNUP,
                        is_verified=True,
                        is_used=False,
                        expires_at__gt=current_time,
                    )
                    .order_by("-created_at")
                    .first()
                )

                if verified_email_otp is None:

                    return api_response(
                        False,
                        http_status=status.HTTP_400_BAD_REQUEST,
                        errors={
                            "email": [
                                "Please verify your email with OTP before signing up."
                            ]
                        },
                    )

               

                verified_sms_otp = (
                    OTP.objects.select_for_update()
                    .filter(
                        phone_number=mobile,
                        email__isnull=True,
                        purpose=OTPPurpose.SIGNUP,
                        is_verified=True,
                        is_used=False,
                        expires_at__gt=current_time,
                    )
                    .order_by("-created_at")
                    .first()
                )

                if verified_sms_otp is None:

                    return api_response(
                        False,
                        http_status=status.HTTP_400_BAD_REQUEST,
                        errors={
                            "mobile": [
                                "Please verify your mobile number with OTP before signing up."
                            ]
                        },
                    )

              

                user = serializer.save()

                # MARK EMAIL VERIFIED

                user.is_email_verified = True

                user.save(
                    update_fields=["is_email_verified"]
                )

             
                verified_email_otp.is_used = True

                verified_email_otp.save(
                    update_fields=["is_used"]
                )

                verified_sms_otp.is_used = True

                verified_sms_otp.save(
                    update_fields=["is_used"]
                )

        except IntegrityError:

            logger.exception(
                "Failed to create recruiter account for email: %s",
                email,
            )

            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors={
                    "non_field_errors": [
                        "An account with these details already exists."
                    ]
                },
            )

    

        recruiter = user.recruiter

        return api_response(
            True,
            "Recruiter registered successfully.",
            http_status=status.HTTP_201_CREATED,
            data={
                "id": user.id,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "is_email_verified": user.is_email_verified,

                "recruiter_id": recruiter.id,
                "fullName": recruiter.full_name,
                "designation": recruiter.designation,
                "gender": recruiter.gender,
                "company_name": recruiter.company_name,
                "company_website": recruiter.company_website,
                "industry_type": recruiter.industry_type,
            },
        )




    
class SendSignupOTPAPIView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = SendOTPSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        value = serializer.validated_data["value"]

        # Check existing user

        if method == "email":

            if User.objects.filter(email__iexact=value).exists():

                return api_response(
                    False,
                    "Email already registered.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

        elif method == "sms":

            if User.objects.filter(phone_number=value).exists():

                return api_response(
                    False,
                    "Mobile number already registered.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

        try:

            otp = issue_otp(
                method=method,
                value=value,
                purpose=OTPPurpose.SIGNUP,
            )

            if method == "email":

                sent = send_otp_email(
                    value,
                    otp,
                    "Signup Email Verification",
                )

            else:

                sent = send_otp_sms(
                    value,
                    otp,
                )

            if not sent:

                return api_response(
                    False,
                    "Unable to send OTP. Please try again.",
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception:

            logger.exception("Failed to send signup OTP")

            return api_response(
                False,
                "Unable to send OTP. Please try again.",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return api_response(
            True,
            "OTP sent successfully.",
            method=method,
            value=value,
        )

class VerifySignupOTPAPIView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = VerifyOTPSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        value = serializer.validated_data["value"]
        otp_value = serializer.validated_data["otp"]

        otp_obj, error = get_valid_otp(
            method=method,
            value=value,
            purpose=OTPPurpose.SIGNUP,
            otp_value=otp_value,
        )

        if error:

            return api_response(
                False,
                error,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        otp_obj.is_verified = True

        otp_obj.save(update_fields=["is_verified"])

        return api_response(
            True,
            "OTP verified successfully.",
            method=method,
            value=value,
        )
class LoginAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]

        # Find user using email
        user = User.objects.filter(
            email__iexact=email
        ).first()

        if user is None:
            return api_response(
                False,
                "Invalid email or password.",
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        # Authenticate password
        authenticated_user = authenticate(
                    request=request,
                    email=email,
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

        authenticated_user.last_login = timezone.now()
        authenticated_user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(authenticated_user)

        return api_response(
            True,
            "Login successful.",
            access=str(refresh.access_token),
            refresh=str(refresh),
            user={
                "id": authenticated_user.id,
                "username": authenticated_user.username,
                "email": authenticated_user.email,
                "role": authenticated_user.role,
                "phone_number": authenticated_user.phone_number,
                "is_email_verified": authenticated_user.is_email_verified,
                "is_phone_verified": authenticated_user.is_phone_verified,
            }
        )


    

def get_user_by_method(method, value):

    if method == "email":

        return User.objects.filter(
            email__iexact=value
        ).first()

    elif method == "sms":

        return User.objects.filter(
            phone_number=value
        ).first()

    return None


# FORGOT PASSWORD - SEND OTP

class ForgotPasswordAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        value = serializer.validated_data["value"]

        user = get_user_by_method(method, value)

        # Avoid revealing whether the account exists.
        if user:

            try:
                otp_value = issue_otp(
                    method=method,
                    value=value,
                    purpose=OTPPurpose.FORGOT_PASSWORD
                )

                if method == "email":

                    sent = send_otp_email(
                        email=value,
                        otp=otp_value,
                        subject="Password Reset OTP"
                    )

                elif method == "sms":

                    sent = send_otp_sms(
                        phone_number=value,
                        otp=otp_value
                    )

                else:
                    sent = False

                if not sent:
                    return api_response(
                        False,
                        "Unable to send OTP. Please try again.",
                        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except Exception:

                logger.exception(
                    "Forgot password OTP generation failed"
                )

                return api_response(
                    False,
                    "Unable to process your request.",
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return api_response(
            True,
            "If the account exists, an OTP has been sent."
        )

class VerifyForgotPasswordOTPAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        serializer = VerifyForgotPasswordOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        value = serializer.validated_data["value"]
        otp_value = serializer.validated_data["otp"]

        user = get_user_by_method(method, value)

        if not user:
            return api_response(
                False,
                "Invalid OTP.",
                http_status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():

            otp_obj, error = get_valid_otp(
                method=method,
                value=value,
                purpose=OTPPurpose.FORGOT_PASSWORD,
                otp_value=otp_value
            )

            if error:
                return api_response(
                    False,
                    error,
                    http_status=status.HTTP_400_BAD_REQUEST
                )

            otp_obj.is_verified = True
            otp_obj.save(update_fields=["is_verified"])

        return api_response(
            True,
            "OTP verified successfully."
        )

    
# RESET PASSWORD
class ResetPasswordAPIView(APIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):

        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        value = serializer.validated_data["value"]
        otp_value = serializer.validated_data["otp"]
        password = serializer.validated_data["password"]

        user = get_user_by_method(method, value)

        if not user:
            return api_response(
                False,
                "Invalid password reset request.",
                http_status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():

            otp_queryset = OTP.objects.select_for_update().filter(
                purpose=OTPPurpose.FORGOT_PASSWORD,
                is_verified=True,
                is_used=False,
                otp=otp_value,
                expires_at__gt=timezone.now(),
            )

            if method == "email":

                otp_queryset = otp_queryset.filter(
                    email__iexact=value,
                    phone_number__isnull=True,
                )

            elif method == "sms":

                otp_queryset = otp_queryset.filter(
                    phone_number=value,
                    email__isnull=True,
                )

            else:

                return api_response(
                    False,
                    "Invalid verification method.",
                    http_status=status.HTTP_400_BAD_REQUEST
                )

            otp_obj = otp_queryset.order_by("-created_at").first()

            if otp_obj is None:

                return api_response(
                    False,
                    "Invalid OTP or OTP not verified.",
                    http_status=status.HTTP_400_BAD_REQUEST
                )

            # Change password
            user.set_password(password)

            user.save(update_fields=["password"])

            # Mark OTP as used
            otp_obj.is_used = True

            otp_obj.save(update_fields=["is_used"])

        return api_response(
            True,
            "Password reset successfully."
        )

    
    
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



class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return api_response(
                False,
                "Refresh token is required.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return api_response(
                True,
                "Logged out successfully.",
            )

        except Exception:
            return api_response(
                False,
                "Invalid or expired refresh token.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )



