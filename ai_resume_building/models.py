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

    degree = models.CharField(max_length=150)

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

    full_name = models.CharField(max_length=150)

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
    



class ResumeStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class ResumeSource(models.TextChoices):
    UPLOAD = "UPLOAD", "Upload"
    LINKEDIN = "LINKEDIN", "LinkedIn"
    INDEED = "INDEED", "Indeed"
    MANUAL = "MANUAL", "Manual"


class ParserType(models.TextChoices):
    SPACY = "SPACY", "spaCy"
    OCR = "OCR", "OCR"
    LLM = "LLM", "LLM"
    HYBRID = "HYBRID", "Hybrid"


class OCRProvider(models.TextChoices):
    TESSERACT = "TESSERACT", "Tesseract"
    PADDLEOCR = "PADDLEOCR", "PaddleOCR"
    EASYOCR = "EASYOCR", "EasyOCR"
    NONE = "NONE", "None"


def resume_upload_path(instance, filename):
    extension = filename.split(".")[-1]
    return (
        f"candidate/resume/"
        f"{instance.candidate.id}/"
        f"{uuid.uuid4().hex}.{extension}"
    )
 

class Resume(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="resumes",
    )

    resume_file = models.FileField(
        upload_to="candidate/resume/",
    )

    original_file_name = models.CharField(
        max_length=255,
    )

    file_size = models.BigIntegerField()

    status = models.CharField(
        max_length=20,
        choices=ResumeStatus.choices,
        default=ResumeStatus.PENDING,
    )

    extracted_text = models.TextField(
        blank=True,
    )

    parser_errors = models.JSONField(
        default=list,
        blank=True,
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "resume"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_file_name
    

class ResumePersonalInformation(models.Model):
    resume = models.OneToOneField(
        Resume,
        on_delete=models.CASCADE,
        related_name="personal_information",
    )

    first_name = models.CharField(
        max_length=100,
        blank=True,
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    alternate_phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    profile_summary = models.TextField(
        blank=True,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=50,
        blank=True,
    )

    nationality = models.CharField(
        max_length=100,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    country = models.CharField(
        max_length=100,
        blank=True,
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
    )

    linkedin_url = models.URLField(
        blank=True,
    )

    github_url = models.URLField(
        blank=True,
    )

    portfolio_url = models.URLField(
        blank=True,
    )

    website_url = models.URLField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "resume_personal_information"

    def __str__(self):
        return self.full_name or f"Resume {self.resume_id}"
    

class ResumeEducation(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="educations",
    )

    degree = models.CharField(
        max_length=255,
    )

    field_of_study = models.CharField(
        max_length=255,
        blank=True,
    )

    institution_name = models.CharField(
        max_length=255,
    )

    university = models.CharField(
        max_length=255,
        blank=True,
    )

    board = models.CharField(
        max_length=255,
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

    is_current = models.BooleanField(
        default=False,
    )

    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    grade = models.CharField(
        max_length=50,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    display_order = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "resume_education"
        ordering = ["display_order", "-end_date"]

    def __str__(self):
        return f"{self.degree} - {self.institution_name}"
    

class EmploymentType(models.TextChoices):
    FULL_TIME = "FULL_TIME", "Full Time"
    PART_TIME = "PART_TIME", "Part Time"
    CONTRACT = "CONTRACT", "Contract"
    INTERNSHIP = "INTERNSHIP", "Internship"
    FREELANCE = "FREELANCE", "Freelance"
    TEMPORARY = "TEMPORARY", "Temporary"
    APPRENTICESHIP = "APPRENTICESHIP", "Apprenticeship"
    
class ResumeWorkExperience(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="work_experiences",
    )

    company_name = models.CharField(
        max_length=255,
    )

    designation = models.CharField(
        max_length=255,
    )

    employment_type = models.CharField(
        max_length=30,
        choices=EmploymentType.choices,
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

    is_current = models.BooleanField(
        default=False,
    )

    responsibilities = models.JSONField(
        default=list,
        blank=True,
    )

    achievements = models.JSONField(
        default=list,
        blank=True,
    )

    technologies = models.JSONField(
        default=list,
        blank=True,
    )

    skills_used = models.JSONField(
        default=list,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    display_order = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "resume_work_experience"
        ordering = ["display_order", "-start_date"]

    def __str__(self):
        return f"{self.designation} - {self.company_name}"


class SkillCategory(models.TextChoices):
    TECHNICAL = "TECHNICAL", "Technical"
    SOFT = "SOFT", "Soft Skill"
    LANGUAGE = "LANGUAGE", "Programming Language"
    FRAMEWORK = "FRAMEWORK", "Framework"
    DATABASE = "DATABASE", "Database"
    TOOL = "TOOL", "Tool"
    CLOUD = "CLOUD", "Cloud"
    OTHER = "OTHER", "Other"


class ProficiencyLevel(models.TextChoices):
    BEGINNER = "BEGINNER", "Beginner"
    INTERMEDIATE = "INTERMEDIATE", "Intermediate"
    ADVANCED = "ADVANCED", "Advanced"
    EXPERT = "EXPERT", "Expert"

class ResumeSkill(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="skills",
    )

    skill_name = models.CharField(
        max_length=150,
    )

    category = models.CharField(
        max_length=30,
        choices=SkillCategory.choices,
        default=SkillCategory.OTHER,
    )

    proficiency = models.CharField(
        max_length=30,
        choices=ProficiencyLevel.choices,
        blank=True,
    )

    years_of_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    last_used = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Year last used (e.g. 2026)",
    )

    display_order = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "resume_skill"
        ordering = ["display_order", "skill_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["resume", "skill_name"],
                name="unique_resume_skill",
            )
        ]

    def __str__(self):
        return self.skill_name

class ResumeProject(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    project_title = models.CharField(max_length=255)

    role = models.CharField(
        max_length=255,
        blank=True,
    )

    organization = models.CharField(
        max_length=255,
        blank=True,
    )

    technologies = models.JSONField(
        default=list,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    responsibilities = models.JSONField(
        default=list,
        blank=True,
    )

    project_url = models.URLField(
        blank=True,
    )

    github_url = models.URLField(
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

    display_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_project"
        ordering = ["display_order", "-start_date"]

    def __str__(self):
        return self.project_title


class ResumeCertification(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="certifications",
    )

    certification_name = models.CharField(max_length=255)

    issuing_organization = models.CharField(
        max_length=255,
        blank=True,
    )

    issue_date = models.DateField(
        null=True,
        blank=True,
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
    )

    credential_id = models.CharField(
        max_length=255,
        blank=True,
    )

    credential_url = models.URLField(
        blank=True,
    )

    display_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_certification"
        ordering = ["display_order", "-issue_date"]

    def __str__(self):
        return self.certification_name
    

class LanguageProficiency(models.TextChoices):
    BASIC = "BASIC", "Basic"
    INTERMEDIATE = "INTERMEDIATE", "Intermediate"
    FLUENT = "FLUENT", "Fluent"
    NATIVE = "NATIVE", "Native"


class ResumeLanguage(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="languages",
    )

    language = models.CharField(max_length=100)

    proficiency = models.CharField(
        max_length=30,
        choices=LanguageProficiency.choices,
        default=LanguageProficiency.BASIC,
    )

    can_read = models.BooleanField(default=True)

    can_write = models.BooleanField(default=True)

    can_speak = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_language"
        ordering = ["display_order", "language"]

    def __str__(self):
        return self.language


class ResumeAchievement(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="achievements",
    )

    title = models.CharField(max_length=255)

    organization = models.CharField(
        max_length=255,
        blank=True,
    )

    achievement_date = models.DateField(
        null=True,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    display_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume_achievement"

    def __str__(self):
        return self.title
    

class ResumeCustomSection(models.Model):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="custom_sections",
    )

    section_name = models.CharField(
        max_length=255,
    )

    section_data = models.JSONField(
        default=dict,
        blank=True,
    )

    display_order = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "resume_custom_section"
        ordering = ["display_order"]

    def __str__(self):
        return self.section_name