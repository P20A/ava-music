from django.test import TestCase, Client
from django.urls import reverse
from apps.music.models import Song
from apps.artists.models import Artist
from apps.albums.models import Album


class CorePagesTests(TestCase):
    def test_home_200(self):
        r = self.client.get(reverse("core:home"))
        self.assertEqual(r.status_code, 200)

    def test_archive_200(self):
        r = self.client.get(reverse("core:archive"))
        self.assertEqual(r.status_code, 200)

    def test_contact_200(self):
        r = self.client.get(reverse("core:contact"))
        self.assertEqual(r.status_code, 200)


class MusicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artist = Artist.objects.create(name="Test Artist", slug="test-artist")
        cls.song = Song.objects.create(
            title="Test Song", slug="test-song", primary_artist=cls.artist,
            is_published=True, publication_authorized=True,
            content_removal_requested=False,
        )

    def test_song_list_200(self):
        r = self.client.get(reverse("music:list"))
        self.assertEqual(r.status_code, 200)

    def test_song_detail_200(self):
        r = self.client.get(self.song.get_absolute_url())
        self.assertEqual(r.status_code, 200)

    def test_like_endpoint(self):
        r = self.client.post(reverse("music:like", args=[self.song.slug]))
        self.assertEqual(r.status_code, 200)
        self.assertIn("liked", r.json())


class AlbumTests(TestCase):
    def test_album_list_200(self):
        r = self.client.get(reverse("albums:list"))
        self.assertEqual(r.status_code, 200)


class ArtistTests(TestCase):
    def test_artist_list_200(self):
        r = self.client.get(reverse("artists:list"))
        self.assertEqual(r.status_code, 200)
