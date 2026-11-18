from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.StaticPageView.as_view(), {"slug": "about"}, name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("archive/", views.ArchiveView.as_view(), name="archive"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("page/<uslug:slug>/", views.StaticPageView.as_view(), name="page"),
    path("newsletter/subscribe/", views.subscribe, name="subscribe"),
    path("health/", views.health, name="health"),
    path("sitemap.xml", views.sitemap_view, name="sitemap"),
    path("robots.txt", views.robots_view, name="robots"),
]