from rest_framework import serializers
from .models import Certification
from django.urls import reverse


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = "__all__"
        read_only_fields = ["id", "candidate", "created_at", "updated_at"]





class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)




class LinkedInLoginSerializer(serializers.Serializer):
    code = serializers.CharField()

from rest_framework import serializers
from .models import ResumeShare


class ResumeShareSerializer(serializers.ModelSerializer):

    share_url = serializers.SerializerMethodField()

    class Meta:
        model = ResumeShare
class ResumeShareSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = ResumeShare
        fields = [
            "id",
            "share_url",
            "share_token",
            "is_public",
            "expires_at",
        ]
        read_only_fields = [
            "share_token",
        ]


    def get_share_url(self, obj):
        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                reverse(
                    "public-resume",
                    kwargs={"token": obj.share_token},
                )
            )

        return None
    


from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


from rest_framework import serializers
from .models import SocialLink


class SocialLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = SocialLink
        fields = "__all__"
        read_only_fields = [
            "id",
            "candidate",
            "created_at",
            "updated_at",
        ]

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import SocialLink
from .serializers import SocialLinkSerializer


class SocialLinkListCreateAPIView(generics.ListCreateAPIView):

    serializer_class = SocialLinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SocialLink.objects.filter(
            candidate=self.request.user.candidate
        ).order_by("platform")

    def perform_create(self, serializer):
        serializer.save(
            candidate=self.request.user.candidate
        )


class SocialLinkRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = SocialLinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SocialLink.objects.filter(
            candidate=self.request.user.candidate
        )
    
from rest_framework import serializers


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()