"""URL configuration for AVA Music Archive."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, register_converter
from django.views.generic import TemplateView

from apps.core import views as core_views
from project.converters import UnicodeSlugConverter

register_converter(UnicodeSlugConverter, "uslug")

handler404 = core_views.handler404
handler500 = core_views.handler500

urlpatterns = [
    path(settings.ADMIN_URL.lstrip("/"), admin.site.urls),
    path("", include("apps.core.urls")),
    path("users/", include("apps.users.urls")),
    path("artists/", include("apps.artists.urls")),
    path("categories/", include("apps.categories.urls")),
    path("songs/", include("apps.music.urls")),
    path("albums/", include("apps.albums.urls")),
    path("playlists/", include("apps.playlists.urls")),
    path("ads/", include("apps.advertisements.urls")),
    path("submissions/", include("apps.submissions.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("sitemap.xml", core_views.sitemap_view, name="sitemap"),
    path("robots.txt", core_views.robots_view, name="robots"),
    path("health/", core_views.health, name="health"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)