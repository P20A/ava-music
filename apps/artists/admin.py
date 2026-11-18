from django.contrib import admin
from django.utils.html import format_html

from apps.artists.models import Artist, ArtistFollow


class ArtistFollowInline(admin.TabularInline):
    model = ArtistFollow
    extra = 0
    readonly_fields = ("user", "session_key", "created_at")
    can_delete = False


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = (
        "name", "slug", "profile_image_preview", "is_verified", "is_featured",
        "is_active", "song_count", "album_count", "follower_count", "created_at"
    )
    list_filter = ("is_verified", "is_featured", "is_active")
    list_editable = ("is_verified", "is_featured", "is_active")
    search_fields = ("name", "biography", "city")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("songs", "albums")
    readonly_fields = ("search_text", "created_at", "updated_at")
    inlines = [ArtistFollowInline]

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": ("name", "slug", "profile_image", "cover_image")
        }),
        ("بیوگرافی و توضیحات", {
            "fields": ("biography", "description", "city", "country", "active_since")
        }),
        ("شبکه‌های اجتماعی", {
            "fields": ("website", "instagram", "telegram")
        }),
        ("تنظیمات", {
            "fields": ("is_verified", "is_featured", "is_active")
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

    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="32" height="32" style="border-radius: 50%;" />', obj.profile_image.url)
        return "—"
    profile_image_preview.short_description = "تصویر"


@admin.register(ArtistFollow)
class ArtistFollowAdmin(admin.ModelAdmin):
    list_display = ("artist", "user", "session_key", "created_at")
    search_fields = ("artist__name", "user__username")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"