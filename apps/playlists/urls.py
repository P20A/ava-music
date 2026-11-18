from django.urls import path

from apps.playlists import views

app_name = "playlists"

urlpatterns = [
    path("", views.PlaylistListView.as_view(), name="list"),
    path("<uslug:slug>/", views.PlaylistDetailView.as_view(), name="detail"),
    path("<uslug:slug>/play/", views.playlist_play, name="play"),
]