import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import hashlib
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(
            email=email,
            password=password,
            **extra_fields
        )

class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    CANDIDATE = "CANDIDATE", "Candidate"
    EMPLOYER = "EMPLOYER", "Employer"

class User(AbstractUser):

    username = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    email = models.EmailField(unique=True)

    objects = UserManager()

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CANDIDATE,
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "user"

    def __str__(self):
        return self.email
 
from django.db import models
from django.conf import settings


class Candidate(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate",
    )

    full_name = models.CharField(max_length=255)

    mobile = models.CharField(max_length=15)

    degree = models.CharField(max_length=50)

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
        ("Prefer not to say", "Prefer not to say"),
    ]

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
    )

    dob = models.DateField()

    class Meta:
        db_table = "candidate"

    def __str__(self):
        return self.user.email


class TermsAcceptance(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="terms_acceptances",
    )

    terms_accepted = models.BooleanField(default=False)

    privacy_policy_accepted = models.BooleanField(default=False)

    terms_version = models.CharField(
        max_length=20,
        default="1.0",
    )

    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "terms_acceptance"

    def __str__(self):
        return self.user.email   


class Recruiter(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter",
    )

    full_name = models.CharField(max_length=255)

    recruiter_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    designation = models.CharField(max_length=100)

    gender = models.CharField(
        max_length=20,
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
            ("Other", "Other"),
            ("Prefer not to say", "Prefer not to say"),
        ],
    )

    company_name = models.CharField(max_length=255)

    company_website = models.URLField(max_length=500)

    company_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    industry_type = models.CharField(max_length=150)

    class Meta:
        db_table = "recruiter"

    def __str__(self):
        return self.full_name


class OTPPurpose(models.TextChoices):
    SIGNUP = "SIGNUP", "Signup"
    LOGIN = "LOGIN", "Login"
    FORGOT_PASSWORD = "FORGOT_PASSWORD", "Forgot Password"


class OTP(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps",
        null=True,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
        null=True,
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    otp = models.CharField(max_length=6)

    purpose = models.CharField(
        max_length=20,
        choices=OTPPurpose.choices,
    )

    expires_at = models.DateTimeField()

    is_verified = models.BooleanField(default=False)

    is_used = models.BooleanField(default=False)

    attempts = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["email", "purpose"]),
            models.Index(fields=["phone_number", "purpose"]),
        ]

    def is_valid(self):
        return (
            not self.is_verified
            and not self.is_used
            and self.attempts < 5
            and self.expires_at > timezone.now()
        )