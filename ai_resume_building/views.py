from django.shortcuts import render

from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated , AllowAny

from .models import Candidate
from rest_framework import viewsets

from .models import Certification
from .serializers import CertificationSerializer
from google.oauth2 import id_token
from google.auth.transport import requests

from django.conf import settings

from rest_framework import status, generics
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import GoogleLoginSerializer



class DashboardAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        total_candidates = Candidate.objects.count()

        male_candidates = Candidate.objects.filter(gender="Male").count()

        female_candidates = Candidate.objects.filter(gender="Female").count()

        experienced_candidates = Candidate.objects.filter(
            experience__gt=0
        ).count()

        freshers = Candidate.objects.filter(
            experience=0
        ).count()

        experience_distribution = (
            Candidate.objects
            .values("experience")
            .annotate(count=Count("id"))
            .order_by("experience")
        )

        return Response({
            "total_candidates": total_candidates,
            "male_candidates": male_candidates,
            "female_candidates": female_candidates,
            "experienced_candidates": experienced_candidates,
            "freshers": freshers,
            "experience_distribution": experience_distribution,
        })
    


from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Certification
from .serializers import CertificationSerializer


class CertificationListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CertificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        canditate= Candidate.objects.first()
        return Certification.objects.filter(
            candidate__user=canditate.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        canditate= Candidate.objects.first()
        serializer.save(
            candidate=canditate
        )


class CertificationRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = CertificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        canditate= Candidate.objects.first()
        return Certification.objects.filter(
            candidate__user=canditate.user
        )
    




class GoogleLoginAPIView(generics.GenericAPIView):
    serializer_class = GoogleLoginSerializer
    permission_classes=[AllowAny]

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["id_token"]

        try:
            google_user = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )

        except Exception:
            return Response(
                {"message": "Invalid Google Token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = google_user["email"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": google_user.get("given_name", ""),
                "last_name": google_user.get("family_name", ""),
                "is_email_verified": True,
            },
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login Successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                },
            }
        )
    

from .serializers import LinkedInLoginSerializer

class LinkedInLoginAPIView(generics.GenericAPIView):

    serializer_class = LinkedInLoginSerializer

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]

        token_response = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            },
        )

        if token_response.status_code != 200:
            return Response(
                {"message": "Unable to authenticate"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = token_response.json()["access_token"]

        profile = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
        ).json()

        email = profile["email"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": profile.get("given_name", ""),
                "last_name": profile.get("family_name", ""),
                "is_email_verified": True,
            },
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
            }
        )
    


from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import ResumeShare
from .serializers import ResumeShareSerializer


class ResumeShareAPIView(generics.RetrieveUpdateAPIView):

    serializer_class = ResumeShareSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):

        candidate = self.request.user.candidate

        share, created = ResumeShare.objects.get_or_create(
            candidate=candidate
        )

        return share


from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class PublicResumeAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, token):

        try:

            share = ResumeShare.objects.get(
                share_token=token,
                is_public=True
            )

        except ResumeShare.DoesNotExist:

            return Response(
                {"message": "Invalid Share Link"},
                status=status.HTTP_404_NOT_FOUND
            )

        if share.expires_at:

            if share.expires_at < timezone.now():

                return Response(
                    {"message": "Link Expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        candidate = share.candidate

        return Response({
            "name": candidate.first_name + " " + candidate.last_name,
            "headline": candidate.headline,
            "summary": candidate.summary,
            "skills": candidate.skills,
            "experience": candidate.experience,
            "education": candidate.education,
            "portfolio": candidate.portfolio,
            "linkedin": candidate.linkedin,
            "github": candidate.github,
        })
    

from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer


class LoginAPIView(generics.GenericAPIView):
    permission_classes=[AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(
            request=request,
            username=email,  # USERNAME_FIELD = "email"
            password=password,
        )

        if not user:
            return Response(
                {"message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                },
            }
        )
    

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LogoutSerializer


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "message": "Logout successful."
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {
                    "message": "Invalid refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )