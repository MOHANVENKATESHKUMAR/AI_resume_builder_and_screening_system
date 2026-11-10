
import logging
import secrets

from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction

from rest_framework.response import Response
from rest_framework import status

from .models import OTPPurpose, OTP


logger = logging.getLogger(__name__)

OTP_VALIDITY_MINUTES = 5


# ============================================================
# GENERATE OTP
# ============================================================

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


# ============================================================
# API RESPONSE
# ============================================================

def api_response(
    success,
    message=None,
    http_status=status.HTTP_200_OK,
    **fields
):
    body = {
        "success": success
    }

    if message is not None:
        body["message"] = message

    body.update(fields)

    return Response(body, status=http_status)


# ============================================================
# SEND OTP EMAIL
# ============================================================

def send_otp_email(email, otp, subject):

    try:

        context = {
            "otp": otp,
            "minutes": OTP_VALIDITY_MINUTES,
        }

        html_content = render_to_string(
            "emails/signup_otp.html",
            context
        )

        message = EmailMultiAlternatives(
            subject=subject,
            body=(
                f"Your OTP is {otp}. "
                f"It is valid for {OTP_VALIDITY_MINUTES} minutes."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )

        message.attach_alternative(
            html_content,
            "text/html"
        )

        message.send(fail_silently=False)

        return True

    except Exception:

        logger.exception("Failed to send OTP email")

        return False


# ============================================================
# BUILD OTP LOOKUP
# ============================================================

def get_otp_lookup(method, value, purpose):

    lookup = {
        "purpose": purpose,
    }

    if method == "email":

        lookup["email"] = value

        lookup["phone_number__isnull"] = True

    elif method == "sms":

        lookup["phone_number"] = value

        lookup["email__isnull"] = True

    else:

        raise ValueError("Invalid OTP method")

    return lookup


# ============================================================
# ISSUE OTP
# ============================================================

def issue_otp(method, value, purpose):

    otp_value = generate_otp()

    expires_at = (
        timezone.now()
        + timedelta(minutes=OTP_VALIDITY_MINUTES)
    )

    lookup = get_otp_lookup(
        method=method,
        value=value,
        purpose=purpose,
    )

    defaults = {
        "otp": otp_value,
        "expires_at": expires_at,
        "is_verified": False,
        "is_used": False,
    }

    with transaction.atomic():

        OTP.objects.update_or_create(
            **lookup,
            defaults=defaults
        )

    return otp_value


# ============================================================
# GET VALID OTP
# ============================================================

def get_valid_otp(
    method,
    value,
    purpose,
    otp_value
):

    lookup = get_otp_lookup(
        method=method,
        value=value,
        purpose=purpose,
    )

    lookup.update({
        "is_verified": False,
        "is_used": False,
    })

    otp_obj = (
        OTP.objects.filter(**lookup)
        .order_by("-created_at")
        .first()
    )

    if otp_obj is None:

        return None, "Invalid OTP."

    if otp_obj.expires_at <= timezone.now():

        return None, "OTP has expired."

    if not secrets.compare_digest(
        str(otp_obj.otp),
        str(otp_value)
    ):

        return None, "Invalid OTP."

    return otp_obj, None
