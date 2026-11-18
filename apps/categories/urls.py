from django.urls import path

from apps.categories import views

app_name = "categories"

urlpatterns = [
    path("", views.CategoryListView.as_view(), name="list"),
    path("<uslug:slug>/", views.CategoryDetailView.as_view(), name="detail"),
]