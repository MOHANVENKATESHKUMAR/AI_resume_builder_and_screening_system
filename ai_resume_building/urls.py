from django.urls import path

from ai_resume_building.serializers import SocialLinkListCreateAPIView, SocialLinkRetrieveUpdateDestroyAPIView
from .views import CertificationListCreateAPIView, CertificationRetrieveUpdateDestroyAPIView, DashboardAPIView, GoogleLoginAPIView, LinkedInLoginAPIView, LoginAPIView, LogoutAPIView, PublicResumeAPIView, ResumeShareAPIView

urlpatterns = [
    path("employer/dashboard/",DashboardAPIView.as_view(),name="dashboard",),
    path("certifications/",CertificationListCreateAPIView.as_view(),name="certification-list-create",),
    path("certifications/<int:pk>/",CertificationRetrieveUpdateDestroyAPIView.as_view(),name="certification-detail",),
    path("google/login/",GoogleLoginAPIView.as_view(),name="google-login",),
    path("linkedin/login/",LinkedInLoginAPIView.as_view(),name="linkedin-login",),
    path("login/", LoginAPIView.as_view(), name="login"),
    path(
        "resume/share/",
        ResumeShareAPIView.as_view(),
        name="resume-share",
    ),

    path(
        "resume/share/<uuid:token>/",
        PublicResumeAPIView.as_view(),
        name="public-resume",
    ),
    path(
        "social-links/",
        SocialLinkListCreateAPIView.as_view(),
        name="social-link-list-create",
    ),

    path(
        "social-links/<int:pk>/",
        SocialLinkRetrieveUpdateDestroyAPIView.as_view(),
        name="social-link-detail",
    ),
     path(
        "logout/",
        LogoutAPIView.as_view(),
        name="logout",
    ),
]



