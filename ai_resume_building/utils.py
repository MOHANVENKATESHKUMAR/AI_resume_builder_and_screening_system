
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
MAX_OTP_ATTEMPTS = 5


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
# GENERATE OTP
# ============================================================

def generate_otp(method):

    if method == "sms":
        return "123456"

    return str(secrets.randbelow(900000) + 100000)


# ============================================================
# SEND EMAIL OTP
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
# SEND SMS OTP
# ============================================================

def send_otp_sms(phone_number, otp):

    # DEVELOPMENT ONLY:
    # This simulates SMS delivery.
    # No actual SMS is sent.

    logger.info(
        "Development SMS OTP generated for %s",
        phone_number
    )

    return True


# ============================================================
# BUILD OTP LOOKUP
# ============================================================
def get_otp_lookup(method, value, purpose):

    lookup = {
        "purpose": purpose,
    }

    if method == "email":

        lookup["email"] = value
        lookup["phone_number"] = None

    elif method == "sms":

        lookup["phone_number"] = value
        lookup["email"] = None

    else:

        raise ValueError("Invalid OTP method")

    return lookup

# ============================================================
# ISSUE OTP
# ============================================================

def issue_otp(method, value, purpose):

    otp_value = generate_otp(method)

    expires_at = (
        timezone.now()
        + timedelta(minutes=OTP_VALIDITY_MINUTES)
    )

    lookup = get_otp_lookup(
        method=method,
        value=value,
        purpose=purpose,
    )

    with transaction.atomic():

        # Invalidate previous OTPs for this contact and purpose.

        OTP.objects.filter(
            **lookup,
            is_used=False,
        ).update(is_used=True)

        # Create a fresh OTP.

        OTP.objects.create(
            **lookup,
            otp=otp_value,
            expires_at=expires_at,
        )

    return otp_value


# ============================================================
# GET VALID OTP
# ============================================================

def get_valid_otp(
    method,
    value,
    purpose,
    otp_value,
):

    lookup = get_otp_lookup(
        method=method,
        value=value,
        purpose=purpose,
    )

    with transaction.atomic():

        otp_obj = (
            OTP.objects.select_for_update()
            .filter(
                **lookup,
                is_verified=False,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if otp_obj is None:

            return None, "Invalid OTP."

        if otp_obj.expires_at <= timezone.now():

            return None, "OTP has expired."

        if otp_obj.attempts >= MAX_OTP_ATTEMPTS:

            otp_obj.is_used = True

            otp_obj.save(update_fields=["is_used"])

            return None, "Maximum OTP attempts exceeded."

        if not secrets.compare_digest(
            str(otp_obj.otp),
            str(otp_value),
        ):

            otp_obj.attempts += 1

            if otp_obj.attempts >= MAX_OTP_ATTEMPTS:
                otp_obj.is_used = True

            otp_obj.save(
                update_fields=["attempts", "is_used"]
            )

            return None, "Invalid OTP."

        return otp_obj, None