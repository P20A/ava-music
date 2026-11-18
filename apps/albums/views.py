from __future__ import annotations

from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, ListView

from apps.albums.models import Album, AlbumTrack
from apps.analytics.models import record_view
from apps.core.utils import fa_number


class AlbumListView(ListView):
    model = Album
    template_name = "albums/album_list.html"
    context_object_name = "albums"
    paginate_by = 12

    def get_queryset(self):
        qs = Album.objects.published().annotate(
            track_total=Count("tracks"),
            total_duration=Sum("tracks__song__duration"),
        ).prefetch_related("artists")

        album_type = self.request.GET.get("type")
        if album_type:
            qs = qs.filter(album_type=album_type)

        sort = self.request.GET.get("sort", "newest")
        if sort == "popular":
            qs = qs.annotate(
                total_plays=Sum("tracks__song__play_count")
            ).order_by("-total_plays")
        elif sort == "title":
            qs = qs.order_by("title")
        else:
            qs = qs.order_by("-release_date", "-created_at")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_type": self.request.GET.get("type", ""),
                "current_sort": self.request.GET.get("sort", "newest"),
            }
        )
        return context


class AlbumDetailView(DetailView):
    model = Album
    template_name = "albums/album_detail.html"
    context_object_name = "album"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Album.objects.published().prefetch_related(
            "artists", "tracks__song__primary_artist", "tracks__song__categories"
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_view(request, self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.object

        tracks = album.tracks.select_related("song__primary_artist").all()

        related_albums = (
            Album.objects.published()
            .filter(artists__in=album.artists.all())
            .exclude(pk=album.pk)
            .distinct()
            .annotate(track_total=Count("tracks"))
            .prefetch_related("artists")
            .order_by("-is_featured", "-release_date")[:4]
        )

        context.update(
            {
                "tracks": tracks,
                "related_albums": related_albums,
                "total_duration": sum(t.song.duration for t in tracks),
            }
        )
        return context


@require_GET
def album_play(request, slug):
    album = get_object_or_404(Album.objects.published(), slug=slug)
    return JsonResponse({"status": "ok"})


@require_GET
def album_download(request, slug):
    album = get_object_or_404(Album.objects.published(), slug=slug)
    return JsonResponse({"status": "ok", "message": "دانلود آلبوم در نسخه کامل فعال است"})