from django.urls import path

from apps.music import views

app_name = "music"

urlpatterns = [
    path("", views.SongListView.as_view(), name="list"),
    path("<uslug:slug>/", views.SongDetailView.as_view(), name="detail"),
    path("<uslug:slug>/play/", views.song_play, name="play"),
    path("<uslug:slug>/download/<str:quality>/", views.song_download, name="download"),
    path("<uslug:slug>/lyrics/", views.song_lyrics, name="lyrics"),
    path("<uslug:slug>/stream/", views.song_stream, name="stream"),
    path("<uslug:slug>/like/", views.song_like, name="like"),
    path("<uslug:slug>/comment/", views.song_comment, name="comment"),
    path("api/related/<uslug:slug>/", views.related_songs_api, name="related_api"),
]