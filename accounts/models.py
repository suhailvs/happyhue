import re

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

E164 = re.compile(r"^\+[1-9]\d{7,14}$")
phone_validator = RegexValidator(E164, "Enter the number in international format, for example +919876543210.")


def normalize_phone(raw):
    """Return the number in E.164 form, or '' if it can't be read. A bare 10 digit Indian mobile gets +91."""
    value = re.sub(r"[\s\-()]", "", raw or "")
    if re.fullmatch(r"[6-9]\d{9}", value):
        value = "+91" + value
    elif re.fullmatch(r"0?91[6-9]\d{9}", value):
        value = "+91" + value[-10:]
    return value if E164.fullmatch(value) else ""


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, password, **extra):
        email = self.normalize_email(email).strip().lower()
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=email, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # customers sign in with Google, never a password
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not password:
            raise ValueError("Superusers need a password to sign in to the admin.")
        return self._create(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    google_sub = models.CharField(max_length=64, unique=True, null=True, blank=True, editable=False)
    name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(
        max_length=16, blank=True, validators=[phone_validator],
        help_text="Optional. International format, e.g. +919876543210.",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False, help_text="Can sign in to the admin site.")
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.name or self.email

    def get_full_name(self):
        return self.name or self.email

    def get_short_name(self):
        return (self.name or self.email).split(" ")[0].split("@")[0]

    @property
    def national_number(self):
        """Ten digit number for the Indian checkout form. Empty if no phone is saved."""
        if not self.phone:
            return ""
        return self.phone[3:] if self.phone.startswith("+91") else self.phone.lstrip("+")