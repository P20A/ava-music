from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.validators import validate_image_file


def avatar_path(instance, filename):
    return f"avatars/{instance.pk or 'new'}/{filename}"


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "مدیر سایت"
        EDITOR = "editor", "ویرایشگر"
        PUBLISHER = "publisher", "ناشر موسیقی"
        LISTENER = "listener", "کاربر عادی"

    email = models.EmailField("ایمیل", unique=True)
    role = models.CharField("نقش", max_length=20, choices=Role.choices, default=Role.LISTENER)
    avatar = models.ImageField("تصویر پروفایل", upload_to=avatar_path, blank=True, validators=[validate_image_file])
    bio = models.TextField("درباره من", blank=True)
    website = models.URLField("وب‌سایت", blank=True)
    instagram = models.CharField("اینستاگرام", max_length=120, blank=True)
    telegram = models.CharField("تلگرام", max_length=120, blank=True)
    newsletter_opt_in = models.BooleanField("عضویت در خبرنامه", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username

    @property
    def is_publisher(self) -> bool:
        return self.role in {self.Role.ADMIN, self.Role.EDITOR, self.Role.PUBLISHER} or self.is_staff
