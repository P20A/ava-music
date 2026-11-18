from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from apps.core.utils import normalize_fa
from apps.core.validators import validate_image_file


def category_image_path(instance, filename):
    return f"categories/{instance.slug or 'new'}/{filename}"


class Category(models.Model):
    class Kind(models.TextChoices):
        GENRE = "genre", "سبک موسیقی"
        CATEGORY = "category", "دسته‌بندی"
        MOOD = "mood", "حال‌وهوا"
        LANGUAGE = "language", "زبان"

    name = models.CharField("نام", max_length=120)
    slug = models.SlugField("نامک", max_length=140, unique=True, allow_unicode=True)
    kind = models.CharField("نوع", max_length=20, choices=Kind.choices, default=Kind.GENRE)
    description = models.TextField("توضیحات", blank=True)
    image = models.ImageField("تصویر", upload_to=category_image_path, blank=True, validators=[validate_image_file])
    icon = models.CharField("آیکون / نشانه", max_length=10, blank=True, help_text="یک کاراکتر مانند ♪ یا ♫")
    parent = models.ForeignKey(
        "self",
        verbose_name="دسته والد",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)
    is_featured = models.BooleanField("ویژه", default=False)
    search_text = models.CharField(max_length=300, blank=True, editable=False, db_index=True)
    seo_title = models.CharField("عنوان SEO", max_length=180, blank=True)
    seo_description = models.TextField("توضیح SEO", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "دسته‌بندی / سبک"
        verbose_name_plural = "دسته‌بندی‌ها و سبک‌ها"
        indexes = [models.Index(fields=["is_active", "kind"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.search_text = normalize_fa(f"{self.name} {self.description}")
        super().save(*args, **kwargs)

    def clean(self):
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "یک دسته نمی‌تواند والد خودش باشد."})
        ancestor = self.parent
        while ancestor:
            if ancestor.pk == self.pk:
                raise ValidationError({"parent": "چرخه در دسته‌بندی‌ها مجاز نیست."})
            ancestor = ancestor.parent

    def get_absolute_url(self):
        return reverse("categories:detail", kwargs={"slug": self.slug})

    @property
    def song_count(self) -> int:
        return self.songs.filter(is_published=True).count()
