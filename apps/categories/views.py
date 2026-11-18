from __future__ import annotations

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView

from apps.analytics.models import record_view
from apps.categories.models import Category
from apps.music.models import Song


class CategoryListView(ListView):
    model = Category
    template_name = "categories/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        kind = self.request.GET.get("kind")
        qs = Category.objects.filter(is_active=True).annotate(
            song_total=Count("songs", filter=Q(songs__is_published=True))
        )

        if kind:
            qs = qs.filter(kind=kind)

        return qs.order_by("order", "name")


class CategoryDetailView(DetailView):
    model = Category
    template_name = "categories/category_detail.html"
    context_object_name = "category"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Category.objects.filter(is_active=True).prefetch_related("children")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_view(request, self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        songs = category.songs.filter(is_published=True).select_related(
            "primary_artist"
        ).prefetch_related("categories", "artists")

        from django.core.paginator import Paginator

        sort = self.request.GET.get("sort", "newest")
        if sort == "views":
            songs = songs.order_by("-view_count")
        elif sort == "popular":
            songs = songs.order_by("-play_count")
        elif sort == "title":
            songs = songs.order_by("title")
        else:
            songs = songs.order_by("-published_at", "-created_at")

        paginator = Paginator(songs, 12)
        page = self.request.GET.get("page")
        page_obj = paginator.get_page(page)

        children = category.children.filter(is_active=True).annotate(
            song_total=Count("songs", filter=Q(songs__is_published=True))
        )

        context.update(
            {
                "page_obj": page_obj,
                "songs": page_obj.object_list,
                "current_sort": sort,
                "children": children,
            }
        )
        return context