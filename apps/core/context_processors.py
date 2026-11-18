from __future__ import annotations

from django.db.models import Count

from apps.core.models import NavigationLink, SiteSettings


def site_context(request):
    settings_obj = SiteSettings.load()
    links = list(NavigationLink.objects.filter(is_active=True).order_by("location", "order", "id"))
    header_links = [link for link in links if link.location == NavigationLink.Location.HEADER]
    footer_links = [link for link in links if link.location == NavigationLink.Location.FOOTER]
    topbar_links = [link for link in links if link.location == NavigationLink.Location.TOPBAR]
    return {
        "site": settings_obj,
        "header_links": header_links,
        "footer_links": footer_links,
        "topbar_links": topbar_links,
        "current_path": request.path,
        "canonical_url": request.build_absolute_uri(request.path),
        "site_name": settings_obj.site_name,
        "site_tagline": settings_obj.site_tagline,
    }
