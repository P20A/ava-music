from django.contrib import admin
from django.utils.html import format_html

from apps.submissions.models import MusicSubmission


@admin.register(MusicSubmission)
class MusicSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "title", "artist_name", "submitter", "status", "status_badge", "genre",
        "has_audio", "reviewed_by", "reviewed_at", "created_at"
    )
    list_filter = ("status", "genre", "is_original", "terms_accepted")
    list_editable = ("status",)
    search_fields = ("title", "artist_name", "contact_name", "contact_email", "submitter__username")
    readonly_fields = (
        "ip_hash", "created_at", "updated_at", "reviewed_at",
        "cover_image_preview", "audio_320_player", "audio_128_player"
    )
    autocomplete_fields = ("submitter", "reviewed_by", "genre", "created_song")
    date_hierarchy = "created_at"

    fieldsets = (
        ("اطلاعات اثر", {
            "fields": ("artist_name", "featured_artists", "title", "genre")
        }),
        ("رسانه", {
            "fields": (
                "cover_image", "cover_image_preview",
                "audio_320", "audio_320_player",
                "audio_128", "audio_128_player",
                "lyrics", "description"
            )
        }),
        ("اطلاعات تماس", {
            "fields": ("contact_name", "contact_email", "contact_phone", "demo_url")
        }),
        ("حقوق و مجوز", {
            "fields": ("rights_holder", "license_status", "license_reference", "permission_document", "is_original", "terms_accepted")
        }),
        ("بررسی و انتشار", {
            "fields": ("status", "review_notes", "reviewed_by", "reviewed_at", "created_song")
        }),
        ("اطلاعات ثبت", {
            "fields": ("submitter", "ip_hash", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def status_badge(self, obj):
        colors = {
            "pending": "orange",
            "reviewing": "blue",
            "approved": "green",
            "rejected": "red",
            "published": "purple",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "وضعیت"

    def has_audio(self, obj):
        return bool(obj.audio_320 or obj.audio_128 or obj.demo_url)
    has_audio.boolean = True
    has_audio.short_description = "فایل صوتی"

    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" width="120" height="120" style="border-radius: 8px;" />', obj.cover_image.url)
        return "—"
    cover_image_preview.short_description = "پیش‌نمایش کاور"

    def audio_320_player(self, obj):
        if obj.audio_320:
            return format_html('<audio controls src="{}"></audio>', obj.audio_320.url)
        return "—"
    audio_320_player.short_description = "پیش‌نمایش ۳۲۰"

    def audio_128_player(self, obj):
        if obj.audio_128:
            return format_html('<audio controls src="{}"></audio>', obj.audio_128.url)
        return "—"
    audio_128_player.short_description = "پیش‌نمایش ۱۲۸"

    actions = ["approve_selected", "reject_selected", "mark_reviewing"]

    def approve_selected(self, request, queryset):
        queryset.update(status="approved", reviewed_by=request.user, reviewed_at=timezone.now())
    approve_selected.short_description = "تأیید موارد انتخابی"

    def reject_selected(self, request, queryset):
        queryset.update(status="rejected", reviewed_by=request.user, reviewed_at=timezone.now())
    reject_selected.short_description = "رد موارد انتخابی"

    def mark_reviewing(self, request, queryset):
        queryset.update(status="reviewing", reviewed_by=request.user)
    mark_reviewing.short_description = "در حال بررسی"