from django.urls import path

from apps.submissions import views

app_name = "submissions"

urlpatterns = [
    path("", views.SubmissionCreateView.as_view(), name="create"),
    path("success/", views.SubmissionSuccessView.as_view(), name="success"),
    path("status/<uuid:token>/", views.SubmissionStatusView.as_view(), name="status"),
]