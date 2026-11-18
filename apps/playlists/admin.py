from django.contrib import admin
from django.utils.html import format_html

from apps.playlists.models import Playlist, PlaylistItem


class PlaylistItemInline(admin.TabularInline):
    model = PlaylistItem
    extra = 1
    autocomplete_fields = ("song",)
    ordering = ("order",)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = (
        "name", "slug", "cover_preview", "owner", "is_public", "is_featured",
        "track_total", "total_duration_display", "created_at"
    )
    list_filter = ("is_public", "is_featured")
    list_editable = ("is_public", "is_featured")
    search_fields = ("name", "description", "owner__username")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("owner",)
    readonly_fields = ("search_text", "created_at", "updated_at")
    inlines = [PlaylistItemInline]

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": ("name", "slug", "cover", "description", "owner")
        }),
        ("تنظیمات", {
            "fields": ("is_public", "is_featured")
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


@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = ("playlist", "song", "order", "added_at")
    search_fields = ("playlist__name", "song__title")
    autocomplete_fields = ("playlist", "song")
    ordering = ("playlist", "order")