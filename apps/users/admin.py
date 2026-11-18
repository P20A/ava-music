from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "display_name", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active", "is_superuser")
    list_editable = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    readonly_fields = ("date_joined", "last_login", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "email")}),
        ("مجوزها", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("تاریخ‌های مهم", {"fields": ("last_login", "date_joined")}),
        ("اطلاعات اضافه", {
            "fields": ("role", "avatar", "bio", "website", "instagram", "telegram", "newsletter_opt_in")
        }),
        ("زمان", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("اطلاعات اضافه", {
            "fields": ("email", "role", "first_name", "last_name")
        }),
    )