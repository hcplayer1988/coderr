"""Custom User Model for Coderr Application."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom User Model that extends Django's AbstractUser.
    Adds user type field to distinguish between customer and business users.
    """
    
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('business', 'Business'),
    ]
    
    type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='customer',
        help_text="User type: customer or business"
    )
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.type})"
