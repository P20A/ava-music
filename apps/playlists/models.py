from __future__ import annotations

from django.db import models
from django.db.models import Sum
from django.urls import reverse

from apps.core.utils import normalize_fa
from apps.core.validators import validate_image_file


class PlaylistQuerySet(models.QuerySet):
    def public(self):
        return self.filter(is_public=True)


class PlaylistManager(models.Manager.from_queryset(PlaylistQuerySet)):
    pass


def playlist_cover_path(instance, filename):
    return f"playlists/{instance.slug or 'new'}/{filename}"


class Playlist(models.Model):
    name = models.CharField("نام پلی‌لیست", max_length=180)
    slug = models.SlugField("نامک", max_length=200, unique=True, allow_unicode=True)
    cover = models.ImageField("کاور", upload_to=playlist_cover_path, blank=True, validators=[validate_image_file])
    description = models.TextField("توضیحات", blank=True)
    songs = models.ManyToManyField(
        "music.Song", through="PlaylistItem", verbose_name="آهنگ‌ها", related_name="playlists", blank=True
    )
    owner = models.ForeignKey(
        "users.User", verbose_name="سازنده", on_delete=models.SET_NULL, null=True, blank=True, related_name="playlists"
    )
    is_public = models.BooleanField("عمومی", default=True)
    is_featured = models.BooleanField("ویژه", default=False)
    search_text = models.CharField(max_length=500, blank=True, editable=False, db_index=True)
    seo_title = models.CharField("عنوان SEO", max_length=180, blank=True)
    seo_description = models.TextField("توضیح SEO", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PlaylistManager()

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        verbose_name = "پلی‌لیست"
        verbose_name_plural = "پلی‌لیست‌ها"
        indexes = [models.Index(fields=["is_public", "is_featured"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.search_text = normalize_fa(f"{self.name} {self.description}")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("playlists:detail", kwargs={"slug": self.slug})

    @property
    def track_total(self) -> int:
        return self.items.count()

    @property
    def total_duration(self) -> int:
        return self.items.aggregate(total=Sum("song__duration"))["total"] or 0


class PlaylistItem(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="items")
    song = models.ForeignKey("music.Song", on_delete=models.CASCADE, related_name="playlist_items")
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "آهنگ پلی‌لیست"
        verbose_name_plural = "آهنگ‌های پلی‌لیست"
        constraints = [
            models.UniqueConstraint(fields=["playlist", "song"], name="unique_playlist_song"),
        ]

    def __str__(self):
        return f"{self.playlist} - {self.song}"
