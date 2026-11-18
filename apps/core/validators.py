"""Reusable file validators for audio, images and documents."""
from __future__ import annotations

import os

from django.conf import settings
from django.core.exceptions import ValidationError

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".flac"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".zip"}

AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/aac",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/flac",
    "application/octet-stream",
}


def _extension(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower()


def validate_audio_file(file):
    if not file:
        return
    name = getattr(file, "name", "")
    if _extension(name) not in AUDIO_EXTENSIONS:
        raise ValidationError(
            "فرمت فایل صوتی مجاز نیست. فایل‌های MP3، M4A، WAV، OGG یا FLAC پذیرفته می‌شوند."
        )
    content_type = getattr(file, "content_type", "") or ""
    if content_type and content_type not in AUDIO_CONTENT_TYPES:
        raise ValidationError("نوع محتوای فایل صوتی معتبر نیست.")
    size = getattr(file, "size", 0) or 0
    limit = getattr(settings, "MAX_AUDIO_UPLOAD_SIZE", 80 * 1024 * 1024)
    if size > limit:
        raise ValidationError(f"حجم فایل صوتی نباید بیشتر از {limit // (1024 * 1024)} مگابایت باشد.")


def validate_image_file(file):
    if not file:
        return
    name = getattr(file, "name", "")
    extension = _extension(name)
    if extension not in IMAGE_EXTENSIONS:
        raise ValidationError("فرمت تصویر مجاز نیست. JPG، PNG، WebP، GIF یا SVG انتخاب کنید.")
    size = getattr(file, "size", 0) or 0
    limit = getattr(settings, "MAX_IMAGE_UPLOAD_SIZE", 8 * 1024 * 1024)
    if size > limit:
        raise ValidationError(f"حجم تصویر نباید بیشتر از {limit // (1024 * 1024)} مگابایت باشد.")
    if extension != ".svg":
        try:
            from PIL import Image

            position = file.tell() if hasattr(file, "tell") else None
            Image.open(file).verify()
            if position is not None and hasattr(file, "seek"):
                file.seek(position)
        except Exception as exc:  # Pillow raises several exception types
            raise ValidationError("فایل تصویر معتبر نیست یا آسیب دیده است.") from exc


def validate_document_file(file):
    if not file:
        return
    if _extension(getattr(file, "name", "")) not in DOCUMENT_EXTENSIONS:
        raise ValidationError("فقط PDF، تصویر یا فایل ZIP برای مدارک مجاز است.")
    size = getattr(file, "size", 0) or 0
    if size > 20 * 1024 * 1024:
        raise ValidationError("حجم مدرک نباید بیشتر از ۲۰ مگابایت باشد.")


def audio_duration_seconds(path: str) -> int | None:
    """Read duration with mutagen without loading the audio into memory."""
    try:
        from mutagen import File as MutagenFile

        media = MutagenFile(path)
        if media is not None and media.info is not None and media.info.length:
            return int(round(media.info.length))
    except Exception:
        return None
    return None
