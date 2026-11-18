from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from apps.core.utils import normalize_fa, truncate
from apps.core.validators import audio_duration_seconds, validate_audio_file, validate_image_file


class SongQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True, publication_authorized=True)

    def featured(self):
        return self.published().filter(is_featured=True)


class SongManager(models.Manager.from_queryset(SongQuerySet)):
    pass


def song_asset_path(instance, filename):
    return f"songs/{instance.slug or 'new'}/{filename}"


class Song(models.Model):
    class Language(models.TextChoices):
        PERSIAN = "fa", "فارسی"
        TURKISH = "tr", "ترکی"
        KURDISH = "ku", "کردی"
        ENGLISH = "en", "انگلیسی"
        ARABIC = "ar", "عربی"
        INSTRUMENTAL = "instrumental", "بی‌کلام"
        OTHER = "other", "سایر"

    class LicenseStatus(models.TextChoices):
        OWNED = "owned", "مالکیت کامل اثر"
        LICENSED = "licensed", "دارای مجوز رسمی"
        PERMITTED = "permitted", "اجازه کتبی صاحب اثر"
        PUBLIC_DOMAIN = "public_domain", "مالکیت عمومی"
        UNKNOWN = "unknown", "نامشخص / در انتظار بررسی"

    title = models.CharField("عنوان آهنگ", max_length=220)
    slug = models.SlugField("نامک", max_length=240, unique=True, allow_unicode=True)
    primary_artist = models.ForeignKey(
        "artists.Artist", verbose_name="هنرمند اصلی", on_delete=models.PROTECT, related_name="primary_songs"
    )
    artists = models.ManyToManyField(
        "artists.Artist", through="SongArtist", verbose_name="هنرمندان", related_name="songs", blank=True
    )
    cover_image = models.ImageField(
        "کاور", upload_to=song_asset_path, blank=True, validators=[validate_image_file]
    )
    audio_320 = models.FileField(
        "فایل صوتی ۳۲۰ کیلوبیت", upload_to=song_asset_path, blank=True, validators=[validate_audio_file]
    )
    audio_128 = models.FileField(
        "فایل صوتی ۱۲۸ کیلوبیت", upload_to=song_asset_path, blank=True, validators=[validate_audio_file]
    )
    preview_audio = models.FileField(
        "فایل پیش‌نمایش", upload_to=song_asset_path, blank=True, validators=[validate_audio_file]
    )
    instrumental_audio = models.FileField(
        "نسخه بی‌کلام", upload_to=song_asset_path, blank=True, validators=[validate_audio_file]
    )
    lyrics = models.TextField("متن ترانه", blank=True)
    description = models.TextField("توضیحات", blank=True)
    categories = models.ManyToManyField(
        "categories.Category", verbose_name="سبک‌ها و دسته‌بندی‌ها", related_name="songs", blank=True
    )
    release_date = models.DateField("تاریخ انتشار", null=True, blank=True)
    duration = models.PositiveIntegerField("مدت (ثانیه)", default=0)
    language = models.CharField("زبان", max_length=20, choices=Language.choices, default=Language.PERSIAN)
    composer = models.CharField("آهنگساز", max_length=180, blank=True)
    lyricist = models.CharField("ترانه‌سرا", max_length=180, blank=True)
    arranger = models.CharField("تنظیم‌کننده", max_length=180, blank=True)
    video_url = models.URLField("لینک موزیک ویدیو", blank=True)
    is_explicit = models.BooleanField("محتوای بزرگسال", default=False)
    is_featured = models.BooleanField("ویژه", default=False)
    is_published = models.BooleanField("منتشر شده", default=False)
    published_at = models.DateTimeField("زمان انتشار", null=True, blank=True)

    view_count = models.PositiveIntegerField("بازدید", default=0, editable=False)
    play_count = models.PositiveIntegerField("پخش", default=0, editable=False)
    download_count = models.PositiveIntegerField("دانلود", default=0, editable=False)
    like_count = models.PositiveIntegerField("پسند", default=0, editable=False)

    rights_holder = models.CharField("صاحب حقوق", max_length=180, blank=True)
    license_status = models.CharField(
        "وضعیت مجوز", max_length=20, choices=LicenseStatus.choices, default=LicenseStatus.UNKNOWN
    )
    license_reference = models.CharField("شماره/مرجع مجوز", max_length=255, blank=True)
    publication_authorized = models.BooleanField("اجازه انتشار تأیید شده", default=False)
    content_removal_requested = models.BooleanField("درخواست حذف محتوا", default=False)
    removal_notes = models.TextField("یادداشت حذف/حقوقی", blank=True)

    search_text = models.CharField(max_length=1000, blank=True, editable=False, db_index=True)
    seo_title = models.CharField("عنوان SEO", max_length=180, blank=True)
    seo_description = models.TextField("توضیح SEO", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SongManager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "آهنگ"
        verbose_name_plural = "آهنگ‌ها"
        indexes = [
            models.Index(fields=["is_published", "published_at"]),
            models.Index(fields=["is_published", "is_featured"]),
            models.Index(fields=["-view_count"]),
            models.Index(fields=["-download_count"]),
            models.Index(fields=["-play_count"]),
            models.Index(fields=["release_date"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.primary_artist}" if self.primary_artist_id else self.title

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        if not self.duration:
            self.duration = self._detect_duration()
        self.search_text = normalize_fa(
            " ".join(
                [
                    self.title or "",
                    self.lyrics or "",
                    self.description or "",
                    self.composer or "",
                    self.lyricist or "",
                    self.arranger or "",
                    self.primary_artist.name if self.primary_artist_id else "",
                ]
            )
        )[:1000]
        super().save(*args, **kwargs)
        if self.primary_artist_id:
            SongArtist.objects.get_or_create(
                song=self,
                artist_id=self.primary_artist_id,
                role=SongArtist.Role.PRIMARY,
                defaults={"order": 0},
            )

    def _detect_duration(self) -> int:
        for field in (self.audio_320, self.audio_128, self.preview_audio):
            if not field:
                continue
            try:
                path = field.path
            except (NotImplementedError, ValueError, AttributeError):
                return 0
            duration = audio_duration_seconds(path)
            if duration:
                return duration
        return 0

    def clean(self):
        errors = {}
        if self.is_published:
            if not self.publication_authorized:
                errors["publication_authorized"] = "پیش از انتشار باید اجازه انتشار اثر تأیید شود."
            if not (self.audio_320 or self.audio_128):
                errors["audio_320"] = "برای انتشار، حداقل یکی از فایل‌های ۱۲۸ یا ۳۲۰ لازم است."
            if self.content_removal_requested:
                errors["content_removal_requested"] = "اثری که درخواست حذف دارد نباید منتشر بماند."
        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        return reverse("music:detail", kwargs={"slug": self.slug})

    @property
    def is_playable(self) -> bool:
        return bool(self.preview_audio or self.audio_320 or self.audio_128)

    @property
    def best_audio(self):
        return self.preview_audio or self.audio_320 or self.audio_128

    @property
    def stream_field_name(self) -> str:
        if self.preview_audio:
            return "preview"
        if self.audio_320:
            return "320"
        return "128"

    @property
    def has_320(self) -> bool:
        return bool(self.audio_320)

    @property
    def has_128(self) -> bool:
        return bool(self.audio_128)

    @property
    def featured_artist_list(self):
        return [credit.artist for credit in self.artist_credits.all() if credit.role != SongArtist.Role.PRIMARY]

    @property
    def all_artist_names(self) -> str:
        names = [self.primary_artist.name]
        names.extend(artist.name for artist in self.featured_artist_list if artist.name != self.primary_artist.name)
        return "، ".join(names)

    @property
    def short_description(self) -> str:
        return truncate(self.description or self.seo_description or "", 150)

    @property
    def tag_label(self) -> str:
        if self.is_featured:
            return "ویژه"
        first = self.categories.first()
        return first.name if first else "آهنگ جدید"

    @property
    def published_year(self):
        return self.release_date.year if self.release_date else None


class SongArtist(models.Model):
    class Role(models.TextChoices):
        PRIMARY = "primary", "هنرمند اصلی"
        FEATURED = "featured", "هنرمند همراه"
        COMPOSER = "composer", "آهنگساز"
        LYRICIST = "lyricist", "ترانه‌سرا"
        ARRANGER = "arranger", "تنظیم‌کننده"
        PRODUCER = "producer", "تهیه‌کننده"

    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="artist_credits")
    artist = models.ForeignKey("artists.Artist", on_delete=models.CASCADE, related_name="song_credits")
    role = models.CharField("نقش", max_length=20, choices=Role.choices, default=Role.FEATURED)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["role", "order", "id"]
        verbose_name = "عوامل آهنگ"
        verbose_name_plural = "عوامل آهنگ"
        constraints = [
            models.UniqueConstraint(fields=["song", "artist", "role"], name="unique_song_artist_role"),
        ]

    def __str__(self):
        return f"{self.song} - {self.artist} ({self.get_role_display()})"


class SongLike(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, null=True, blank=True, related_name="song_likes"
    )
    session_key = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پسند آهنگ"
        verbose_name_plural = "پسندهای آهنگ"
        constraints = [
            models.UniqueConstraint(
                fields=["song", "user"], condition=Q(user__isnull=False), name="unique_song_like_user"
            ),
            models.UniqueConstraint(
                fields=["song", "session_key"],
                condition=Q(user__isnull=True),
                name="unique_song_like_session",
            ),
        ]

    def __str__(self):
        return f"{self.song} - {self.user or self.session_key}"


class CommentQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(is_approved=True)


class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="comments"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    name = models.CharField("نام", max_length=120)
    email = models.EmailField("ایمیل", blank=True)
    body = models.TextField("متن دیدگاه")
    is_approved = models.BooleanField("تأیید شده", default=False)
    ip_hash = models.CharField(max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ["created_at"]
        verbose_name = "دیدگاه"
        verbose_name_plural = "دیدگاه‌ها"
        indexes = [models.Index(fields=["song", "is_approved"])]

    def __str__(self):
        return f"{self.name}: {self.body[:40]}"

    @property
    def initial(self) -> str:
        return (self.name or "؟").strip()[:1]
