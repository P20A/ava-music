from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.db.models import Count, Q
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    HttpResponseNotModified,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, ListView

from apps.analytics.models import record_download, record_play, record_view
from apps.core.models import SiteSettings
from apps.core.utils import fa_number, hash_ip, visitor_key
from apps.music.models import Comment, Song, SongLike


class SongListView(ListView):
    model = Song
    template_name = "music/song_list.html"
    context_object_name = "songs"
    paginate_by = 12

    def get_queryset(self):
        qs = Song.objects.published().select_related("primary_artist").prefetch_related(
            "artists", "categories"
        )

        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(categories__slug=category)

        artist = self.request.GET.get("artist")
        if artist:
            qs = qs.filter(artists__slug=artist)

        query = self.request.GET.get("q")
        if query:
            normalized = query.strip()
            qs = qs.filter(
                Q(title__icontains=normalized)
                | Q(primary_artist__name__icontains=normalized)
                | Q(artists__name__icontains=normalized)
                | Q(lyrics__icontains=normalized)
                | Q(search_text__icontains=normalized)
            ).distinct()

        sort = self.request.GET.get("sort", "newest")
        if sort == "views":
            qs = qs.order_by("-view_count", "-published_at")
        elif sort == "title":
            qs = qs.order_by("title")
        elif sort == "popular":
            qs = qs.order_by("-play_count", "-published_at")
        else:
            qs = qs.order_by("-published_at", "-created_at")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_category": self.request.GET.get("category", ""),
                "current_artist": self.request.GET.get("artist", ""),
                "current_sort": self.request.GET.get("sort", "newest"),
                "query": self.request.GET.get("q", ""),
                "categories": self._get_categories(),
            }
        )
        return context

    def _get_categories(self):
        from apps.categories.models import Category

        return Category.objects.filter(is_active=True).annotate(
            song_total=Count("songs", filter=Q(songs__is_published=True))
        )


