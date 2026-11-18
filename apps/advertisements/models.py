from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from apps.core.validators import validate_image_file


class AdvertisementQuerySet(models.QuerySet):
    def live(self):
        now = timezone.now()
        return self.filter(is_active=True).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now)
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=now))


class AdvertisementManager(models.Manager.from_queryset(AdvertisementQuerySet)):
    pass


def ad_banner_path(instance, filename):
    return f"ads/{filename}"


class Advertisement(models.Model):
    class Placement(models.TextChoices):
        HEADER = "header", "نوار بالای سایت"
        HOME_TOP = "home_top", "بالای صفحه اصلی"
        HOME_SIDEBAR = "home_sidebar", "ستون کنار صفحه اصلی"
        ARCHIVE = "archive", "صفحه آرشیو"
        SONG_SIDEBAR = "song_sidebar", "ستون کنار صفحه آهنگ"
        ARTISTS = "artists", "صفحه خوانندگان"
        ALBUMS = "albums", "صفحه آلبوم‌ها"
        PLAYLISTS = "playlists", "صفحه پلی‌لیست‌ها"
        CATEGORY = "category", "صفحه دسته‌بندی"
        FOOTER = "footer", "بالای فوتر"

    title = models.CharField("عنوان", max_length=160)
    image = models.ImageField(
        "تصویر / بنر", upload_to=ad_banner_path, blank=True, validators=[validate_image_file]
    )
    alt_text = models.CharField("متن جایگزین تصویر", max_length=180, blank=True)
    destination_url = models.URLField("آدرس مقصد", help_text="لینک مقصد تبلیغ (http یا https)")
    placement = models.CharField("محل نمایش", max_length=30, choices=Placement.choices)
    description = models.CharField("متن کوتاه", max_length=220, blank=True)
    start_date = models.DateTimeField("شروع نمایش", null=True, blank=True)
    end_date = models.DateTimeField("پایان نمایش", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    priority = models.PositiveSmallIntegerField("اولویت نمایش", default=0, help_text="عدد بزرگ‌تر زودتر نمایش داده می‌شود.")
    click_count = models.PositiveIntegerField("کلیک", default=0, editable=False)
    impression_count = models.PositiveIntegerField("نمایش", default=0, editable=False)
    open_new_tab = models.BooleanField("باز شدن در تب جدید", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AdvertisementManager()

    class Meta:
        ordering = ["-priority", "id"]
        verbose_name = "تبلیغ"
        verbose_name_plural = "تبلیغات"
        indexes = [models.Index(fields=["placement", "is_active", "priority"])]

    def __str__(self):
        return f"{self.title} ({self.get_placement_display()})"

    @property
    def is_live(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True

    def get_click_url(self):
        return reverse("advertisements:click", kwargs={"pk": self.pk})
