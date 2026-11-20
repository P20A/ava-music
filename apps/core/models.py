from __future__ import annotations

import uuid

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify

from apps.core.validators import validate_image_file


def site_asset_path(instance, filename):
    return f"site/{filename}"


def banner_path(instance, filename):
    return f"banners/{filename}"


def page_image_path(instance, filename):
    return f"pages/{filename}"


class SiteSettings(models.Model):
    """Singleton row edited from Django admin."""

    CACHE_KEY = "ava:site-settings"

    site_name = models.CharField("نام سایت", max_length=120, default="آوا موزیک")
    site_tagline = models.CharField("شعار کوتاه", max_length=180, blank=True)
    site_description = models.TextField("توضیح کوتاه سایت", blank=True)
    logo = models.ImageField("لوگو", upload_to=site_asset_path, blank=True, validators=[validate_image_file])
    favicon = models.ImageField("فاوآیکون", upload_to=site_asset_path, blank=True, validators=[validate_image_file])
    default_share_image = models.ImageField(
        "تصویر پیش‌فرض اشتراک‌گذاری",
        upload_to=site_asset_path,
        blank=True,
        validators=[validate_image_file],
    )
    contact_email = models.EmailField("ایمیل تماس", blank=True)
    contact_phone = models.CharField("تلفن تماس", max_length=40, blank=True)
    address = models.CharField("نشانی", max_length=255, blank=True)
    working_hours = models.CharField("ساعات پاسخ‌گویی", max_length=120, blank=True, default="۹ تا ۱۸")
    instagram = models.URLField("اینستاگرام", blank=True)
    telegram = models.URLField("تلگرام", blank=True)
    twitter = models.URLField("ایکس / توییتر", blank=True)
    youtube = models.URLField("یوتیوب", blank=True)
    spotify = models.URLField("اسپاتیفای", blank=True)
    whatsapp = models.URLField("واتساپ", blank=True)

    footer_about = models.TextField("درباره در فوتر", blank=True)
    footer_copyright = models.CharField("متن کپی‌رایت", max_length=220, blank=True)
    default_seo_title = models.CharField("عنوان SEO پیش‌فرض", max_length=180, blank=True)
    default_seo_description = models.TextField("توضیح SEO پیش‌فرض", blank=True)
    default_keywords = models.CharField("کلمات کلیدی پیش‌فرض", max_length=300, blank=True)
    google_analytics_id = models.CharField("شناسه Google Analytics", max_length=60, blank=True)
    theme_color = models.CharField("رنگ نوار مرورگر", max_length=20, default="#091540")
    default_theme = models.CharField("پوسته پیش‌فرض", max_length=20, choices=[("light", "روشن"), ("dark", "تیره")], default="light")
    posts_per_page = models.PositiveSmallIntegerField("تعداد آیتم در هر صفحه", default=12)

    ads_enabled = models.BooleanField("نمایش تبلیغات", default=True)
    comments_enabled = models.BooleanField("فعال بودن دیدگاه‌ها", default=True)
    submissions_enabled = models.BooleanField("فعال بودن ارسال اثر", default=True)
    downloads_enabled = models.BooleanField("فعال بودن دانلود", default=True)
    registration_enabled = models.BooleanField("فعال بودن ثبت‌نام", default=True)
    maintenance_mode = models.BooleanField("حالت تعمیرات", default=False)

    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.site_name or "تنظیمات سایت"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(self.CACHE_KEY)

    @classmethod
    def load(cls):
        cached = cache.get(cls.CACHE_KEY)
        if cached is not None:
            return cached
        try:
            obj, _ = cls.objects.get_or_create(pk=1)
        except Exception:
            # During first migration or before the DB is reachable.
            obj = cls(pk=1)
        try:
            cache.set(cls.CACHE_KEY, obj, 300)
        except Exception:
            pass
        return obj

    @property
    def share_image(self):
        return self.default_share_image or self.logo


class NavigationLink(models.Model):
    class Location(models.TextChoices):
        TOPBAR = "topbar", "نوار بالایی"
        HEADER = "header", "منوی اصلی"
        FOOTER = "footer", "فوتر"

    location = models.CharField("محل نمایش", max_length=20, choices=Location.choices, default=Location.HEADER)
    label = models.CharField("عنوان", max_length=80)
    url = models.CharField("لینک", max_length=255, help_text="مثال: /songs/ یا https://...")
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)
    open_new_tab = models.BooleanField("باز شدن در تب جدید", default=False)

    class Meta:
        ordering = ["location", "order", "id"]
        verbose_name = "لینک ناوبری"
        verbose_name_plural = "لینک‌های ناوبری"

    def __str__(self):
        return f"{self.label} ({self.get_location_display()})"


class HomeSection(models.Model):
    class Type(models.TextChoices):
        LATEST = "latest", "جدیدترین آهنگ‌ها"
        FEATURED = "featured", "آهنگ‌های ویژه"
        POPULAR = "popular", "پربازدیدترین آهنگ‌ها"
        MOST_DOWNLOADED = "most_downloaded", "بیشترین دانلود"
        MOST_PLAYED = "most_played", "بیشترین پخش"
        ALBUMS = "albums", "آلبوم‌ها"
        PLAYLISTS = "playlists", "پلی‌لیست‌ها"
        ARTISTS = "artists", "خوانندگان"
        CATEGORIES = "categories", "دسته‌بندی‌ها"

    section_type = models.CharField("نوع بخش", max_length=30, choices=Type.choices)
    title = models.CharField("عنوان", max_length=120)
    subtitle = models.CharField("زیرعنوان", max_length=160, blank=True)
    link_label = models.CharField("متن لینک", max_length=80, blank=True)
    link_url = models.CharField("آدرس لینک", max_length=255, blank=True)
    limit = models.PositiveSmallIntegerField("تعداد آیتم", default=6)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "بخش صفحه اصلی"
        verbose_name_plural = "بخش‌های صفحه اصلی"

    def __str__(self):
        return self.title

    def clean(self):
        if self.limit > 24:
            raise ValidationError({"limit": "حداکثر ۲۴ آیتم برای هر بخش مجاز است."})


class HomeBanner(models.Model):
    class Placement(models.TextChoices):
        HERO = "hero", "بنر ویژه صفحه اصلی"
        HEADER = "header", "بنر کنار لوگو"
        SIDEBAR = "sidebar", "بنر ستون کنار"
        ARCHIVE = "archive", "بنر صفحه آرشیو"
        FOOTER = "footer", "بنر بالای فوتر"

    placement = models.CharField("محل", max_length=20, choices=Placement.choices, default=Placement.HERO)
    title = models.CharField("عنوان", max_length=160)
    subtitle = models.CharField("زیرعنوان", max_length=220, blank=True)
    label = models.CharField("برچسب کوچک", max_length=60, blank=True)
    image = models.ImageField("تصویر", upload_to=banner_path, blank=True, validators=[validate_image_file])
    link_url = models.CharField("لینک", max_length=255, blank=True)
    link_label = models.CharField("متن دکمه", max_length=80, blank=True, default="مشاهده")
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)
    start_date = models.DateTimeField("شروع نمایش", null=True, blank=True)
    end_date = models.DateTimeField("پایان نمایش", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["placement", "order", "id"]
        verbose_name = "بنر صفحه اصلی"
        verbose_name_plural = "بنرهای صفحه اصلی"

    def __str__(self):
        return self.title

    @property
    def is_live(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class StaticPage(models.Model):
    title = models.CharField("عنوان", max_length=160)
    slug = models.SlugField("نامک", max_length=160, unique=True, allow_unicode=True)
    excerpt = models.TextField("خلاصه", blank=True)
    content = models.TextField("محتوا (HTML)", help_text="این محتوا توسط مدیر سایت نوشته می‌شود و به‌صورت HTML نمایش داده می‌شود.")
    image = models.ImageField("تصویر", upload_to=page_image_path, blank=True, validators=[validate_image_file])
    is_published = models.BooleanField("منتشر شده", default=True)
    show_in_footer = models.BooleanField("نمایش در فوتر", default=True)
    seo_title = models.CharField("عنوان SEO", max_length=180, blank=True)
    seo_description = models.TextField("توضیح SEO", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "صفحه ثابت"
        verbose_name_plural = "صفحات ثابت"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.excerpt:
            self.excerpt = strip_tags(self.content or "")[:300]
        if not self.seo_description:
            self.seo_description = self.excerpt[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:page", kwargs={"slug": self.slug})


class ContactMessage(models.Model):
    class Subject(models.TextChoices):
        SUPPORT = "support", "پشتیبانی"
        ADVERTISING = "advertising", "همکاری و تبلیغات"
        CORRECTION = "correction", "اصلاح اطلاعات اثر"
        REPORT = "report", "گزارش تخلف / حذف محتوا"
        OTHER = "other", "سایر"

    name = models.CharField("نام", max_length=120)
    email = models.EmailField("ایمیل")
    phone = models.CharField("تلفن", max_length=30, blank=True)
    subject = models.CharField("موضوع", max_length=30, choices=Subject.choices, default=Subject.SUPPORT)
    message = models.TextField("پیام")
    is_read = models.BooleanField("خوانده شده", default=False)
    ip_hash = models.CharField(max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField("ایمیل", unique=True)
    name = models.CharField("نام", max_length=120, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    source = models.CharField("منبع", max_length=60, blank=True, default="footer")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "عضو خبرنامه"
        verbose_name_plural = "اعضای خبرنامه"

    def __str__(self):
        return self.email


class Redirect(models.Model):
    old_path = models.CharField("مسیر قدیمی", max_length=500, unique=True)
    new_path = models.CharField("مسیر جدید", max_length=500)
    is_permanent = models.BooleanField("ریدایرکت دائمی (301)", default=True)
    hits = models.PositiveIntegerField("تعداد بازدید", default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_hit_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ریدایرکت"
        verbose_name_plural = "ریدایرکت‌ها"

    def __str__(self):
        return f"{self.old_path} → {self.new_path}"

    def save(self, *args, **kwargs):
        if self.old_path and not self.old_path.startswith("/"):
            self.old_path = "/" + self.old_path
        if self.new_path and not self.new_path.startswith(("/", "http://", "https://")):
            self.new_path = "/" + self.new_path
        super().save(*args, **kwargs)

    @classmethod
    def create_for_slug_change(cls, old_path: str, new_path: str):
        if not old_path or not new_path or old_path == new_path:
            return None
        obj, _ = cls.objects.update_or_create(
            old_path=old_path,
            defaults={"new_path": new_path, "is_permanent": True},
        )
        return obj
