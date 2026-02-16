"""Admin configuration for authentication app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model."""

    list_display = [
        'username',
        'email',
        'type',
        'is_staff',
        'is_active',
        'date_joined'
    ]
    list_filter = ['type', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email']

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('type',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('type',)}),
    )
    
