from __future__ import annotations

from django import forms

from apps.core.models import ContactMessage, NewsletterSubscriber
from apps.submissions.models import MusicSubmission
from apps.categories.models import Category


class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="")

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "نام شما"}),
            "email": forms.EmailInput(attrs={"class": "input", "placeholder": "you@example.com"}),
            "phone": forms.TextInput(attrs={"class": "input", "placeholder": "۰۹۱۲..."}),
            "subject": forms.Select(attrs={"class": "field-select", "style": "width:100%;max-width:none"}),
            "message": forms.Textarea(attrs={"class": "textarea", "rows": 5, "placeholder": "پیام خود را بنویسید..."}),
        }

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("ارسال پیام ممکن نشد.")
        return value


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email", "name"]
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "input", "placeholder": "ایمیل شما", "aria-label": "ایمیل خبرنامه"}
            ),
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "نام (اختیاری)"}),
        }

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = MusicSubmission
        fields = [
            "artist_name", "featured_artists", "title", "genre",
            "cover_image", "audio_320", "audio_128", "lyrics", "description",
            "contact_name", "contact_email", "contact_phone", "demo_url",
            "rights_holder", "license_status", "license_reference", "permission_document",
            "is_original", "terms_accepted",
        ]
        widgets = {
            "artist_name": forms.TextInput(attrs={"class": "input", "placeholder": "مثال: آرمان راد"}),
            "featured_artists": forms.TextInput(attrs={"class": "input", "placeholder": "مثال: رها، دنیز"}),
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "مثال: شب بارونی"}),
            "genre": forms.Select(attrs={"class": "field-select", "style": "width:100%;max-width:none"}),
            "cover_image": forms.FileInput(attrs={"class": "file-input", "accept": "image/*"}),
            "audio_320": forms.FileInput(attrs={"class": "file-input", "accept": "audio/mpeg,audio/mp3,audio/mp4,audio/x-m4a,audio/aac,audio/wav,audio/ogg,audio/flac"}),
            "audio_128": forms.FileInput(attrs={"class": "file-input", "accept": "audio/mpeg,audio/mp3,audio/mp4,audio/x-m4a,audio/aac,audio/wav,audio/ogg,audio/flac"}),
            "lyrics": forms.Textarea(attrs={"class": "textarea", "rows": 6, "placeholder": "متن ترانه را اینجا بنویسید..."}),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 4, "placeholder": "درباره اثر، تنظیم، میکس، مسترینگ و..."}),
            "contact_name": forms.TextInput(attrs={"class": "input", "placeholder": "نام و نام خانوادگی"}),
            "contact_email": forms.EmailInput(attrs={"class": "input", "placeholder": "email@example.com"}),
            "contact_phone": forms.TextInput(attrs={"class": "input", "placeholder": "۰۹xxxxxxxxx"}),
            "demo_url": forms.URLInput(attrs={"class": "input", "placeholder": "https://..."}),
            "rights_holder": forms.TextInput(attrs={"class": "input", "placeholder": "نام صاحب اثر/حقوق"}),
            "license_status": forms.Select(attrs={"class": "field-select", "style": "width:100%;max-width:none"}),
            "license_reference": forms.TextInput(attrs={"class": "input", "placeholder": "شماره قرارداد و..."}),
            "permission_document": forms.FileInput(attrs={"class": "file-input", "accept": ".pdf,.jpg,.jpeg,.png,.zip"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["genre"].queryset = Category.objects.filter(is_active=True, kind=Category.Kind.GENRE)
        self.fields["genre"].empty_label = "سبک را انتخاب کنید"
        self.fields["license_status"].choices = MusicSubmission._meta.get_field("license_status").choices
        self.fields["is_original"].required = True
        self.fields["terms_accepted"].required = True

    def clean_is_original(self):
        value = self.cleaned_data.get("is_original")
        if not value:
            raise forms.ValidationError("تأیید اصالت اثر الزامی است.")
        return value

    def clean_terms_accepted(self):
        value = self.cleaned_data.get("terms_accepted")
        if not value:
            raise forms.ValidationError("پذیرش قوانین انتشار الزامی است.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        audio_320 = cleaned_data.get("audio_320")
        audio_128 = cleaned_data.get("audio_128")
        demo_url = cleaned_data.get("demo_url")
        
        if not (audio_320 or audio_128 or demo_url):
            raise forms.ValidationError("حداقل یک فایل صوتی یا لینک دمو وارد کنید.")
        
        return cleaned_data