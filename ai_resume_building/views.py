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

from ai_resume_building.utils import FRONTEND_RESET_PASSWORD_URL, api_response, generate_otp, get_client_ip, get_valid_otp, issue_otp, send_otp_email, send_reset_password_email

from .models import OTP, Candidate, OTPPurpose, PasswordResetToken, Recruiter
from .serializers import (
    CandidateRegistrationSerializer,
    RecruiterRegistrationSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
   
    SendOTPSerializer,
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



# Forgot / reset passwords

class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        user = User.objects.filter(
            email__iexact=email,
            role=role,
        ).first()

        if user:
            reset = PasswordResetToken.objects.create(user=user)
            reset_link = f"{FRONTEND_RESET_PASSWORD_URL}?token={reset.token}"
            send_reset_password_email(user, reset_link)

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

           
            PasswordResetToken.objects.filter(
                user=user, is_used=False
            ).exclude(pk=reset.pk).update(is_used=True)

        return api_response(True, "Password updated successfully.")




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



#for candidate profile page 
class CandidateProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        candidate = (
            Candidate.objects.select_related(
                "user",
                "active_resume",
            )
            .prefetch_related(
                "skills",
                "educations",
                "experiences",
                "certifications",
                "languages",
            )
            .get(user=request.user)
        )

        return Response({
            "profile": self._get_profile(candidate),
            "profile_strength": self._calculate_profile_strength(candidate),
            "professional_highlights": self._get_professional_highlights(candidate),
            "profile_highlights": self._get_profile_highlights(candidate),
            "skill_competency": self._get_skill_competency(candidate),
            "experience": self._get_experience(candidate),
            "education": self._get_education(candidate),
            "certifications": self._get_certifications(candidate),
            "languages": self._get_languages(candidate),
        })


    def _get_profile(self, candidate):
        return {
            "id": candidate.id,
            "profile_image": candidate.profile_image.url if candidate.profile_image else None,
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "full_name": f"{candidate.first_name} {candidate.last_name}".strip(),
            "headline": candidate.headline,
            "about_me": candidate.about_me,
            "email": candidate.user.email,
            "phone": candidate.user.phone_number,
            "location": candidate.location,
            "linkedin": candidate.linkedin_url,
        }


    def _calculate_profile_strength(self, candidate):

        score = 0

        if candidate.profile_image:
            score += 10

        if candidate.first_name:
            score += 10

        if candidate.headline:
            score += 10

        if candidate.about_me:
            score += 10

        if candidate.location:
            score += 10

        if candidate.linkedin_url:
            score += 10

        if candidate.skills.exists():
            score += 15

        if candidate.educations.exists():
            score += 10

        if candidate.experiences.exists():
            score += 10

        if candidate.languages.exists():
            score += 5

        if score >= 90:
            status = "Excellent"
        elif score >= 70:
            status = "Good"
        elif score >= 50:
            status = "Average"
        else:
            status = "Beginner"

        return {
            "percentage": score,
            "status": status,
        }

 

    def _get_professional_highlights(self, candidate):
        return {
            "experience_years": candidate.total_experience,
            "highest_degree": candidate.highest_qualification,
            "total_certifications": candidate.certifications.count(),
            "total_skills": candidate.skills.count(),
        }

  

    def _get_profile_highlights(self, candidate):

        return [
            {
                "title": "Personal Information",
                "completed": bool(
                    candidate.first_name
                    and candidate.location
                    and candidate.user.email
                ),
            },
            {
                "title": "Experience",
                "completed": candidate.experiences.exists(),
            },
            {
                "title": "Skills",
                "completed": candidate.skills.exists(),
            },
            {
                "title": "Education",
                "completed": candidate.educations.exists(),
            },
            {
                "title": "Languages",
                "completed": candidate.languages.exists(),
            },
        ]



    def _get_skill_competency(self, candidate):

        data = []

        for skill in candidate.skills.all():

            rating = skill.proficiency or 10

            data.append({
                "id": skill.id,
                "skill": skill.skill_name,
                "rating": rating,
                "percentage": rating * 10,
            })

        return data


    def _get_experience(self, candidate):

        data = []

        for exp in candidate.experiences.all():
            data.append({
                "id": exp.id,
                "company": exp.company_name,
                "designation": exp.designation,
                "employment_type": exp.employment_type,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "currently_working": exp.currently_working,
                "description": exp.description,
            })

        return data



    def _get_education(self, candidate):

        data = []

        for edu in candidate.educations.all():
            data.append({
                "id": edu.id,
                "degree": edu.degree,
                "institution": edu.institution,
                "specialization": edu.specialization,
                "cgpa": edu.cgpa,
                "percentage": edu.percentage,
                "start_year": edu.start_year,
                "end_year": edu.end_year,
            })

        return data

   
    def _get_certifications(self, candidate):

        data = []

        for cert in candidate.certifications.all():
            data.append({
                "id": cert.id,
                "certificate_name": cert.certificate_name,
                "issuing_organization": cert.issuing_organization,
                "issue_date": cert.issue_date,
                "expiry_date": cert.expiry_date,
                "credential_url": cert.credential_url,
            })

        return data


    def _get_languages(self, candidate):

        data = []

        for lang in candidate.languages.all():
            data.append({
                "id": lang.id,
                "language": lang.language,
                "proficiency": lang.proficiency,
                "can_read": lang.can_read,
                "can_write": lang.can_write,
                "can_speak": lang.can_speak,
            })

        return data


class CandidateHeaderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            candidate = Candidate.objects.select_related("user").get(
                user=request.user
            )

            return api_response(
                True,
                "Header profile fetched successfully.",
                data={
                    "id": candidate.id,
                    "full_name": f"{candidate.first_name} {candidate.last_name}".strip(),
                    "first_name": candidate.first_name,
                    "last_name": candidate.last_name,
                    "email": candidate.user.email,
                    "role": candidate.user.role,
                    "profile_image": (
                        candidate.profile_image.url
                        if candidate.profile_image
                        else None
                    ),
                },
            )

        except Candidate.DoesNotExist:
            return api_response(
                False,
                "Candidate profile not found.",
                http_status=status.HTTP_404_NOT_FOUND,
            )


class RecruiterHeaderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            recruiter = Recruiter.objects.select_related("user").get(
                user=request.user
            )

            return api_response(
                True,
                "Recruiter header profile fetched successfully.",
                data={
                    "id": recruiter.id,
                    "full_name": recruiter.user.username,
                    "email": recruiter.user.email,
                    "role": recruiter.user.role,
                    "company_name": recruiter.company_name if hasattr(recruiter, "company_name") else None,
                    "profile_image": (
                        recruiter.profile_image.url
                        if recruiter.profile_image
                        else None
                    ),
                },
            )

        except Recruiter.DoesNotExist:
            return api_response(
                False,
                "Recruiter profile not found.",
                http_status=status.HTTP_404_NOT_FOUND,
            )


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