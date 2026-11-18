from __future__ import annotations

from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from apps.analytics.models import record_view
from apps.artists.models import Artist, ArtistFollow
from apps.albums.models import Album
from apps.core.utils import visitor_key
from apps.music.models import Song


class ArtistListView(ListView):
    model = Artist
    template_name = "artists/artist_list.html"
    context_object_name = "artists"
    paginate_by = 8

    def get_queryset(self):
        qs = Artist.objects.active().annotate(
            song_total=Count("songs", filter=Q(songs__is_published=True)),
            album_total=Count("albums", filter=Q(albums__is_published=True)),
            total_plays=Sum("songs__play_count"),
        )

        sort = self.request.GET.get("sort", "popular")
        if sort == "newest":
            qs = qs.order_by("-created_at")
        elif sort == "songs":
            qs = qs.order_by("-song_total")
        else:
            qs = qs.order_by("-is_featured", "-is_verified", "-song_total", "name")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_sort": self.request.GET.get("sort", "popular"),
                "total_albums": Album.objects.published().count(),
                "total_songs": Song.objects.published().count(),
            }
        )
        return context


class ArtistDetailView(DetailView):
    model = Artist
    template_name = "artists/artist_detail.html"
    context_object_name = "artist"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Artist.objects.active().prefetch_related(
            "songs__categories", "albums", "song_credits__song"
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_view(request, self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        artist = self.object

        tab = self.request.GET.get("tab", "songs")

        songs = artist.songs.filter(is_published=True).select_related(
            "primary_artist"
        ).prefetch_related("categories")[:20]

        albums = artist.albums.filter(is_published=True).prefetch_related("tracks__song")[:10]

        popular_songs = artist.songs.filter(is_published=True).order_by(
            "-view_count"
        )[:5]

        category_ids = (
            artist.songs.filter(is_published=True).values_list("categories", flat=True).distinct()
        )

        similar_artists = (
            Artist.objects.active()
            .filter(songs__categories__in=category_ids)
            .exclude(pk=artist.pk)
            .distinct()
            .annotate(song_total=Count("songs", filter=Q(songs__is_published=True)))
            .order_by("-is_featured", "-song_total")[:6]
        )

        context.update(
            {
                "current_tab": tab,
                "songs": songs,
                "albums": albums,
                "popular_songs": popular_songs,
                "similar_artists": similar_artists,
                "is_following": self._is_following(artist),
            }
        )
        return context

    def _is_following(self, artist):
        user = self.request.user
        if user.is_authenticated:
            return artist.followers.filter(user=user).exists()
        session_key = visitor_key(self.request)
        if session_key.startswith("session:"):
            return artist.followers.filter(session_key=session_key).exists()
        return False


@require_POST
def artist_follow(request, slug):
    artist = get_object_or_404(Artist.objects.active(), slug=slug)

    user = request.user if request.user.is_authenticated else None
    session_key = visitor_key(request) if not user else ""

    if user:
        follow, created = ArtistFollow.objects.get_or_create(artist=artist, user=user)
    else:
        follow, created = ArtistFollow.objects.get_or_create(
            artist=artist, session_key=session_key
        )

    if not created:
        follow.delete()
        following = False
    else:
        following = True

    return JsonResponse(
        {
            "following": following,
            "follower_count": artist.follower_count,
        }
    )


def artist_songs(request, slug):
    artist = get_object_or_404(Artist.objects.active(), slug=slug)
    songs = artist.songs.filter(is_published=True).select_related("primary_artist").prefetch_related("categories")

    from django.core.paginator import Paginator

    paginator = Paginator(songs, 12)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(
        request,
        "artists/artist_songs.html",
        {"artist": artist, "page_obj": page_obj, "songs": page_obj.object_list},
    )


def artist_albums(request, slug):
    artist = get_object_or_404(Artist.objects.active(), slug=slug)
    albums = artist.albums.filter(is_published=True).prefetch_related("tracks__song")

    from django.core.paginator import Paginator

    paginator = Paginator(albums, 12)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return render(
        request,
        "artists/artist_albums.html",
        {"artist": artist, "page_obj": page_obj, "albums": page_obj.object_list},
    )