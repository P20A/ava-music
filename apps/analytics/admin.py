from django.contrib import admin

from apps.analytics.models import DownloadEvent, PlayEvent, SearchLog, SongView


@admin.register(PlayEvent)
class PlayEventAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "quality", "event_date", "created_at")
    list_filter = ("quality", "event_date")
    search_fields = ("song__title", "user__username")
    readonly_fields = ("created_at",)
    date_hierarchy = "event_date"


@admin.register(DownloadEvent)
class DownloadEventAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "quality", "event_date", "created_at")
    list_filter = ("quality", "event_date")
    search_fields = ("song__title", "user__username")
    readonly_fields = ("created_at",)
    date_hierarchy = "event_date"


@admin.register(SongView)
class SongViewAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "event_date", "created_at")
    list_filter = ("event_date",)
    search_fields = ("song__title", "user__username")
    readonly_fields = ("created_at",)
    date_hierarchy = "event_date"


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ("query", "results_count", "session_key", "created_at")
    search_fields = ("query",)
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"