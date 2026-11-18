from django.urls import path

from apps.albums import views

app_name = "albums"

urlpatterns = [
    path("", views.AlbumListView.as_view(), name="list"),
    path("<uslug:slug>/", views.AlbumDetailView.as_view(), name="detail"),
    path("<uslug:slug>/play/", views.album_play, name="play"),
    path("<uslug:slug>/download/", views.album_download, name="download"),
]