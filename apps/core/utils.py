"""Persian text, number and Jalali date helpers used across the project."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime

from django.utils import timezone

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_TO_PERSIAN = {"ي": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "ؤ": "و", "إ": "ا", "أ": "ا", "آ": "آ"}
ZWNJ = "\u200c"
DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
WHITESPACE = re.compile(r"\s+")

JALALI_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]


def to_persian_digits(value: object) -> str:
    return str(value).translate(str.maketrans("0123456789", PERSIAN_DIGITS))


def to_ascii_digits(value: object) -> str:
    text = str(value)
    for index, digit in enumerate(PERSIAN_DIGITS):
        text = text.replace(digit, str(index))
    return text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))


def normalize_fa(text: str | None) -> str:
    """Normalise Persian/Arabic input for case-insensitive searching.

    Handles Arabic yeh/kaf, half-spaces, diacritics, tatweel, Persian digits and
    repeated whitespace.  The result is intentionally stable so it can be
    persisted in a search column.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text)).lower()
    for source, target in ARABIC_TO_PERSIAN.items():
        text = text.replace(source, target)
    text = text.replace("\u0640", "")
    text = DIACRITICS.sub("", text)
    text = text.replace(ZWNJ, " ")
    text = to_ascii_digits(text)
    return WHITESPACE.sub(" ", text).strip()


def fa_number(value: object, compact: bool = False) -> str:
    """Format a number with Persian digits and separators."""
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return to_persian_digits(value)
    if compact:
        absolute = abs(number)
        if absolute >= 1_000_000:
            formatted = f"{number / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
        elif absolute >= 1_000:
            formatted = f"{number / 1_000:.1f}".rstrip("0").rstrip(".") + "k"
        else:
            formatted = str(int(number))
        return to_persian_digits(formatted)
    if number == int(number):
        formatted = f"{int(number):,}".replace(",", "٬")
    else:
        formatted = f"{number:,.1f}".replace(",", "٬")
    return to_persian_digits(formatted)


def fa_duration(seconds: int | None) -> str:
    seconds = max(0, int(seconds or 0))
    return f"{to_persian_digits(seconds // 60)}:{to_persian_digits(str(seconds % 60).zfill(2))}"


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """Convert a Gregorian date to the Solar Hijri calendar (algorithmic)."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        365 * gy
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
        - 80
        + gd
        + g_d_m[gm - 1]
    )
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def fa_date(value: date | datetime | None, with_year: bool = True) -> str:
    """Render a date as a Persian (Jalali) label, e.g. ۱۳ آبان ۱۴۰۵."""
    if not value:
        return ""
    if isinstance(value, datetime) and timezone.is_aware(value):
        value = timezone.localtime(value)
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    day = to_persian_digits(jd)
    month = JALALI_MONTHS[jm - 1]
    return f"{day} {month} {to_persian_digits(jy)}" if with_year else f"{day} {month}"


def fa_date_short(value: date | datetime | None) -> str:
    return fa_date(value, with_year=False)


def jalali_year(value: date | datetime | None) -> str:
    if not value:
        return ""
    if isinstance(value, datetime) and timezone.is_aware(value):
        value = timezone.localtime(value)
    return to_persian_digits(gregorian_to_jalali(value.year, value.month, value.day)[0])


def client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or "0.0.0.0"


def hash_ip(request) -> str:
    from django.conf import settings

    raw = f"{client_ip(request)}|{settings.SECRET_KEY}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:64]


def visitor_key(request) -> str:
    """A privacy-preserving key used for like/follow/stat deduplication."""
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    if not request.session.session_key:
        try:
            request.session.create()
        except Exception:  # pragma: no cover - sessions misconfigured
            pass
    if request.session.session_key:
        return f"session:{request.session.session_key}"
    return f"ip:{hash_ip(request)}"


def truncate(text: str | None, length: int = 160) -> str:
    text = (text or "").strip()
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "…"


def safe_next_url(value: str | None, fallback: str = "/") -> str:
    """Only allow same-site relative redirects."""
    if not value:
        return fallback
    value = value.strip()
    if value.startswith("/") and not value.startswith("//"):
        return value
    return fallback
