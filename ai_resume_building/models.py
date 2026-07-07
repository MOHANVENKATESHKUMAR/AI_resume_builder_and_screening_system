import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    CANDIDATE = "CANDIDATE", "Candidate"
    EMPLOYER = "EMPLOYER", "Employer"


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CANDIDATE,
    )

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "user"

    def __str__(self):
        return self.email


class Candidate(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)

    profile_image = models.ImageField(
        upload_to="candidate/profile/",
        blank=True,
        null=True,
    )

    resume = models.FileField(
        upload_to="candidate/resume/",
        blank=True,
        null=True,
    )

    profile_summary = models.TextField(blank=True, null=True)
    current_job_title = models.CharField(max_length=150, blank=True)
    current_company = models.CharField(max_length=150, blank=True)

    years_of_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
    )

    current_location = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate"

    def __str__(self):
        return self.user.email


class OTPPurpose(models.TextChoices):
    SIGNUP = "SIGNUP", "Signup"
    LOGIN = "LOGIN", "Login"
    FORGOT_PASSWORD = "FORGOT_PASSWORD", "Forgot Password"


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=OTPPurpose.choices)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp"
        # Every OTP send/verify request filters on this pair — index it.
        indexes = [
            models.Index(fields=["email", "purpose"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} - {self.purpose}"

    def is_valid(self):
        return not self.is_verified and self.expires_at > timezone.now()


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_token"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()