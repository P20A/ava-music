from __future__ import annotations

from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.core.forms import SubmissionForm
from apps.core.models import SiteSettings
from apps.core.utils import hash_ip
from apps.submissions.models import MusicSubmission


class SubmissionCreateView(FormView):
    template_name = "submissions/submission_form.html"
    form_class = SubmissionForm
    success_url = "/submissions/success/"

    def dispatch(self, request, *args, **kwargs):
        settings_obj = SiteSettings.load()
        if not settings_obj.submissions_enabled:
            messages.error(request, "ارسال اثر در حال حاضر غیرفعال است.")
            return HttpResponseRedirect("/")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        key = f"submission:{hash_ip(self.request)}"
        attempts = cache.get(key, 0)
        if attempts >= 3:
            messages.error(self.request, "شما در این ساعت بیش از حد مجاز اثر ارسال کرده‌اید.")
            return self.form_invalid(form)

        submission = form.save(commit=False)
        submission.ip_hash = hash_ip(self.request)
        if self.request.user.is_authenticated:
            submission.submitter = self.request.user
        submission.save()

        cache.set(key, attempts + 1, 3600)

        settings_obj = SiteSettings.load()
        if settings_obj.contact_email:
            try:
                send_mail(
                    subject=f"[{settings_obj.site_name}] اثر جدید ارسال شده: {submission.title}",
                    message=(
                        f"هنرمند: {submission.artist_name}\n"
                        f"اثر: {submission.title}\n"
                        f"ارسال‌کننده: {submission.contact_name} <{submission.contact_email}>\n"
                        f"لینک بررسی: {self.request.build_absolute_uri(submission.get_admin_url())}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings_obj.contact_email],
                    fail_silently=True,
                )
            except Exception:
                pass

        messages.success(self.request, "اثر شما با موفقیت ارسال شد. پس از بررسی منتشر خواهد شد.")
        self.request.session["last_submission_token"] = str(submission.token)
        return super().form_valid(form)


class SubmissionSuccessView(TemplateView):
    template_name = "submissions/submission_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = self.request.session.get("last_submission_token")
        if token:
            context["status_url"] = reverse("submissions:status", kwargs={"token": token})
        return context


class SubmissionStatusView(TemplateView):
    template_name = "submissions/submission_status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get("token")
        submission = get_object_or_404(MusicSubmission, token=token)
        context["submission"] = submission
        return context