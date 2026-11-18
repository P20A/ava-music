from django.urls import path

from apps.advertisements import views

app_name = "advertisements"

urlpatterns = [
    path("click/<int:pk>/", views.ad_click, name="click"),
    path("impression/", views.ad_impression, name="impression"),
]