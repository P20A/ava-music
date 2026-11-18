from __future__ import annotations

from django.db.models import F
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.advertisements.models import Advertisement


@require_GET
def ad_click(request, pk):
    ad = get_object_or_404(Advertisement, pk=pk)
    if not ad.is_live:
        return HttpResponseRedirect("/")

    Advertisement.objects.filter(pk=ad.pk).update(click_count=F("click_count") + 1)
    return HttpResponseRedirect(ad.destination_url)


@require_POST
def ad_impression(request):
    placement = request.POST.get("placement")
    if not placement:
        return JsonResponse({"error": "placement required"}, status=400)

    ads = Advertisement.objects.live().filter(placement=placement).order_by("-priority")[:5]

    for ad in ads:
        Advertisement.objects.filter(pk=ad.pk).update(impression_count=F("impression_count") + 1)

    return JsonResponse({"count": len(ads)})