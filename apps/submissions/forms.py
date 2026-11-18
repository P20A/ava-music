from __future__ import annotations

from django import forms

from apps.categories.models import Category
from apps.submissions.models import MusicSubmission


class MusicSubmissionForm(forms.ModelForm):
    class Meta:
        model = MusicSubmission
        fields = [
            "artist_name",
            "featured_artists",
            "title",
            "genre",
            "cover_image",
            "audio_320",
            "audio_128",
            "demo_url",
            "lyrics",
            "description",
            "contact_name",
            "contact_email",
            "contact_phone",
            "rights_holder",
            "license_status",
            "license_reference",
            "permission_document",
            "is_original",
            "terms_accepted",
        ]
        widgets = {
            "artist_name": forms.TextInput(attrs={"class": "input", "placeholder": "نام هنری شما", "required": True}),
            "featured_artists": forms.TextInput(attrs={"class": "input", "placeholder": "هنرمندان همراه (اختیاری)"}),
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "نام آهنگ", "required": True}),
            "genre": forms.Select(attrs={"class": "field-select", "style": "width:100%;max-width:none"}),
            "cover_image": forms.ClearableFileInput(attrs={"class": "file-input", "accept": "image/*"}),
            "audio_320": forms.ClearableFileInput(attrs={"class": "file-input", "accept": "audio/*"}),
            "audio_128": forms.ClearableFileInput(attrs={"class": "file-input", "accept": "audio/*"}),
            "demo_url": forms.URLInput(attrs={"class": "input", "placeholder": "https://...", "dir": "ltr"}),
            "lyrics": forms.Textarea(attrs={"class": "textarea", "rows": 4, "placeholder": "متن ترانه"}),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 3, "placeholder": "درباره اثر"}),
            "contact_name": forms.TextInput(attrs={"class": "input", "placeholder": "نام تماس", "required": True}),
            "contact_email": forms.EmailInput(attrs={"class": "input", "placeholder": "you@example.com", "required": True}),
            "contact_phone": forms.TextInput(attrs={"class": "input", "placeholder": "۰۹۱۲..."}),
            "rights_holder": forms.TextInput(attrs={"class": "input", "placeholder": "نام صاحب حقوق", "required": True}),
            "license_status": forms.Select(attrs={"class": "field-select", "style": "width:100%;max-width:none"}),
            "license_reference": forms.TextInput(attrs={"class": "input", "placeholder": "شماره یا مرجع مجوز"}),
            "permission_document": forms.ClearableFileInput(attrs={"class": "file-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["genre"].queryset = Category.objects.filter(is_active=True)
        self.fields["cover_image"].required = False
        self.fields["audio_320"].required = False
        self.fields["audio_128"].required = False

    def clean(self):
        cleaned = super().clean()
        if not (cleaned.get("audio_320") or cleaned.get("audio_128") or cleaned.get("demo_url")):
            self.add_error("audio_320", "حداقل یک فایل صوتی یا لینک دمو وارد کنید.")
        if not cleaned.get("is_original"):
            self.add_error("is_original", "تأیید اصالت اثر الزامی است.")
        if not cleaned.get("terms_accepted"):
            self.add_error("terms_accepted", "پذیرش قوانین انتشار الزامی است.")
        return cleaned
