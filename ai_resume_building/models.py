from django.db import models
from django.contrib.auth.models import AbstractUser

class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    CANDIDATE = "CANDIDATE", "Candidate"
    EMPLOYER = "EMPLOYER", "Employer"


class User(AbstractUser):

    username = models.CharField(
        max_length=150,
        unique=True,
    )

    email = models.EmailField(
        unique=True,
    )

    role = models.CharField(
        max_length=20,
        choices=[
            ("ADMIN", "Admin"),
            ("CANDIDATE", "Candidate"),
            ("EMPLOYER", "Employer"),
        ],
        default="CANDIDATE",
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    is_email_verified = models.BooleanField(default=False)

    is_phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
    class Meta:
        db_table = "user"
    
    

class Candidate(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="candidate"
    )

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

    profile_picture = models.ImageField(
        upload_to="candidate/profile/",
        null=True,
        blank=True,
    )

    headline = models.CharField(max_length=200, blank=True)

    summary = models.TextField(blank=True)

    date_of_birth = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=20, blank=True)

    country = models.CharField(max_length=100, blank=True)

    state = models.CharField(max_length=100, blank=True)

    city = models.CharField(max_length=100, blank=True)

    address = models.TextField(blank=True)

    experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
    )

    education = models.TextField(blank=True)

    skills = models.TextField(blank=True)


    resume = models.FileField(
        upload_to="candidate/resume/",
        blank=True,
        null=True,
    )

    portfolio = models.URLField(blank=True)

    linkedin = models.URLField(blank=True)

    github = models.URLField(blank=True)

    expected_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    preferred_location = models.CharField(
        max_length=200,
        blank=True,
    )

    profile_completion = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate"


class Employer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employer"
    )

    company_name = models.CharField(max_length=255)

    company_logo = models.ImageField(
        upload_to="employer/logo/",
        blank=True,
        null=True,
    )

    company_email = models.EmailField()

    company_phone = models.CharField(max_length=15)

    company_website = models.URLField(blank=True)

    industry = models.CharField(max_length=100)

    company_size = models.CharField(max_length=100)

    founded_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    country = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    city = models.CharField(max_length=100)

    address = models.TextField()

    description = models.TextField(blank=True)

    linkedin = models.URLField(blank=True)

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "employer"




class Certification(models.Model):

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="certifications"
    )

    certification_name = models.CharField(
        max_length=255
    )

    issuing_organization = models.CharField(
        max_length=255
    )

    issue_date = models.DateField()

    expiry_date = models.DateField(
        null=True,
        blank=True
    )

    credential_id = models.CharField(
        max_length=150,
        blank=True
    )

    credential_url = models.URLField(
        blank=True
    )

    certificate_file = models.FileField(
        upload_to="candidate/certifications/",
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "certification"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.certification_name} - {self.candidate.first_name}"
    


import uuid
from django.db import models


class ResumeShare(models.Model):
    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name="resume_share"
    )

    share_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    is_public = models.BooleanField(
        default=False
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "resume_share"

    def __str__(self):
        return f"{self.candidate.user.email}"


class SocialLink(models.Model):

    PLATFORM_CHOICES = (
        ("LINKEDIN", "LinkedIn"),
        ("GITHUB", "GitHub"),
        ("PORTFOLIO", "Portfolio"),
        ("LEETCODE", "LeetCode"),
        ("HACKERRANK", "HackerRank"),
        ("CODECHEF", "CodeChef"),
        ("OTHER", "Other"),
    )

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="social_links"
    )

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES
    )

    profile_url = models.URLField()

    username = models.CharField(
        max_length=100,
        blank=True
    )

    is_primary = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "social_link"
        ordering = ["platform"]

    def __str__(self):
        return f"{self.candidate.user.email} - {self.platform}"