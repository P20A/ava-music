from django.contrib import admin
from django.utils.html import format_html

from apps.advertisements.models import Advertisement


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = (
        "title", "placement", "image_preview", "priority", "is_live_status",
        "click_count", "impression_count", "start_date", "end_date", "is_active"
    )
    list_filter = ("placement", "is_active", "open_new_tab")
    list_editable = ("priority", "is_active")
    search_fields = ("title", "description", "destination_url")
    readonly_fields = ("click_count", "impression_count", "created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": ("title", "placement", "description")
        }),
        ("رسانه", {
            "fields": ("image", "alt_text")
        }),
        ("لینک و رفتار", {
            "fields": ("destination_url", "open_new_tab")
        }),
        ("زمان‌بندی", {
            "fields": ("start_date", "end_date")
        }),
        ("تنظیمات نمایش", {
            "fields": ("is_active", "priority")
        }),
        ("آمار", {
            "fields": ("click_count", "impression_count"),
            "classes": ("collapse",)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="30" style="border-radius: 4px;" />', obj.image.url)
        return "—"
    image_preview.short_description = "بنر"

    def is_live_status(self, obj):
        if obj.is_live:
            return format_html('<span style="color: green;">● فعال</span>')
        return format_html('<span style="color: gray;">○ غیرفعال</span>')
    is_live_status.short_description = "وضعیت"