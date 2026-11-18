from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap as sitemap_view_fn
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Count, Q, Sum
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView, View

from apps.albums.models import Album
from apps.artists.models import Artist
from apps.categories.models import Category
from apps.core.forms import ContactForm, NewsletterForm
from apps.core.models import ContactMessage, HomeBanner, HomeSection, SiteSettings, StaticPage
from apps.core.utils import hash_ip, visitor_key
from apps.music.models import Song
from apps.playlists.models import Playlist


def default_home_sections():
    """Fallback layout used when no HomeSection rows are configured yet."""
    return [
        HomeSection(
            section_type=HomeSection.Type.LATEST,
            title="تازه‌ترین انتشارها",
            subtitle="جدیدترین آهنگ‌های آوا",
            link_label="آرشیو آهنگ‌ها ←",
            link_url=reverse("music:list"),
            limit=6,
            order=1,
        ),
        HomeSection(
            section_type=HomeSection.Type.POPULAR,
            title="پیشنهاد شنیدنی",
            subtitle="پربازدیدترین آهنگ‌ها",
            link_label="همه آهنگ‌ها ←",
            link_url=reverse("music:list"),
            limit=4,
            order=2,
        ),
        HomeSection(
            section_type=HomeSection.Type.ARTISTS,
            title="هنرمندان",
            subtitle="خوانندگان و گروه‌های محبوب",
            link_label="همه هنرمندان ←",
            link_url=reverse("artists:list"),
            limit=4,
            order=3,
        ),
        HomeSection(
            section_type=HomeSection.Type.CATEGORIES,
            title="دسته‌بندی‌ها",
            subtitle="موسیقی را بر اساس سبک بشنوید",
            link_label="همه دسته‌ها ←",
            link_url=reverse("categories:list"),
            limit=6,
            order=4,
        ),
    ]


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        published = Song.objects.published()
        sections = list(HomeSection.objects.filter(is_active=True))
        if not sections:
            sections = default_home_sections()

        built_sections = []
        for section in sections:
            items = []
            if section.section_type == HomeSection.Type.LATEST:
                items = (
                    published.select_related("primary_artist")
                    .prefetch_related("artists", "categories")
                    .order_by("-published_at", "-created_at")[: section.limit]
                )
                template = "includes/music_post.html"
            elif section.section_type == HomeSection.Type.FEATURED:
                items = (
                    published.filter(is_featured=True)
                    .select_related("primary_artist")
                    .prefetch_related("artists", "categories")
                    .order_by("-published_at")[: section.limit]
                )
                template = "includes/song_card.html"
            elif section.section_type == HomeSection.Type.POPULAR:
                items = (
                    published.select_related("primary_artist")
                    .order_by("-view_count", "-published_at")[: section.limit]
                )
                template = "includes/song_card.html"
            elif section.section_type == HomeSection.Type.MOST_DOWNLOADED:
                items = (
                    published.select_related("primary_artist")
                    .order_by("-download_count", "-published_at")[: section.limit]
                )
                template = "includes/song_card.html"
            elif section.section_type == HomeSection.Type.MOST_PLAYED:
                items = (
                    published.select_related("primary_artist")
                    .order_by("-play_count", "-published_at")[: section.limit]
                )
                template = "includes/song_card.html"
            elif section.section_type == HomeSection.Type.ALBUMS:
                items = (
                    Album.objects.published()
                    .annotate(track_total=Count("tracks"))
                    .prefetch_related("artists")
                    .order_by("-release_date")[: section.limit]
                )
                template = "includes/album_card.html"
            elif section.section_type == HomeSection.Type.PLAYLISTS:
                items = (
                    Playlist.objects.public()
                    .annotate(track_total=Count("items"))
                    .order_by("-is_featured", "-created_at")[: section.limit]
                )
                template = "includes/album_card.html"
            elif section.section_type == HomeSection.Type.ARTISTS:
                items = (
                    Artist.objects.active()
                    .annotate(song_total=Count("songs", filter=Q(songs__is_published=True)))
                    .order_by("-is_featured", "-is_verified", "name")[: section.limit]
                )
                template = "includes/artist_card.html"
            elif section.section_type == HomeSection.Type.CATEGORIES:
                items = (
                    Category.objects.filter(is_active=True)
                    .annotate(song_total=Count("songs", filter=Q(songs__is_published=True)))
                    .order_by("order", "name")[: section.limit]
                )
                template = "includes/category_card.html"
            else:
                template = "includes/song_card.html"
            built_sections.append({"section": section, "items": items, "template": template})

        context.update(
            {
                "home_sections": built_sections,
                "hero_banner": HomeBanner.objects.filter(
                    placement=HomeBanner.Placement.HERO, is_active=True
                ).first(),
                "featured_song": published.filter(is_featured=True)
                .select_related("primary_artist")
                .order_by("-published_at")
                .first()
                or published.select_related("primary_artist").order_by("-published_at").first(),
                "latest_songs": published.select_related("primary_artist").order_by("-published_at")[:4],
                "popular_songs": published.select_related("primary_artist").order_by("-view_count", "-published_at")[:5],
                "sidebar_categories": Category.objects.filter(is_active=True)
                .annotate(song_total=Count("songs", filter=Q(songs__is_published=True)))
                .order_by("order", "name")[:8],
                "sidebar_artists": Artist.objects.active()
                .annotate(
                    song_total=Count("songs", filter=Q(songs__is_published=True)),
                    total_plays=Sum("songs__play_count", filter=Q(songs__is_published=True)),
                )
                .order_by("-is_featured", "-is_verified", "name")[:4],
                "latest_albums": Album.objects.published()
                .annotate(track_total=Count("tracks"))
                .prefetch_related("artists")
                .order_by("-release_date")[:3],
                "featured_playlists": Playlist.objects.public()
                .annotate(track_total=Count("items"))
                .order_by("-is_featured", "-created_at")[:3],
            }
        )
        return context


