from django.urls import path
from .views import CertificationListCreateAPIView, CertificationRetrieveUpdateDestroyAPIView, DashboardAPIView, GoogleLoginAPIView, LinkedInLoginAPIView

urlpatterns = [
    path("employer/dashboard/",DashboardAPIView.as_view(),name="dashboard",),
    path("certifications/",CertificationListCreateAPIView.as_view(),name="certification-list-create",),
    path("certifications/<int:pk>/",CertificationRetrieveUpdateDestroyAPIView.as_view(),name="certification-detail",),
    path("google/login/",GoogleLoginAPIView.as_view(),name="google-login",),
    path("linkedin/login/",LinkedInLoginAPIView.as_view(),name="linkedin-login",)


]