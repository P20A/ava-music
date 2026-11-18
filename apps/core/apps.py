from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "تنظیمات و محتوای سایت"

    def ready(self):
        # Import signals for slug-change redirects and cache invalidation
        try:
            from apps.seo import signals  # noqa: F401
        except ImportError:
            pass