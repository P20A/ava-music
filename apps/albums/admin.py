from django.contrib import admin
from django.utils.html import format_html

from apps.albums.models import Album, AlbumTrack


class AlbumTrackInline(admin.TabularInline):
    model = AlbumTrack
    extra = 1
    autocomplete_fields = ("song",)
    ordering = ("disc_number", "track_number", "order")


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = (
        "title", "slug", "cover_preview", "album_type", "release_date",
        "is_published", "is_featured", "total_duration_display", "created_at"
    )
    list_filter = ("album_type", "is_published", "is_featured", "release_date")
    list_editable = ("is_published", "is_featured")
    search_fields = ("title", "artists__name", "description", "label")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("artists",)
    readonly_fields = ("search_text", "published_at", "created_at", "updated_at")
    filter_horizontal = ("artists",)
    date_hierarchy = "release_date"
    inlines = [AlbumTrackInline]

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": ("title", "slug", "cover", "artists")
        }),
        ("توضیحات", {
            "fields": ("description", "release_date", "album_type", "label")
        }),
        ("تنظیمات انتشار", {
            "fields": ("is_published", "is_featured", "published_at")
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

    def cover_preview(self, obj):
        if obj.cover:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 4px;" />', obj.cover.url)
        return "—"
    cover_preview.short_description = "کاور"

    def total_duration_display(self, obj):
        total = obj.total_duration
        if total:
            return f"{total // 60}:{total % 60:02d}"
        return "—"
    total_duration_display.short_description = "مدت کل"

    actions = ["publish", "unpublish", "feature", "unfeature"]

    def publish(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_published=True, published_at=timezone.now())
    publish.short_description = "انتشار آلبوم‌های انتخابی"

    def unpublish(self, request, queryset):
        queryset.update(is_published=False)
    unpublish.short_description = "حذف از انتشار"

    def feature(self, request, queryset):
        queryset.update(is_featured=True)
    feature.short_description = "ویژه کردن"

    def unfeature(self, request, queryset):
        queryset.update(is_featured=False)
    unfeature.short_description = "حالت عادی"


@admin.register(AlbumTrack)
class AlbumTrackAdmin(admin.ModelAdmin):
    list_display = ("album", "song", "disc_number", "track_number", "order")
    list_filter = ("disc_number",)
    search_fields = ("album__title", "song__title")
    autocomplete_fields = ("album", "song")
    ordering = ("album", "disc_number", "track_number", "order")