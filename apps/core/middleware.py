from __future__ import annotations

from django.db.models import F
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils import timezone

from apps.core.models import Redirect, SiteSettings


class RedirectMiddleware:
    """Apply admin-managed 301 redirects for changed slugs/URLs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in {"GET", "HEAD"}:
            path = request.path
            if not path.startswith(("/admin/", "/static/", "/media/", "/health/")):
                try:
                    redirect_obj = Redirect.objects.filter(old_path=path).only(
                        "id", "new_path", "is_permanent"
                    ).first()
                except Exception:
                    redirect_obj = None
                if redirect_obj:
                    Redirect.objects.filter(pk=redirect_obj.pk).update(
                        hits=F("hits") + 1, last_hit_at=timezone.now()
                    )
                    if redirect_obj.is_permanent:
                        return HttpResponsePermanentRedirect(redirect_obj.new_path)
                    return HttpResponseRedirect(redirect_obj.new_path)
        return self.get_response(request)


class MaintenanceModeMiddleware:
    """Display a friendly 503 page while still allowing staff to work."""

    ALLOWED_PREFIXES = ("/admin/", "/static/", "/media/", "/health/", "/accounts/login/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            enabled = SiteSettings.load().maintenance_mode
        except Exception:
            enabled = False
        if enabled:
            user = getattr(request, "user", None)
            is_staff = bool(user and user.is_authenticated and user.is_staff)
            if not is_staff and not request.path.startswith(self.ALLOWED_PREFIXES):
                from django.shortcuts import render

                response = render(request, "503.html", status=503)
                response["Retry-After"] = "3600"
                return response
        return self.get_response(request)
