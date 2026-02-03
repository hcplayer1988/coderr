"""Admin configuration for offer app."""
from django.contrib import admin
from offer_app.models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Inline admin for offer details."""
    model = OfferDetail
    extra = 1
    fields = ['title', 'price', 'delivery_time_in_days', 'revisions', 'offer_type']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin configuration for Offer model."""
    
    list_display = [
        'id',
        'title',
        'user',
        'get_min_price',
        'get_min_delivery_time',
        'created_at',
        'updated_at'
    ]
    
    list_filter = ['created_at', 'updated_at', 'user']
    
    search_fields = ['title', 'description', 'user__username']
    
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [OfferDetailInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'image', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_min_price(self, obj):
        """Display minimum price."""
        return obj.min_price
    get_min_price.short_description = 'Min Price'
    
    def get_min_delivery_time(self, obj):
        """Display minimum delivery time."""
        return obj.min_delivery_time
    get_min_delivery_time.short_description = 'Min Delivery Time'


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin configuration for OfferDetail model."""
    
    list_display = [
        'id',
        'offer',
        'title',
        'price',
        'delivery_time_in_days',
        'revisions',
        'offer_type',
        'created_at'
    ]
    
    list_filter = ['offer_type', 'created_at', 'offer']
    
    search_fields = ['title', 'offer__title', 'features']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Offer', {
            'fields': ('offer',)
        }),
        ('Detail Information', {
            'fields': ('title', 'offer_type', 'price', 'delivery_time_in_days', 'revisions')
        }),
        ('Features', {
            'fields': ('features',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


