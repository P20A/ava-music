from django.contrib import admin

from apps.seo.models import Redirect, SEOConfig, SitemapEntry


@admin.register(SEOConfig)
class SEOConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ("پیش‌فرض‌ها", {
            "fields": ("site_name", "default_title", "default_description", "default_keywords", "default_og_image")
        }),
        ("رصد و تحلیل", {
            "fields": ("twitter_site", "google_analytics_id", "google_search_console")
        }),
        ("ربات‌ها", {
            "fields": ("robots_txt",)
        }),
    )

    def has_add_permission(self, request):
        return not SEOConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    list_display = ("old_path", "new_path", "is_permanent", "hits", "created_at", "last_hit_at")
    list_filter = ("is_permanent",)
    search_fields = ("old_path", "new_path")
    readonly_fields = ("hits", "created_at", "last_hit_at")
    date_hierarchy = "created_at"


@admin.register(SitemapEntry)
class SitemapEntryAdmin(admin.ModelAdmin):
    list_display = ("url", "changefreq", "priority", "is_active", "lastmod")
    list_filter = ("changefreq", "is_active")
    list_editable = ("priority", "is_active")
    search_fields = ("url",)