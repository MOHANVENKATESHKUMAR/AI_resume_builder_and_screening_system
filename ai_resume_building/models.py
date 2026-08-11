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

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    headline = models.CharField(max_length=255, blank=True)
    about_me = models.TextField(blank=True)

    profile_image = models.ImageField(
        upload_to="candidate/profile/",
        blank=True,
        null=True,
    )

    

    # Contact
    
    alternate_phone = models.CharField(max_length=20, blank=True)

    # Location
    location = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Social Links
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    # Career
    current_company = models.CharField(max_length=255, blank=True)
    current_designation = models.CharField(max_length=255, blank=True)
    total_experience = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
    )

    highest_qualification = models.CharField(max_length=255, blank=True)

    # Scores
    profile_strength = models.PositiveSmallIntegerField(default=0)
    ats_score = models.PositiveSmallIntegerField(default=0)

    # Active Resume Version
    active_resume = models.ForeignKey(
        "ResumeParsedData",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_candidates",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate"

    def __str__(self):
        return self.user.email

class Recruiter(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)

    recruiter_name = models.CharField(
        max_length=150,
        help_text="Display name or recruiter name",
    )

    designation = models.CharField(max_length=150)

    company_name = models.CharField(max_length=200)

    company_website = models.URLField(blank=True)

    company_location = models.CharField(max_length=200)

    industry_type = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recruiter"

    def __str__(self):
        return self.company_name
    
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


# while registering and parsing the resume we will store the parsed data in this model and also keep the history of all the parsed data for a candidate
class ResumeParsedData(models.Model):

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="resume_versions",
    )

    version = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)

    resume_file = models.FileField(
        upload_to="candidate/resume/history/"
    )

    # Backup Personal Information
    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100, blank=True)

    headline = models.CharField(max_length=255, blank=True)

    about_me = models.TextField(blank=True)

    email = models.EmailField(blank=True)

    phone = models.CharField(max_length=20, blank=True)

    alternate_phone = models.CharField(max_length=20, blank=True)

    location = models.CharField(max_length=255, blank=True)

    city = models.CharField(max_length=100, blank=True)

    state = models.CharField(max_length=100, blank=True)

    country = models.CharField(max_length=100, blank=True)

    linkedin_url = models.URLField(blank=True)

    github_url = models.URLField(blank=True)

    portfolio_url = models.URLField(blank=True)

    website_url = models.URLField(blank=True)

    current_company = models.CharField(max_length=255, blank=True)

    current_designation = models.CharField(max_length=255, blank=True)

    total_experience = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
    )

    highest_qualification = models.CharField(
        max_length=255,
        blank=True,
    )

    profile_strength = models.PositiveSmallIntegerField(default=0)

    ats_score = models.PositiveSmallIntegerField(default=0)

    parser_status = models.CharField(
        max_length=30,
        default="PENDING",
    )

    parser_version = models.CharField(
        max_length=30,
        default="1.0",
    )

    raw_resume_text = models.TextField(blank=True)

    extra_data = models.JSONField(
        default=dict,
        blank=True,
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resume_parsed_data"

        ordering = ["-version"]
        indexes = [
        models.Index(fields=["candidate"]),
        models.Index(fields=["candidate", "is_active"]),
    ]

class CandidateSkill(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="skills",
    )

    resume_version = models.ForeignKey(
        ResumeParsedData,
        on_delete=models.CASCADE,
        related_name="skills",
        null=True,
        blank=True,
    )

    skill_name = models.CharField(max_length=150)

    proficiency = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10),
        ],
    )

    years_of_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
    )

    is_primary = models.BooleanField(default=False)

    is_from_resume = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_skill"
        ordering = ["skill_name"]
        indexes = [
        models.Index(fields=["candidate"]),
        models.Index(fields=["resume_version"]),
        models.Index(fields=["skill_name"]),
    ]

    def __str__(self):
        return self.skill_name


class CandidateEducation(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="educations",
    )

    resume_version = models.ForeignKey(
        ResumeParsedData,
        on_delete=models.CASCADE,
        related_name="educations",
        null=True,
        blank=True,
    )

    degree = models.CharField(max_length=255)

    specialization = models.CharField(
        max_length=255,
        blank=True,
    )

    institution = models.CharField(max_length=255)

    board = models.CharField(
        max_length=100,
        blank=True,
    )

    cgpa = models.CharField(
        max_length=20,
        blank=True,
    )

    percentage = models.CharField(
        max_length=20,
        blank=True,
    )

    start_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    end_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    is_from_resume = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_education"
        ordering = ["-end_year"]
        indexes = [
        models.Index(fields=["candidate"]),
        models.Index(fields=["resume_version"]),
        models.Index(fields=["degree"]),
    ]

    def __str__(self):
        return self.degree



class CandidateExperience(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="experiences",
    )
#.msfc
    resume_version = models.ForeignKey(
        ResumeParsedData,
        on_delete=models.CASCADE,
        related_name="experiences",
        null=True,
        blank=True,
    )

    company_name = models.CharField(max_length=255)

    designation = models.CharField(max_length=255)

    employment_type = models.CharField(
        max_length=100,
        blank=True,
    )

    location = models.CharField(
        max_length=255,
        blank=True,
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    currently_working = models.BooleanField(default=False)

    description = models.TextField(blank=True)

    is_from_resume = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_experience"
        ordering = ["-start_date"]
        indexes = [
        models.Index(fields=["candidate"]),
        models.Index(fields=["resume_version"]),
        models.Index(fields=["company_name"]),
    ]

    def __str__(self):
        return self.designation


class CandidateCertification(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="certifications",
    )

    resume_version = models.ForeignKey(
        ResumeParsedData,
        on_delete=models.CASCADE,
        related_name="certifications",
        null=True,
        blank=True,
    )

    certificate_name = models.CharField(max_length=255)

    issuing_organization = models.CharField(
        max_length=255,
    )

    credential_id = models.CharField(
        max_length=255,
        blank=True,
    )

    credential_url = models.URLField(blank=True)

    issue_date = models.DateField(
        null=True,
        blank=True,
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
    )

    is_from_resume = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_certification"
        ordering = ["certificate_name"]
        indexes = [
        models.Index(fields=["candidate"]),
        models.Index(fields=["resume_version"]),
        models.Index(fields=["certificate_name"]),
    ]

    def __str__(self):
        return self.certificate_name


class CandidateLanguage(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="languages",
    )

    resume_version = models.ForeignKey(
        ResumeParsedData,
        on_delete=models.CASCADE,
        related_name="languages",
        null=True,
        blank=True,
    )

    language = models.CharField(max_length=100)

    proficiency = models.CharField(
        max_length=50,
        blank=True,
    )

    can_read = models.BooleanField(default=True)

    can_write = models.BooleanField(default=True)

    can_speak = models.BooleanField(default=True)

    is_from_resume = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_language"
        ordering = ["language"]
        indexes = [
        models.Index(fields=["candidate"]),
        models.Index(fields=["resume_version"]),
        models.Index(fields=["language"]),
    ]

    def __str__(self):
        return self.language