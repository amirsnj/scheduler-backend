from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    search_fields = ['username']
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "usable_password", "email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )