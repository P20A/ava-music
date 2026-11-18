from __future__ import annotations

from django.db import models
from django.urls import reverse

from apps.core.utils import normalize_fa


class SEOConfig(models.Model):
    """Global SEO configuration - singleton."""
    
    CACHE_KEY = "ava:seo-config"

    site_name = models.CharField("نام سایت", max_length=120, default="آوا موزیک")
    default_title = models.CharField("عنوان پیش‌فرض", max_length=180, blank=True)
    default_description = models.TextField("توضیح پیش‌فرض", blank=True)
    default_keywords = models.CharField("کلمات کلیدی پیش‌فرض", max_length=300, blank=True)
    default_og_image = models.ImageField(
        "تصویر پیش‌فرض Open Graph",
        upload_to="seo/",
        blank=True,
    )
    twitter_site = models.CharField("Twitter Site", max_length=60, blank=True, default="@avamusic")
    google_analytics_id = models.CharField("Google Analytics ID", max_length=60, blank=True)
    google_search_console = models.CharField("Google Search Console", max_length=120, blank=True)
    robots_txt = models.TextField("محتوای robots.txt", blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات SEO"
        verbose_name_plural = "تنظیمات SEO"

    def __str__(self):
        return "تنظیمات SEO"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.delete(self.CACHE_KEY)

    @classmethod
    def load(cls):
        from django.core.cache import cache
        cached = cache.get(cls.CACHE_KEY)
        if cached is not None:
            return cached
        try:
            obj, _ = cls.objects.get_or_create(pk=1)
        except Exception:
            obj = cls(pk=1)
        try:
            cache.set(cls.CACHE_KEY, obj, 300)
        except Exception:
            pass
        return obj


class Redirect(models.Model):
    """301/302 redirects for changed URLs."""
    
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


class SitemapEntry(models.Model):
    """Manual sitemap entries for pages not covered by auto-sitemap."""
    
    class ChangeFreq(models.TextChoices):
        ALWAYS = "always", "همیشه"
        HOURLY = "hourly", "هر ساعت"
        DAILY = "daily", "روزانه"
        WEEKLY = "weekly", "هفتگی"
        MONTHLY = "monthly", "ماهانه"
        YEARLY = "yearly", "سالانه"
        NEVER = "never", "هرگز"

    url = models.CharField("آدرس", max_length=500, unique=True)
    changefreq = models.CharField("تغییر", max_length=10, choices=ChangeFreq.choices, default=ChangeFreq.WEEKLY)
    priority = models.DecimalField("اولویت", max_digits=2, decimal_places=1, default=0.5)
    lastmod = models.DateTimeField("آخرین تغییر", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "ورودی نقشه سایت"
        verbose_name_plural = "ورودی‌های نقشه سایت"

    def __str__(self):
        return self.url