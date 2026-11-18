from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView as AuthPasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from apps.core.models import SiteSettings
from apps.users.forms import LoginForm, ProfileForm, RegisterForm
from apps.users.models import User


class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:profile")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:profile")
        if not SiteSettings.load().registration_enabled:
            messages.warning(request, "ثبت‌نام در حال حاضر غیرفعال است.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "حساب شما ساخته شد. خوش آمدید!")
        return response


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "با موفقیت وارد شدید.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = SiteSettings.load()
        return context


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("home")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["profile"] = user
        context["submissions"] = user.submissions.all()[:10] if hasattr(user, "submissions") else []
        context["likes"] = user.song_likes.select_related("song", "song__primary_artist")[:12]
        context["followed_artists"] = user.artist_follows.select_related("artist")[:12]
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "پروفایل شما به‌روزرسانی شد.")
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, AuthPasswordChangeView):
    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, "رمز عبور شما تغییر کرد.")
        return response


class FavoritesView(LoginRequiredMixin, TemplateView):
    template_name = "users/favorites.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["likes"] = user.song_likes.select_related("song", "song__primary_artist").all()
        return context


class HistoryView(LoginRequiredMixin, TemplateView):
    template_name = "users/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from apps.analytics.models import PlayEvent, SongView

        context["plays"] = PlayEvent.objects.filter(user=user).select_related("song", "song__primary_artist")[:50]
        context["views"] = SongView.objects.filter(user=user).select_related("song", "song__primary_artist")[:50]
        return context


class FollowedArtistsView(LoginRequiredMixin, TemplateView):
    template_name = "users/followed_artists.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["followed"] = user.artist_follows.select_related("artist").all()
        return context