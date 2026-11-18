from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core.utils import hash_ip, visitor_key


class PlayEvent(models.Model):
    class Quality(models.TextChoices):
        PREVIEW = "preview", "پیش‌نمایش"
        Q128 = "128", "۱۲۸"
        Q320 = "320", "۳۲۰"

    song = models.ForeignKey("music.Song", on_delete=models.CASCADE, related_name="play_events")
    user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="play_events"
    )
    session_key = models.CharField(max_length=64)
    quality = models.CharField(max_length=10, choices=Quality.choices, default=Quality.Q320)
    event_date = models.DateField(default=timezone.localdate, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "رویداد پخش"
        verbose_name_plural = "رویدادهای پخش"
        constraints = [
            models.UniqueConstraint(
                fields=["song", "session_key", "quality", "event_date"],
                name="unique_play_per_visitor_day",
            )
        ]
        indexes = [models.Index(fields=["-event_date", "song"])]

    def __str__(self):
        return f"{self.song} - {self.quality} - {self.event_date}"


class DownloadEvent(models.Model):
    song = models.ForeignKey("music.Song", on_delete=models.CASCADE, related_name="download_events")
    user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="download_events"
    )
    session_key = models.CharField(max_length=64)
    quality = models.CharField(
        max_length=15,
        choices=(("128", "۱۲۸"), ("320", "۳۲۰"), ("instrumental", "بی‌کلام"), ("lyrics", "متن ترانه")),
    )
    event_date = models.DateField(default=timezone.localdate, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "رویداد دانلود"
        verbose_name_plural = "رویدادهای دانلود"
        constraints = [
            models.UniqueConstraint(
                fields=["song", "session_key", "quality", "event_date"],
                name="unique_download_per_visitor_day",
            )
        ]
        indexes = [models.Index(fields=["-event_date", "song"])]

    def __str__(self):
        return f"{self.song} - {self.quality} - {self.event_date}"


class SongView(models.Model):
    song = models.ForeignKey("music.Song", on_delete=models.CASCADE, related_name="view_events")
    user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="song_views"
    )
    session_key = models.CharField(max_length=64)
    event_date = models.DateField(default=timezone.localdate, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "بازدید آهنگ"
        verbose_name_plural = "بازدیدهای آهنگ"
        constraints = [
            models.UniqueConstraint(
                fields=["song", "session_key", "event_date"], name="unique_view_per_visitor_day"
            )
        ]

    def __str__(self):
        return f"{self.song} - {self.event_date}"


class SearchLog(models.Model):
    query = models.CharField(max_length=200)
    results_count = models.PositiveIntegerField(default=0)
    session_key = models.CharField(max_length=64, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "جستجو"
        verbose_name_plural = "تاریخچه جستجو"
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self):
        return self.query


def _base_event_kwargs(request):
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    return {
        "user": user,
        "session_key": visitor_key(request),
        "ip_hash": hash_ip(request),
    }


def record_view(request, song) -> bool:
    from django.apps import apps

    if not isinstance(song, apps.get_model("music", "Song")):
        return False
    kwargs = _base_event_kwargs(request)
    _, created = SongView.objects.get_or_create(
        song=song,
        session_key=kwargs["session_key"],
        event_date=timezone.localdate(),
        defaults={"user": kwargs["user"], "ip_hash": kwargs["ip_hash"]},
    )
    if created:
        type(song).objects.filter(pk=song.pk).update(view_count=models.F("view_count") + 1)
        song.view_count += 1
    return created


def record_play(request, song, quality: str = "320") -> bool:
    kwargs = _base_event_kwargs(request)
    if quality not in {choice[0] for choice in PlayEvent.Quality.choices}:
        quality = "320"
    _, created = PlayEvent.objects.get_or_create(
        song=song,
        session_key=kwargs["session_key"],
        quality=quality,
        event_date=timezone.localdate(),
        defaults={
            "user": kwargs["user"],
            "ip_hash": kwargs["ip_hash"],
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:300],
        },
    )
    if created:
        type(song).objects.filter(pk=song.pk).update(play_count=models.F("play_count") + 1)
        song.play_count += 1
    return created


def record_download(request, song, quality: str) -> bool:
    kwargs = _base_event_kwargs(request)
    _, created = DownloadEvent.objects.get_or_create(
        song=song,
        session_key=kwargs["session_key"],
        quality=quality,
        event_date=timezone.localdate(),
        defaults={
            "user": kwargs["user"],
            "ip_hash": kwargs["ip_hash"],
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:300],
        },
    )
    if created:
        type(song).objects.filter(pk=song.pk).update(download_count=models.F("download_count") + 1)
        song.download_count += 1
    return created


def log_search(request, query: str, results_count: int) -> None:
    from django.core.cache import cache

    if not query or len(query) < 2:
        return
    key = f"searchlog:{visitor_key(request)}:{query[:60]}"
    if cache.get(key):
        return
    SearchLog.objects.create(
        query=query[:200],
        results_count=results_count,
        session_key=visitor_key(request),
        ip_hash=hash_ip(request),
    )
    cache.set(key, 1, 3600)
