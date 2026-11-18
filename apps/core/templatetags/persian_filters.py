from django import template
from django.utils.safestring import mark_safe
import jdatetime

register = template.Library()


@register.filter
def fa_number(value):
    """Convert English digits to Persian/Arabic digits."""
    if value is None:
        return ""
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    translation_table = str.maketrans(english_digits, persian_digits)
    return str(value).translate(translation_table)


@register.filter
def fa_date_short(value):
    """Convert Gregorian date to short Persian (Jalali) date string."""
    if not value:
        return ""
    try:
        if hasattr(value, 'year'):
            jdate = jdatetime.date.fromgregorian(date=value)
        else:
            jdate = jdatetime.date.fromgregorian(date=value.date() if hasattr(value, 'date') else value)
        return fa_number(f"{jdate.year}/{jdate.month:02d}/{jdate.day:02d}")
    except Exception:
        return ""


@register.filter
def fa_date(value):
    """Convert Gregorian date to long Persian (Jalali) date string with month name."""
    if not value:
        return ""
    try:
        if hasattr(value, 'year'):
            jdate = jdatetime.date.fromgregorian(date=value)
        else:
            jdate = jdatetime.date.fromgregorian(date=value.date() if hasattr(value, 'date') else value)
        persian_months = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        month_name = persian_months[jdate.month - 1] if 1 <= jdate.month <= 12 else str(jdate.month)
        return fa_number(f"{jdate.day} {month_name} {jdate.year}")
    except Exception:
        return ""


@register.filter
def fa_duration(value):
    """Convert seconds to mm:ss format with Persian digits."""
    if value is None:
        return ""
    try:
        total_seconds = int(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return fa_number(f"{minutes}:{seconds:02d}")
    except Exception:
        return ""


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary using variable key."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def categories(value):
    """Return categories queryset for archive template."""
    if hasattr(value, 'all'):
        return value.all()
    return value


@register.simple_tag
def static_url(path):
    """Generate static URL."""
    from django.templatetags.static import static
    return static(path)