"""Models for offer app."""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Offer(models.Model):
    """
    Offer model representing a service or product offered by a business user.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='offers',
        help_text="Business user who created this offer"
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Title of the offer"
    )
    
    image = models.ImageField(
        upload_to='offer_images/',
        blank=True,
        null=True,
        help_text="Offer image"
    )
    
    description = models.TextField(
        help_text="Detailed description of the offer"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when offer was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when offer was last updated"
    )
    
    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.user.username}"
    
    @property
    def min_price(self):
        """Get minimum price from offer details."""
        details = self.details.all()
        if details.exists():
            return min(detail.price for detail in details)
        return 0
    
    @property
    def min_delivery_time(self):
        """Get minimum delivery time from offer details."""
        details = self.details.all()
        if details.exists():
            return min(detail.delivery_time_in_days for detail in details)
        return 0


class OfferDetail(models.Model):
    """
    OfferDetail model representing different tiers/options for an offer.
    Each offer can have multiple details (e.g., Basic, Standard, Premium).
    """
    
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='details',
        help_text="The offer this detail belongs to"
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Title of this detail tier (e.g., 'Basic Package')"
    )
    
    revisions = models.IntegerField(
        default=0,
        help_text="Number of revisions included"
    )
    
    delivery_time_in_days = models.IntegerField(
        help_text="Delivery time in days"
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price for this detail tier"
    )
    
    features = models.TextField(
        help_text="Features included in this tier"
    )
    
    offer_type = models.CharField(
        max_length=50,
        help_text="Type of offer (e.g., 'basic', 'standard', 'premium')"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when detail was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when detail was last updated"
    )
    
    class Meta:
        verbose_name = 'Offer Detail'
        verbose_name_plural = 'Offer Details'
        ordering = ['price']
    
    def __str__(self):
        return f"{self.offer.title} - {self.title}"
    


