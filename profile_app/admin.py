"""Admin configuration for profile app."""
from django.contrib import admin

from profile_app.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin configuration for Profile model."""

    list_display = [
        'user',
        'get_username',
        'get_type',
        'first_name',
        'last_name',
        'location',
        'tel',
        'created_at'
    ]

    list_filter = ['user__type', 'created_at']

    search_fields = [
        'user__username',
        'user__email',
        'first_name',
        'last_name',
        'location'
    ]

    readonly_fields = ['user', 'created_at', 'updated_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'file', 'location', 'tel')
        }),
        ('Professional Information', {
            'fields': ('description', 'working_hours')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_username(self, obj):
        """Display username."""
        return obj.user.username

    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'

    def get_type(self, obj):
        """Display user type."""
        return obj.user.type

    get_type.short_description = 'Type'
    get_type.admin_order_field = 'user__type'
    
