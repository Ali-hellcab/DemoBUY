from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Custom user model with a required, unique email address."""

    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
