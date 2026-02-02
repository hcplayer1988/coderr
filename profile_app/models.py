"""Profile model for user profiles."""
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Profile(models.Model):
    """
    Profile model for storing additional user information.
    Automatically created when a user is created.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True
    )
    
    first_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="User's first name"
    )
    
    last_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="User's last name"
    )
    
    file = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        help_text="Profile picture"
    )
    
    location = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="User's location"
    )
    
    tel = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Phone number"
    )
    
    description = models.TextField(
        blank=True,
        default='',
        help_text="User description or bio"
    )
    
    working_hours = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Working hours (e.g., '9-17')"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Profile creation timestamp"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    
    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Profile of {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a profile when a user is created.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save profile when user is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
        
        