class StaticPageView(DetailView):
    model = StaticPage
    template_name = "pages/static_page.html"
    context_object_name = "page"

    def get_queryset(self):
        return StaticPage.objects.filter(is_published=True)

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()
        return get_object_or_404(queryset, slug=self.kwargs["slug"])


class ContactView(View):
    template_name = "pages/contact.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "form": ContactForm(),
                "page_title": "تماس با ما",
                "meta_description": "تماس با تحریریه آوا موزیک، ارسال اثر و پاسخ پرسش‌های متداول درباره انتشار موسیقی.",
            },
        )

    def post(self, request):
        key = f"contact:{hash_ip(request)}"
        attempts = cache.get(key, 0)
        if attempts >= 5:
            messages.error(request, "تعداد پیام‌های ارسالی بیش از حد مجاز است. کمی بعد دوباره تلاش کنید.")
            return render(request, self.template_name, {"form": ContactForm(request.POST)}, status=429)
        form = ContactForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ip_hash = hash_ip(request)
            obj.save()
            cache.set(key, attempts + 1, 3600)
            settings_obj = SiteSettings.load()
            if settings_obj.contact_email:
                try:
                    send_mail(
                        subject=f"[{settings_obj.site_name}] {obj.get_subject_display()}",
                        message=f"از: {obj.name} <{obj.email}>\n\n{obj.message}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings_obj.contact_email],
                        fail_silently=True,
                    )
                except Exception:
                    pass
            messages.success(request, "پیام شما ثبت شد. در اولین فرصت پاسخ می‌دهیم.")
            return redirect("core:contact")
        messages.error(request, "لطفاً خطاهای فرم را بررسی کنید.")
        return render(request, self.template_name, {"form": form}, status=400)


@require_POST
def subscribe(request):
    referer = request.META.get("HTTP_REFERER", "")
    target = referer if referer and "newsletter/subscribe" not in referer else reverse("core:home")
    form = NewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data["email"]
        from apps.core.models import NewsletterSubscriber

        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={"name": form.cleaned_data.get("name", ""), "source": "website"},
        )
        if not created:
            messages.info(request, "این ایمیل قبلاً در خبرنامه ثبت شده است.")
        else:
            messages.success(request, "عضویت شما در خبرنامه ثبت شد.")
        return redirect(target)

    messages.error(request, "ایمیل وارد شده معتبر نیست.")
    return redirect(target)


class ArchiveView(ListView):
    model = Song
    template_name = "pages/archive.html"
    context_object_name = "songs"
    paginate_by = 12

    def get_queryset(self):
        qs = Song.objects.published().select_related("primary_artist").prefetch_related("categories", "artists")

        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(categories__slug=category)

        artist = self.request.GET.get("artist")
        if artist:
            qs = qs.filter(artists__slug=artist)

        tag = self.request.GET.get("tag")
        if tag:
            qs = qs.filter(categories__name=tag)

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
        elif sort == "popular":
            qs = qs.order_by("-play_count", "-published_at")
        elif sort == "title":
            qs = qs.order_by("title")
        else:
            qs = qs.order_by("-published_at", "-created_at")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_category": self.request.GET.get("category", ""),
                "current_artist": self.request.GET.get("artist", ""),
                "current_tag": self.request.GET.get("tag", ""),
                "current_sort": self.request.GET.get("sort", "newest"),
                "query": self.request.GET.get("q", ""),
                "categories": Category.objects.filter(is_active=True).annotate(
                    song_total=Count("songs", filter=Q(songs__is_published=True))
                ),
                "artists": Artist.objects.active().annotate(
                    song_total=Count("songs", filter=Q(songs__is_published=True))
                ).order_by("-is_featured", "-song_total")[:20],
            }
        )
        return context


