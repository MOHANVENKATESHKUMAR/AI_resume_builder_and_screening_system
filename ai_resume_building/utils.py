from asyncio.log import logger
import random
import string
import secrets
from datetime import timedelta

from django.conf import settings

from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPPurpose, OTP, PasswordResetToken



#for login success page 
def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


#for generate otp

def generate_otp():
    return f"{random.randint(100000, 999999)}"

OTP_VALIDITY_MINUTES = 5
FRONTEND_RESET_PASSWORD_URL = getattr(
    settings,
    "FRONTEND_RESET_PASSWORD_URL",
    "http://localhost:5173/Resume-builder/login/createpassword",
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def api_response(success, message=None, http_status=status.HTTP_200_OK, **fields):
   
    body = {"success": success}
    if message is not None:
        body["message"] = message
    body.update(fields)
    return Response(body, status=http_status)


def send_otp_email(email, otp, subject):
    
    try:
        send_mail(
            subject=subject,
            message=f"Your OTP is {otp}. It is valid for {OTP_VALIDITY_MINUTES} minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send OTP email to %s", email)


def issue_otp(email, purpose):
    
    otp = generate_otp()
    OTP.objects.update_or_create(
        email=email,
        purpose=purpose,
        defaults={
            "otp": otp,
            "expires_at": timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES),
            "is_verified": False,
        },
    )
    return otp


def get_valid_otp(email, purpose, otp_value):
    
    otp_obj = (
        OTP.objects.filter(email=email, purpose=purpose, is_verified=False)
        .order_by("-created_at")
        .first()
    )

    if otp_obj is None:
        return None, "Invalid OTP."

    if otp_obj.expires_at < timezone.now():
        return None, "OTP has expired."

    if not secrets.compare_digest(otp_obj.otp, otp_value):
        return None, "Invalid OTP."

    return otp_obj, None

