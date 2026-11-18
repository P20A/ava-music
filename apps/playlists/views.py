from __future__ import annotations

from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, ListView

from apps.analytics.models import record_view
from apps.playlists.models import Playlist


class PlaylistListView(ListView):
    model = Playlist
    template_name = "playlists/playlist_list.html"
    context_object_name = "playlists"
    paginate_by = 12

    def get_queryset(self):
        qs = Playlist.objects.public().annotate(
            track_total=Count("items"),
            total_duration=Sum("items__song__duration"),
        )

        sort = self.request.GET.get("sort", "newest")
        if sort == "popular":
            qs = qs.annotate(
                total_plays=Sum("items__song__play_count")
            ).order_by("-total_plays")
        elif sort == "title":
            qs = qs.order_by("name")
        else:
            qs = qs.order_by("-is_featured", "-created_at")

        return qs


class PlaylistDetailView(DetailView):
    model = Playlist
    template_name = "playlists/playlist_detail.html"
    context_object_name = "playlist"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Playlist.objects.public().prefetch_related(
            "items__song__primary_artist", "items__song__categories"
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_view(request, self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        playlist = self.object

        items = playlist.items.select_related("song__primary_artist").all()

        related_playlists = (
            Playlist.objects.public()
            .exclude(pk=playlist.pk)
            .annotate(track_total=Count("items"))
            .order_by("-is_featured", "-created_at")[:4]
        )

        context.update(
            {
                "items": items,
                "related_playlists": related_playlists,
                "total_duration": sum(item.song.duration for item in items),
            }
        )
        return context


@require_GET
def playlist_play(request, slug):
    playlist = get_object_or_404(Playlist.objects.public(), slug=slug)
    return JsonResponse({"status": "ok"})