class SearchView(ListView):
    model = Song
    template_name = "pages/search.html"
    context_object_name = "songs"
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()
        self.query = query

        if not query:
            return Song.objects.none()

        from apps.analytics.models import log_search

        log_search(self.request, query, 0)

        qs = Song.objects.published().select_related("primary_artist").prefetch_related("categories", "artists")

        qs = qs.filter(
            Q(title__icontains=query)
            | Q(primary_artist__name__icontains=query)
            | Q(artists__name__icontains=query)
            | Q(lyrics__icontains=query)
            | Q(search_text__icontains=query)
            | Q(album_tracks__album__title__icontains=query)
        ).distinct()

        sort = self.request.GET.get("sort", "relevance")
        if sort == "views":
            qs = qs.order_by("-view_count")
        elif sort == "popular":
            qs = qs.order_by("-play_count")
        elif sort == "title":
            qs = qs.order_by("title")
        elif sort == "newest":
            qs = qs.order_by("-published_at")
        else:
            qs = qs.order_by("-is_featured", "-view_count", "-published_at")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = getattr(self, "query", "")

        if query:
            from apps.analytics.models import log_search

            total = context["paginator"].count if "paginator" in context else 0
            log_search(self.request, query, total)

        context.update(
            {
                "query": query,
                "result_count": context["paginator"].count if "paginator" in context else 0,
                "categories": Category.objects.filter(is_active=True).annotate(
                    song_total=Count("songs", filter=Q(songs__is_published=True))
                )[:10],
                "artists": Artist.objects.active().annotate(
                    song_total=Count("songs", filter=Q(songs__is_published=True))
                ).order_by("-song_total")[:10],
            }
        )
        return context


def health(request):
    return JsonResponse({"status": "ok", "time": timezone.now().isoformat()})


def media_serve(request, path: str):
    if settings.USE_S3:
        raise Http404("Media is served by object storage.")
    root = Path(settings.MEDIA_ROOT).resolve()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise Http404("File not found.")
    if not candidate.is_file():
        raise Http404("File not found.")
    content_type, _ = mimetypes.guess_type(str(candidate))
    if not content_type:
        content_type = "application/octet-stream"
    response = FileResponse(open(candidate, "rb"), content_type=content_type)
    response["Cache-Control"] = "public, max-age=86400"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)


song_sitemap = GenericSitemap(
    {
        "queryset": Song.objects.published(),
        "date_field": "updated_at",
    },
    priority=0.8,
    changefreq="weekly",
)

artist_sitemap = GenericSitemap(
    {
        "queryset": Artist.objects.active(),
        "date_field": "updated_at",
    },
    priority=0.7,
    changefreq="weekly",
)

album_sitemap = GenericSitemap(
    {
        "queryset": Album.objects.published(),
        "date_field": "updated_at",
    },
    priority=0.7,
    changefreq="weekly",
)

category_sitemap = GenericSitemap(
    {
        "queryset": Category.objects.filter(is_active=True),
        "date_field": "updated_at",
    },
    priority=0.6,
    changefreq="weekly",
)

playlist_sitemap = GenericSitemap(
    {
        "queryset": Playlist.objects.public(),
        "date_field": "updated_at",
    },
    priority=0.6,
    changefreq="weekly",
)

page_sitemap = GenericSitemap(
    {
        "queryset": StaticPage.objects.filter(is_published=True),
        "date_field": "updated_at",
    },
    priority=0.5,
    changefreq="monthly",
)

sitemaps = {
    "songs": song_sitemap,
    "artists": artist_sitemap,
    "albums": album_sitemap,
    "categories": category_sitemap,
    "playlists": playlist_sitemap,
    "pages": page_sitemap,
}


def sitemap_view(request):
    return sitemap_view_fn(request, sitemaps=sitemaps)


def robots_view(request):
    base = settings.SITE_BASE_URL or request.build_absolute_uri("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {base}/sitemap.xml",
        "",
        f"Host: {base}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def handler404(request, exception=None):
    from django.shortcuts import render
    context = {"site": SiteSettings.load()}
    return render(request, "404.html", context, status=404)


def handler500(request):
    from django.shortcuts import render
    context = {"site": SiteSettings.load()}
    return render(request, "500.html", context, status=500)