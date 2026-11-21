# آوا | AVA Music Archive

Django 5.2 backend for the Persian (RTL) music site «آوا موزیک» — song/album/artist archive with streaming, downloads, likes, comments, follows, submissions, and a persistent mini-player.

## Stack

- Django 5.2.19, PostgreSQL (prod) / SQLite (dev)
- Gunicorn, WhiteNoise, Pillow, mutagen, jdatetime, python-dotenv
- Optional: django-storages[boto3] for S3 media

## Setup (dev)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Environment variables (`.env`): `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `MEDIA_ROOT`.

## Apps

`core`, `music`, `artists`, `albums`, `categories`, `playlists`, `users`, `submissions`, `advertisements`, `analytics`.

## Key URLs

- `/` home, `/songs/`, `/albums/`, `/artists/`, `/archive/`
- `/songs/<slug>/` song detail + stream `/songs/<slug>/stream/`
- Password reset: `/users/password/reset/`
- Admin: `/admin/` (superuser admin/admin123 in dev)

## Tests

```bash
python manage.py check
python manage.py test
```
