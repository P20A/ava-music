from __future__ import annotations

import uuid

from django.db import models
from django.urls import reverse

from apps.core.validators import validate_audio_file, validate_document_file, validate_image_file


def submission_path(instance, filename):
    return f"submissions/{instance.pk or 'new'}/{filename}"


class MusicSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار بررسی"
        REVIEWING = "reviewing", "در حال بررسی"
        APPROVED = "approved", "تأیید شده"
        REJECTED = "rejected", "رد شده"
        PUBLISHED = "published", "منتشر شده"

    submitter = models.ForeignKey(
        "users.User",
        verbose_name="کاربر ارسال‌کننده",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
    )
    artist_name = models.CharField("نام هنرمند", max_length=180)
    featured_artists = models.CharField("هنرمندان همراه", max_length=255, blank=True)
    title = models.CharField("نام اثر", max_length=220)
    genre = models.ForeignKey(
        "categories.Category", verbose_name="سبک", on_delete=models.SET_NULL, null=True, blank=True
    )
    cover_image = models.ImageField(
        "کاور", upload_to=submission_path, blank=True, validators=[validate_image_file]
    )
    audio_320 = models.FileField(
        "فایل ۳۲۰", upload_to=submission_path, blank=True, validators=[validate_audio_file]
    )
    audio_128 = models.FileField(
        "فایل ۱۲۸", upload_to=submission_path, blank=True, validators=[validate_audio_file]
    )
    lyrics = models.TextField("متن ترانه", blank=True)
    description = models.TextField("توضیحات اثر", blank=True)
    contact_name = models.CharField("نام تماس", max_length=160)
    contact_email = models.EmailField("ایمیل تماس")
    contact_phone = models.CharField("تلفن تماس", max_length=40, blank=True)
    demo_url = models.URLField("لینک فایل / دمو", blank=True)

    rights_holder = models.CharField("صاحب حقوق", max_length=180)
    license_status = models.CharField(
        "وضعیت مجوز",
        max_length=20,
        choices=(
            ("owned", "مالکیت کامل اثر"),
            ("licensed", "دارای مجوز رسمی"),
            ("permitted", "اجازه کتبی صاحب اثر"),
            ("unknown", "نامشخص"),
        ),
        default="owned",
    )
    license_reference = models.CharField("مرجع مجوز", max_length=255, blank=True)
    permission_document = models.FileField(
        "مدرک مجوز", upload_to=submission_path, blank=True, validators=[validate_document_file]
    )
    is_original = models.BooleanField("اثر اصیل است", default=False)
    terms_accepted = models.BooleanField("پذیرش قوانین", default=False)

    status = models.CharField("وضعیت", max_length=20, choices=Status.choices, default=Status.PENDING)
    review_notes = models.TextField("یادداشت بررسی", blank=True)
    reviewed_by = models.ForeignKey(
        "users.User",
        verbose_name="بررسی‌کننده",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_submissions",
    )
    reviewed_at = models.DateTimeField("زمان بررسی", null=True, blank=True)
    created_song = models.ForeignKey(
        "music.Song",
        verbose_name="آهنگ ساخته‌شده",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_submissions",
    )
    ip_hash = models.CharField(max_length=64, blank=True, editable=False)
    token = models.UUIDField("شناسه پیگیری", default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "درخواست ارسال اثر"
        verbose_name_plural = "درخواست‌های ارسال اثر"
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.title} — {self.artist_name}"

    def get_status_url(self) -> str:
        return reverse("submissions:status", kwargs={"token": self.token})

    def get_admin_url(self) -> str:
        return f"/admin/submissions/musicsubmission/{self.pk}/change/"

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}
        if self.terms_accepted is not True:
            errors["terms_accepted"] = "پذیرش قوانین انتشار الزامی است."
        if self.is_original is not True:
            errors["is_original"] = "تأیید اصالت اثر الزامی است."
        if not (self.audio_320 or self.audio_128 or self.demo_url):
            errors["audio_320"] = "حداقل یک فایل صوتی یا لینک دمو وارد کنید."
        if errors:
            raise ValidationError(errors)
