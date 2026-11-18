from django.urls import path

from apps.artists import views

app_name = "artists"

urlpatterns = [
    path("", views.ArtistListView.as_view(), name="list"),
    path("<uslug:slug>/", views.ArtistDetailView.as_view(), name="detail"),
    path("<uslug:slug>/follow/", views.artist_follow, name="follow"),
    path("<uslug:slug>/songs/", views.artist_songs, name="songs"),
    path("<uslug:slug>/albums/", views.artist_albums, name="albums"),
]