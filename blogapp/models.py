from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .validators import validate_file_size


# ---------------- USER MODEL ----------------
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# ---------------- POST MODEL ----------------
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(
        upload_to='post_images/',
        blank=True,
        null=True,
        validators=[validate_file_size]  # 5MB limit
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ---------------- MEDIA FILE MODEL ----------------
class MediaFile(models.Model):
    title = models.CharField(max_length=200)

    image = models.ImageField(
        upload_to='images/',
        null=True,
        blank=True,
        validators=[validate_file_size]
    )

    video = models.FileField(
        upload_to='videos/',
        null=True,
        blank=True,
        validators=[validate_file_size]
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
