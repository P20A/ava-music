from django.contrib import admin
from django.utils.html import format_html

from apps.music.models import Comment, Song, SongArtist, SongLike


class SongArtistInline(admin.TabularInline):
    model = SongArtist
    extra = 1
    autocomplete_fields = ("artist",)
    ordering = ("role", "order")


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = (
        "title", "primary_artist", "release_date", "duration_display",
        "is_published", "is_featured", "view_count", "play_count", "download_count",
        "license_status", "publication_authorized"
    )
    list_filter = (
        "is_published", "is_featured", "is_explicit", "language",
        "license_status", "publication_authorized", "content_removal_requested",
        "categories", "release_date"
    )
    list_editable = ("is_published", "is_featured")
    search_fields = ("title", "primary_artist__name", "artists__name", "lyrics", "composer", "lyricist")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("primary_artist", "categories")
    readonly_fields = (
        "view_count", "play_count", "download_count", "like_count",
        "created_at", "updated_at", "published_at", "search_text"
    )
    filter_horizontal = ("categories",)
    date_hierarchy = "published_at"
    inlines = [SongArtistInline]

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": ("title", "slug", "primary_artist", "cover_image")
        }),
        ("فایل‌های صوتی", {
            "fields": ("audio_320", "audio_128", "preview_audio", "instrumental_audio")
        }),
        ("متن و توضیحات", {
            "fields": ("lyrics", "description", "composer", "lyricist", "arranger")
        }),
        ("دسته‌بندی و سبک", {
            "fields": ("categories", "release_date", "duration", "language", "video_url")
        }),
        ("تنظیمات انتشار", {
            "fields": ("is_explicit", "is_featured", "is_published", "published_at")
        }),
        ("آمار", {
            "fields": ("view_count", "play_count", "download_count", "like_count"),
            "classes": ("collapse",)
        }),
        ("حقوق و مجوز", {
            "fields": ("rights_holder", "license_status", "license_reference", "publication_authorized", "content_removal_requested", "removal_notes"),
            "classes": ("collapse",)
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

    def duration_display(self, obj):
        return f"{obj.duration // 60}:{obj.duration % 60:02d}"
    duration_display.short_description = "مدت"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("primary_artist")

    actions = ["publish", "unpublish", "feature", "unfeature"]

    def publish(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_published=True, published_at=timezone.now())
    publish.short_description = "انتشار آثار انتخابی"

    def unpublish(self, request, queryset):
        queryset.update(is_published=False)
    unpublish.short_description = "حذف از انتشار"

    def feature(self, request, queryset):
        queryset.update(is_featured=True)
    feature.short_description = "ویژه کردن"

    def unfeature(self, request, queryset):
        queryset.update(is_featured=False)
    unfeature.short_description = "حالت عادی"


@admin.register(SongArtist)
class SongArtistAdmin(admin.ModelAdmin):
    list_display = ("song", "artist", "role", "order")
    list_filter = ("role",)
    search_fields = ("song__title", "artist__name")
    autocomplete_fields = ("song", "artist")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("song", "name", "initial", "is_approved", "created_at")
    list_filter = ("is_approved",)
    list_editable = ("is_approved",)
    search_fields = ("song__title", "name", "body", "email")
    readonly_fields = ("ip_hash", "created_at")
    date_hierarchy = "created_at"
    autocomplete_fields = ("song", "user", "parent")

    actions = ["approve", "disapprove"]

    def approve(self, request, queryset):
        queryset.update(is_approved=True)
    approve.short_description = "تأیید دیدگاه‌ها"

    def disapprove(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove.short_description = "لغو تأیید"


@admin.register(SongLike)
class SongLikeAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "session_key", "created_at")
    search_fields = ("song__title", "user__username")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"