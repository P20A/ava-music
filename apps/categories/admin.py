from django.contrib import admin
from django.utils.html import format_html

from apps.categories.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name", "slug", "kind", "image_preview", "icon", "parent",
        "order", "is_active", "is_featured", "song_count", "created_at"
    )
    list_filter = ("kind", "is_active", "is_featured", "parent")
    list_editable = ("order", "is_active", "is_featured")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("parent",)
    readonly_fields = ("search_text", "created_at", "updated_at")

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": ("name", "slug", "kind", "parent")
        }),
        ("توضیحات و رسانه", {
            "fields": ("description", "image", "icon")
        }),
        ("تنظیمات", {
            "fields": ("order", "is_active", "is_featured")
        }),
        ("SEO", {
            "fields": ("seo_title", "seo_description"),
            "classes": ("collapse",)
        }),
        ("سیستم", {
            "fields": ("search_text", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="32" height="32" style="border-radius: 4px;" />', obj.image.url)
        return "—"
    image_preview.short_description = "تصویر"