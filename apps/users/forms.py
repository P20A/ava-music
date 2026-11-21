from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from apps.core.models import SiteSettings
from apps.core.validators import validate_image_file
from apps.users.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="ایمیل",
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "you@example.com"}),
    )
    first_name = forms.CharField(
        label="نام",
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "نام"}),
    )
    last_name = forms.CharField(
        label="نام خانوادگی",
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "نام خانوادگی"}),
    )
    terms = forms.BooleanField(
        label="قوانین انتشار و حریم خصوصی را می‌پذیرم.",
        error_messages={"required": "پذیرش قوانین الزامی است."},
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "input", "placeholder": "نام کاربری", "dir": "ltr"}),
        }
        labels = {"username": "نام کاربری"}

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
            raise forms.ValidationError("این نام کاربری قبلاً ثبت شده است.")
        return username

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.update({"class": "input", "dir": "ltr"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return email

    def clean(self):
        cleaned = super().clean()
        if not SiteSettings.load().registration_enabled:
            raise forms.ValidationError("ثبت‌نام در حال حاضر غیرفعال است.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="نام کاربری",
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "نام کاربری یا ایمیل", "dir": "ltr"}),
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "رمز عبور", "dir": "ltr"}),
    )

    def clean(self):
        username = self.cleaned_data.get("username")
        if username:
            try:
                user = User.objects.get(email__iexact=username.strip())
                self.cleaned_data["username"] = user.username
            except User.DoesNotExist:
                pass
        return super().clean()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "avatar", "bio", "website", "instagram", "telegram", "newsletter_opt_in"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "input", "dir": "ltr"}),
            "first_name": forms.TextInput(attrs={"class": "input"}),
            "last_name": forms.TextInput(attrs={"class": "input"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
            "avatar": forms.ClearableFileInput(attrs={"class": "input"}),
            "bio": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "website": forms.URLInput(attrs={"class": "input", "dir": "ltr"}),
            "instagram": forms.TextInput(attrs={"class": "input", "dir": "ltr"}),
            "telegram": forms.TextInput(attrs={"class": "input", "dir": "ltr"}),
            "newsletter_opt_in": forms.CheckboxInput(),
        }

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("این نام کاربری برای کاربر دیگری ثبت شده است.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("این ایمیل برای کاربر دیگری ثبت شده است.")
        return email


class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["avatar"]

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            raise forms.ValidationError("لطفاً یک تصویر انتخاب کنید.")
        validate_image_file(avatar)
        return avatar
