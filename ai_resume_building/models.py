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
    
  