class SongDetailView(DetailView):
    model = Song
    template_name = "music/song_detail.html"
    context_object_name = "song"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Song.objects.published().select_related("primary_artist").prefetch_related(
            "artists", "categories", "album_tracks__album", "artist_credits__artist"
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_view(request, self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song = self.object

        related = (
            Song.objects.published()
            .filter(
                Q(categories__in=song.categories.all())
                | Q(artists__in=song.artists.all())
            )
            .exclude(pk=song.pk)
            .distinct()
            .select_related("primary_artist")
            .order_by("-is_featured", "-play_count", "-published_at")[:4]
        )

        comments = song.comments.filter(is_approved=True, parent__isnull=True).select_related(
            "user"
        )[:10]

        settings_obj = self._get_settings()
        context.update(
            {
                "related_songs": related,
                "comments": comments,
                "featured_artists": [
                    credit.artist
                    for credit in song.artist_credits.select_related("artist").all()
                    if credit.role != credit.Role.PRIMARY
                ],
                "albums": song.album_tracks.select_related("album").all(),
                "can_download": settings_obj,
            }
        )
        return context

    def _get_settings(self):
        from apps.core.models import SiteSettings

        return SiteSettings.load().downloads_enabled


@require_GET
def song_play(request, slug):
    song = get_object_or_404(Song.objects.published(), slug=slug)
    quality = request.GET.get("quality", "320")
    record_play(request, song, quality)
    return JsonResponse({"status": "ok"})


def song_stream(request, slug):
    song = get_object_or_404(Song.objects.published(), slug=slug)
    quality = request.GET.get("quality", "320")

    field_map = {
        "preview": song.preview_audio,
        "320": song.audio_320,
        "128": song.audio_128,
        "instrumental": song.instrumental_audio,
    }

    audio_file = field_map.get(quality) or song.best_audio
    if not audio_file:
        raise Http404("فایل صوتی موجود نیست")

    path = Path(audio_file.path).resolve()
    media_root = Path(settings.MEDIA_ROOT).resolve()

    try:
        path.relative_to(media_root)
    except ValueError:
        raise Http404("فایل یافت نشد")

    if not path.is_file():
        raise Http404("فایل یافت نشد")

    content_type, _ = mimetypes.guess_type(str(path))
    if not content_type:
        content_type = "audio/mpeg"

    range_header = request.META.get("HTTP_RANGE")
    file_size = path.stat().st_size

    if range_header:
        start, end = _parse_range(range_header, file_size)
        if start is None:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{file_size}"
            return response

        length = end - start + 1
        response = HttpResponse(status=206, content_type=content_type)
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Content-Length"] = str(length)
        response["Accept-Ranges"] = "bytes"
        response["Cache-Control"] = "public, max-age=3600"

        def file_iterator(file_path, start_byte, length_bytes):
            with open(file_path, "rb") as f:
                f.seek(start_byte)
                remaining = length_bytes
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        response.streaming_content = file_iterator(path, start, length)
        return response

    if_none_match = request.META.get("HTTP_IF_NONE_MATCH")
    etag = f'"{path.stat().st_mtime:.0f}-{file_size}"'
    if if_none_match == etag:
        return HttpResponseNotModified()

    response = FileResponse(open(path, "rb"), content_type=content_type)
    response["Content-Length"] = str(file_size)
    response["Accept-Ranges"] = "bytes"
    response["ETag"] = etag
    response["Cache-Control"] = "public, max-age=3600"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def _parse_range(range_header: str, file_size: int):
    if not range_header.startswith("bytes="):
        return None, None
    range_str = range_header[6:]
    parts = range_str.split("-")
    if len(parts) != 2:
        return None, None

    start_str, end_str = parts
    try:
        start = int(start_str) if start_str else 0
    except ValueError:
        return None, None

    if end_str:
        try:
            end = int(end_str)
        except ValueError:
            return None, None
    else:
        end = file_size - 1

    if start > end or start >= file_size or end >= file_size:
        return None, None

    return start, end


@require_GET
def song_download(request, slug, quality):
    song = get_object_or_404(Song.objects.published(), slug=slug)

    if quality == "320":
        audio_file = song.audio_320
        filename = f"{song.slug}-320.mp3"
    elif quality == "128":
        audio_file = song.audio_128
        filename = f"{song.slug}-128.mp3"
    elif quality == "instrumental":
        audio_file = song.instrumental_audio
        filename = f"{song.slug}-instrumental.mp3"
    elif quality == "lyrics":
        if not song.lyrics:
            raise Http404("متن ترانه موجود نیست")
        from django.http import HttpResponse

        response = HttpResponse(song.lyrics, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{song.slug}-lyrics.txt"'
        return response
    else:
        raise Http404("کیفیت نامعتبر")

    if not audio_file:
        raise Http404(f"فایل {quality} موجود نیست")

    record_download(request, song, quality)

    path = Path(audio_file.path).resolve()
    media_root = Path(settings.MEDIA_ROOT).resolve()

    try:
        path.relative_to(media_root)
    except ValueError:
        raise Http404("فایل یافت نشد")

    if not path.is_file():
        raise Http404("فایل یافت نشد")

    content_type, _ = mimetypes.guess_type(str(path))
    if not content_type:
        content_type = "audio/mpeg"

    response = FileResponse(open(path, "rb"), content_type=content_type)
    response["Content-Length"] = str(path.stat().st_size)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def song_lyrics(request, slug):
    song = get_object_or_404(Song.objects.published(), slug=slug)
    if not song.lyrics:
        return JsonResponse({"lyrics": "", "has_lyrics": False})
    return JsonResponse({"lyrics": song.lyrics, "has_lyrics": True})


@require_POST
def song_like(request, slug):
    song = get_object_or_404(Song.objects.published(), slug=slug)
    user = request.user if request.user.is_authenticated else None
    session_key = "" if user else visitor_key(request)
    lookup = {"song": song, "user": user} if user else {"song": song, "session_key": session_key}
    like, created = SongLike.objects.get_or_create(**lookup)
    if not created:
        like.delete()
    count = song.likes.count()
    Song.objects.filter(pk=song.pk).update(like_count=count)
    return JsonResponse({"liked": created, "count": count, "count_fa": fa_number(count)})


@require_POST
def song_comment(request, slug):
    song = get_object_or_404(Song.objects.published(), slug=slug)
    site = SiteSettings.load()
    if not site.comments_enabled:
        return JsonResponse({"ok": False, "error": "ارسال دیدگاه در حال حاضر غیرفعال است."}, status=403)

    body = (request.POST.get("body") or "").strip()
    if len(body) < 3:
        return JsonResponse({"ok": False, "error": "متن دیدگاه را کامل بنویسید."}, status=400)

    fallback_name = request.user.get_full_name() or request.user.username if request.user.is_authenticated else ""
    name = (request.POST.get("name") or fallback_name or "کاربر مهمان").strip()[:120]
    email = (request.POST.get("email") or "").strip()

    comment = Comment.objects.create(
        song=song,
        user=request.user if request.user.is_authenticated else None,
        name=name,
        email=email,
        body=body,
        is_approved=True,
        ip_hash=hash_ip(request),
    )
    return JsonResponse(
        {
            "ok": True,
            "name": comment.name,
            "body": comment.body,
            "initial": comment.initial,
            "url": song.get_absolute_url(),
        }
    )


@require_GET
def related_songs_api(request, slug):
    song = get_object_or_404(Song.objects.published(), slug=slug)
    related = (
        Song.objects.published()
        .filter(
            Q(categories__in=song.categories.all())
            | Q(artists__in=song.artists.all())
        )
        .exclude(pk=song.pk)
        .distinct()
        .select_related("primary_artist")
        .order_by("-is_featured", "-play_count", "-published_at")[:8]
    )

    data = [
        {
            "title": s.title,
            "slug": s.slug,
            "artist": s.primary_artist.name if s.primary_artist else "",
            "cover_url": s.cover_image.url if s.cover_image else "",
            "duration": s.duration,
            "url": s.get_absolute_url(),
        }
        for s in related
    ]
    return JsonResponse({"results": data})