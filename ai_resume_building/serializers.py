from rest_framework import serializers
from .models import Certification


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = "__all__"
        read_only_fields = ["id", "candidate", "created_at", "updated_at"]





class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)




class LinkedInLoginSerializer(serializers.Serializer):
    code = serializers.CharField()