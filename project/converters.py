"""Custom path converters."""


class UnicodeSlugConverter:
    """Slug converter that accepts Persian/Unicode slugs (Django's default is ASCII-only)."""

    regex = "[-\\w]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
