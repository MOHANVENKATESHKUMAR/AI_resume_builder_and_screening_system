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






# class GoogleLoginAPIView(generics.GenericAPIView):
#     serializer_class = GoogleLoginSerializer
#     permission_classes=[AllowAny]

#     def post(self, request):

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         token = serializer.validated_data["id_token"]

#         try:
#             google_user = id_token.verify_oauth2_token(
#                 token,
#                 requests.Request(),
#                 settings.GOOGLE_CLIENT_ID,
#             )

#         except Exception:
#             return Response(
#                 {"message": "Invalid Google Token"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         email = google_user["email"]

#         user, created = User.objects.get_or_create(
#             email=email,
#             defaults={
#                 "username": email.split("@")[0],
#                 "first_name": google_user.get("given_name", ""),
#                 "last_name": google_user.get("family_name", ""),
#                 "is_email_verified": True,
#             },
#         )

#         refresh = RefreshToken.for_user(user)

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

# class LinkedInLoginAPIView(generics.GenericAPIView):

#     serializer_class = LinkedInLoginSerializer

#     def post(self, request):

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         code = serializer.validated_data["code"]

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

#         if token_response.status_code != 200:
#             return Response(
#                 {"message": "Unable to authenticate"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         access_token = token_response.json()["access_token"]

#         profile = requests.get(
#             "https://api.linkedin.com/v2/userinfo",
#             headers={
#                 "Authorization": f"Bearer {access_token}"
#             },
#         ).json()

#         email = profile["email"]

#         user, created = User.objects.get_or_create(
#             email=email,
#             defaults={
#                 "username": email.split("@")[0],
#                 "first_name": profile.get("given_name", ""),
#                 "last_name": profile.get("family_name", ""),
#                 "is_email_verified": True,
#             },
#         )

#         refresh = RefreshToken.for_user(user)

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
    
