from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.urls import reverse

from apps.core.utils import normalize_fa
from apps.core.validators import validate_image_file


class ArtistQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def featured(self):
        return self.active().filter(is_featured=True)


class ArtistManager(models.Manager.from_queryset(ArtistQuerySet)):
    pass


def artist_image_path(instance, filename):
    return f"artists/{instance.slug or 'new'}/{filename}"


class Artist(models.Model):
    name = models.CharField("نام هنرمند", max_length=160)
    slug = models.SlugField("نامک", max_length=180, unique=True, allow_unicode=True)
    profile_image = models.ImageField(
        "تصویر پروفایل", upload_to=artist_image_path, blank=True, validators=[validate_image_file]
    )
    cover_image = models.ImageField(
        "تصویر کاور صفحه", upload_to=artist_image_path, blank=True, validators=[validate_image_file]
    )
    biography = models.TextField("بیوگرافی", blank=True)
    description = models.TextField("توضیح کوتاه", blank=True)
    city = models.CharField("شهر", max_length=80, blank=True)
    country = models.CharField("کشور", max_length=80, blank=True, default="ایران")
    active_since = models.CharField("فعال از", max_length=20, blank=True)
    website = models.URLField("وب‌سایت", blank=True)
    instagram = models.CharField("اینستاگرام", max_length=160, blank=True)
    telegram = models.CharField("تلگرام", max_length=160, blank=True)
    is_verified = models.BooleanField("تأیید شده", default=False)
    is_featured = models.BooleanField("ویژه", default=False)
    is_active = models.BooleanField("فعال", default=True)
    search_text = models.CharField(max_length=500, blank=True, editable=False, db_index=True)
    seo_title = models.CharField("عنوان SEO", max_length=180, blank=True)
    seo_description = models.TextField("توضیح SEO", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ArtistManager()

    class Meta:
        ordering = ["name"]
        verbose_name = "هنرمند"
        verbose_name_plural = "هنرمندان"
        indexes = [
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.search_text = normalize_fa(f"{self.name} {self.biography} {self.city}")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("artists:detail", kwargs={"slug": self.slug})

    @property
    def song_count(self) -> int:
        return self.songs.filter(is_published=True).count()

    @property
    def album_count(self) -> int:
        return self.albums.filter(is_published=True).count()

    @property
    def follower_count(self) -> int:
        return self.followers.count()

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def primary_songs(self):
        return self.songs.filter(is_published=True)


class ArtistFollow(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="followers")
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, null=True, blank=True, related_name="artist_follows"
    )
    session_key = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "دنبال‌کننده هنرمند"
        verbose_name_plural = "دنبال‌کنندگان هنرمند"
        constraints = [
            models.UniqueConstraint(
                fields=["artist", "user"],
                condition=Q(user__isnull=False),
                name="unique_artist_follow_user",
            ),
            models.UniqueConstraint(
                fields=["artist", "session_key"],
                condition=Q(user__isnull=True),
                name="unique_artist_follow_session",
            ),
        ]

    def __str__(self):
        return f"{self.artist} - {self.user or self.session_key}"
