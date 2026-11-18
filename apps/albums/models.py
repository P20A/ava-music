from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.urls import reverse

from apps.core.utils import normalize_fa
from apps.core.validators import validate_image_file


class AlbumQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class AlbumManager(models.Manager.from_queryset(AlbumQuerySet)):
    pass


def album_cover_path(instance, filename):
    return f"albums/{instance.slug or 'new'}/{filename}"


class Album(models.Model):
    class Type(models.TextChoices):
        ALBUM = "album", "آلبوم رسمی"
        EP = "ep", "ئی‌پی"
        SINGLE = "single", "تک‌آهنگ"
        COMPILATION = "compilation", "گردآوری"
        SOUNDTRACK = "soundtrack", "موسیقی متن"
        LIVE = "live", "اجرای زنده"

    title = models.CharField("عنوان آلبوم", max_length=180)
    slug = models.SlugField("نامک", max_length=200, unique=True, allow_unicode=True)
    cover = models.ImageField("کاور", upload_to=album_cover_path, blank=True, validators=[validate_image_file])
    artists = models.ManyToManyField("artists.Artist", verbose_name="هنرمندان", related_name="albums", blank=True)
    description = models.TextField("توضیحات", blank=True)
    release_date = models.DateField("تاریخ انتشار", null=True, blank=True)
    album_type = models.CharField("نوع آلبوم", max_length=20, choices=Type.choices, default=Type.ALBUM)
    label = models.CharField("ناشر", max_length=160, blank=True)
    is_published = models.BooleanField("منتشر شده", default=False)
    is_featured = models.BooleanField("ویژه", default=False)
    published_at = models.DateTimeField("زمان انتشار", null=True, blank=True)
    search_text = models.CharField(max_length=500, blank=True, editable=False, db_index=True)
    seo_title = models.CharField("عنوان SEO", max_length=180, blank=True)
    seo_description = models.TextField("توضیح SEO", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AlbumManager()

    class Meta:
        ordering = ["-release_date", "-created_at"]
        verbose_name = "آلبوم"
        verbose_name_plural = "آلبوم‌ها"
        indexes = [
            models.Index(fields=["is_published", "release_date"]),
            models.Index(fields=["is_published", "is_featured"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.search_text = normalize_fa(f"{self.title} {self.description} {self.label}")
        if self.is_published and not self.published_at:
            from django.utils import timezone

            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def clean(self):
        if self.is_published and self.release_date is None:
            raise ValidationError({"release_date": "برای انتشار آلبوم، تاریخ انتشار را وارد کنید."})

    def get_absolute_url(self):
        return reverse("albums:detail", kwargs={"slug": self.slug})

    @property
    def track_total(self) -> int:
        return self.tracks.count()

    @property
    def total_duration(self) -> int:
        return self.tracks.aggregate(total=Sum("song__duration"))["total"] or 0

    @property
    def primary_artist(self):
        return self.artists.first()

    @property
    def year(self):
        return self.release_date.year if self.release_date else None


class AlbumTrack(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="tracks")
    song = models.ForeignKey("music.Song", on_delete=models.CASCADE, related_name="album_tracks")
    disc_number = models.PositiveSmallIntegerField("شماره دیسک", default=1)
    track_number = models.PositiveSmallIntegerField("شماره قطعه", default=1)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["disc_number", "track_number", "order", "id"]
        verbose_name = "قطعه آلبوم"
        verbose_name_plural = "قطعات آلبوم"
        constraints = [
            models.UniqueConstraint(
                fields=["album", "disc_number", "track_number"],
                name="unique_album_disc_track",
            ),
            models.UniqueConstraint(fields=["album", "song"], name="unique_album_song"),
        ]

    def __str__(self):
        return f"{self.album} - {self.track_number}. {self.song}"
