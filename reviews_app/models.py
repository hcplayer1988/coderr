"""Models for reviews app."""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Review(models.Model):
    """
    Model for user reviews.

    Business users can receive reviews from other users.
    A user can only review a business user once.
    """

    business_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_reviews',
        help_text='The business user being reviewed'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_reviews',
        help_text='The user who wrote the review'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5'
    )
    description = models.TextField(
        help_text='Review description/comment'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = [['business_user', 'reviewer']]

    def __str__(self):
        return (
            f'Review by {self.reviewer.username} '
            f'for {self.business_user.username} - {self.rating}/5'
        )


