from django.contrib import admin
from django.utils.html import format_html

from apps.core.models import (
    ContactMessage,
    HomeBanner,
    HomeSection,
    NavigationLink,
    NewsletterSubscriber,
    Redirect,
    SiteSettings,
    StaticPage,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("اطلاعات پایه", {
            "fields": ("site_name", "site_tagline", "site_description")
        }),
        ("برندینگ", {
            "fields": ("logo", "favicon", "default_share_image", "theme_color")
        }),
        ("تماس و آدرس", {
            "fields": ("contact_email", "contact_phone", "address", "working_hours")
        }),
        ("شبکه‌های اجتماعی", {
            "fields": ("instagram", "telegram", "twitter", "youtube", "spotify", "whatsapp")
        }),
        ("فوتر", {
            "fields": ("footer_about", "footer_copyright")
        }),
        ("SEO پیش‌فرض", {
            "fields": ("default_seo_title", "default_seo_description", "default_keywords", "google_analytics_id")
        }),
        ("تنظیمات سایت", {
            "fields": ("posts_per_page", "ads_enabled", "comments_enabled", "submissions_enabled", "downloads_enabled", "registration_enabled", "maintenance_mode")
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NavigationLink)
class NavigationLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "location", "url", "order", "is_active", "open_new_tab")
    list_filter = ("location", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("label", "url")


@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "section_type", "limit", "order", "is_active")
    list_filter = ("section_type", "is_active")
    list_editable = ("order", "is_active", "limit")
    search_fields = ("title", "subtitle")


@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    list_display = ("title", "placement", "order", "is_active", "is_live", "start_date", "end_date")
    list_filter = ("placement", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "subtitle")
    readonly_fields = ("created_at",)

    def is_live(self, obj):
        if obj.is_live:
            return format_html('<span style="color: green;">● زنده</span>')
        return format_html('<span style="color: gray;">○ غیرفعال</span>')
    is_live.short_description = "وضعیت"


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "show_in_footer", "created_at")
    list_filter = ("is_published", "show_in_footer")
    list_editable = ("is_published", "show_in_footer")
    search_fields = ("title", "slug", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "created_at")
    list_filter = ("subject", "is_read")
    list_editable = ("is_read",)
    search_fields = ("name", "email", "message")
    readonly_fields = ("ip_hash", "created_at")
    date_hierarchy = "created_at"

    actions = ["mark_as_read", "mark_as_unread"]

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "علامت‌گذاری به عنوان خوانده شده"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "علامت‌گذاری به عنوان خوانده نشده"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_active", "source", "created_at")
    list_filter = ("is_active", "source")
    list_editable = ("is_active",)
    search_fields = ("email", "name")
    readonly_fields = ("token", "created_at")
    date_hierarchy = "created_at"


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    list_display = ("old_path", "new_path", "is_permanent", "hits", "created_at", "last_hit_at")
    list_filter = ("is_permanent",)
    search_fields = ("old_path", "new_path")
    readonly_fields = ("hits", "created_at", "last_hit_at")
    date_hierarchy = "created_at"