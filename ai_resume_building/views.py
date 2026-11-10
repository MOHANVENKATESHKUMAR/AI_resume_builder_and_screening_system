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
)

from .models import OTP, Candidate, OTPPurpose,  Recruiter
from .serializers import (
    CandidateRegistrationSerializer,
    RecruiterRegistrationSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
   
    SendOTPSerializer,
    VerifyForgotPasswordOTPSerializer,
    VerifyOTPSerializer,
    UserRole
)

User = get_user_model()
logger = logging.getLogger(__name__)




# canditate Registration  with needed email verify

class CandidateRegistrationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = CandidateRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        email = serializer.validated_data["email"]

        verified_otp = (
            OTP.objects.filter(
                email=email,
                purpose=OTPPurpose.SIGNUP,
                is_verified=True,
            )
            .order_by("-created_at")
            .first()
        )

        if verified_otp is None:
            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors={
                    "email": [
                        "Please verify your email with the OTP before signing up."
                    ]
                },
            )

        try:
            with transaction.atomic():
                user = serializer.save()

                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])

                verified_otp.delete()

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
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "candidate_id": user.candidate.id,
            },
        )

#recruiter Registration  with needed email verification


class RecruiterRegistrationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RecruiterRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        email = serializer.validated_data["email"]

        verified_otp = (
            OTP.objects.filter(
                email=email,
                purpose=OTPPurpose.SIGNUP,
                is_verified=True,
            )
            .order_by("-created_at")
            .first()
        )

        if verified_otp is None:
            return api_response(
                False,
                http_status=status.HTTP_400_BAD_REQUEST,
                errors={
                    "email": [
                        "Please verify your email with the OTP before signing up."
                    ]
                },
            )

        try:
            with transaction.atomic():
                user = serializer.save()

                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])

                verified_otp.delete()

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

        return api_response(
            True,
            "Recruiter registered successfully.",
            http_status=status.HTTP_201_CREATED,
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "recruiter_id": user.recruiter.id,
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

from django.contrib.auth import authenticate

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        login = serializer.validated_data["login"]
        password = serializer.validated_data["password"]
        role = serializer.validated_data["role"]

        # Candidate -> Email only
        if role == UserRole.CANDIDATE:
            user = User.objects.filter(
                email__iexact=login,
                role=UserRole.CANDIDATE,
            ).first()

        # Employer -> Username only
        elif role == UserRole.EMPLOYER:
            user = User.objects.filter(
                username__iexact=login,
                role=UserRole.EMPLOYER,
            ).first()

        else:
            return api_response(
                False,
                "Invalid role.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if user is None:
            return api_response(
                False,
                "Invalid credentials.",
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        authenticated_user = authenticate(
            username=user.username,
            password=password,
        )

        if authenticated_user is None:
            return api_response(
                False,
                "Invalid credentials.",
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        if not authenticated_user.is_active:
            return api_response(
                False,
                "Your account has been deactivated.",
                http_status=status.HTTP_403_FORBIDDEN,
            )

        otp = issue_otp(user.email, OTPPurpose.LOGIN)
        send_otp_email(user.email, otp, "Login Verification OTP")

        return api_response(
            True,
            "OTP sent successfully.",
            email=user.email,
        )

    
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
        #ip_address = get_client_ip(request)

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
            }
        #     login_info={
        #         "last_login": user.last_login.strftime("%d-%m-%Y %I:%M:%S %p"),
        #         "ip_address": ip_address,
        #     },
        )



# ============================================================
# HELPER: FIND USER USING EMAIL OR PHONE
# ============================================================

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

    def post(self, request):

        serializer = ForgotPasswordSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        method = serializer.validated_data["method"]
        value = serializer.validated_data["value"]

        user = get_user_by_method(
            method,
            value
        )

        # Avoid revealing whether the account exists.
        if user:

            try:

                otp_value = issue_otp(
                    method=method,
                    value=value,
                    purpose=OTPPurpose.FORGOT_PASSWORD
                )

                if method == "email":

                    email_sent = send_otp_email(
                        email=value,
                        otp=otp_value,
                        subject="Password Reset OTP"
                    )

                    if not email_sent:

                        return api_response(
                            False,
                            "Unable to send OTP. Please try again.",
                            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                elif method == "sms":

                    # SMS provider integration required here.
                    # Example: Twilio SMS sending function.
                    return api_response(
                        False,
                        "SMS service is not configured yet.",
                        http_status=status.HTTP_501_NOT_IMPLEMENTED
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

    def post(self, request):

        serializer = VerifyForgotPasswordOTPSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        method = serializer.validated_data["method"]
        value = serializer.validated_data["value"]
        otp_value = serializer.validated_data["otp"]

        user = get_user_by_method(
            method,
            value
        )

        if not user:

            return api_response(
                False,
                "Invalid OTP.",
                http_status=status.HTTP_400_BAD_REQUEST
            )

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

        otp_obj.save(
            update_fields=["is_verified"]
        )

        return api_response(
            True,
            "OTP verified successfully."
        )


# RESET PASSWORD

class ResetPasswordAPIView(APIView):

    permission_classes = [AllowAny]

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

            # Base OTP query
            otp_queryset = OTP.objects.select_for_update().filter(
                purpose=OTPPurpose.FORGOT_PASSWORD,
                is_verified=True,
                is_used=False,
                otp=otp_value,
            )

            # Match OTP by email or phone number
            if method == "email":

                otp_queryset = otp_queryset.filter(
                    email__iexact=value
                )

            elif method == "sms":

                otp_queryset = otp_queryset.filter(
                    phone_number=value
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

          

            user.set_password(password)

            user.save(update_fields=["password"])

            

            otp_obj.delete()

        

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



