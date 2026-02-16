"""Models for order app."""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Order(models.Model):
    """
    Model representing an order/booking.

    Links a customer with a business user for a specific service.
    """

    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    OFFER_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]

    customer_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders_as_customer',
        help_text='Customer who placed the order'
    )
    business_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders_as_business',
        help_text='Business user fulfilling the order'
    )

    title = models.CharField(max_length=255)
    revisions = models.IntegerField(default=0)
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(
        default=list,
        help_text='List of features included'
    )
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order #{self.id}: {self.title} - {self.status}"
    
