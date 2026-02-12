from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel

from .managers import CustomUserManager


class User(AbstractUser, UUIDModel, TimeStampedModel):
    username = None  # type: ignore[assignment]
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()  # type: ignore[assignment, misc]

    def __str__(self) -> str:
        return self.email
