"""Admin configuration for reviews app."""
from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model."""

    list_display = [
        'id',
        'business_user',
        'reviewer',
        'rating',
        'created_at',
        'updated_at'
    ]

    list_filter = ['rating', 'created_at', 'updated_at']

    search_fields = [
        'business_user__username',
        'reviewer__username',
        'description'
    ]

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Review Information', {
            'fields': ('business_user', 'reviewer', 'rating', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
