"""Admin configuration for order app."""
from django.contrib import admin
from order_app.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model."""

    list_display = [
        'id',
        'title',
        'customer_user',
        'business_user',
        'status',
        'price',
        'offer_type',
        'created_at'
    ]

    list_filter = [
        'status',
        'offer_type',
        'created_at'
    ]

    search_fields = [
        'title',
        'customer_user__username',
        'business_user__username'
    ]

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Order Information', {
            'fields': ('title', 'offer_type', 'status')
        }),
        ('Users', {
            'fields': ('customer_user', 'business_user')
        }),
        ('Details', {
            'fields': (
                'revisions',
                'delivery_time_in_days',
                'price',
                'features'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

